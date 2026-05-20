import streamlit as st
import random
import time
import threading
from collections import Counter, deque
import utils

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from model.keypoint_classifier import recognition
from model.dynamic_classifier.dynamic_classifier import model_exists as dynamic_model_exists
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase, WebRtcMode
import av
import cv2
import numpy as np
import copy
import itertools
import mediapipe as mp

DYNAMIC_LETTERS  = frozenset('ҐДЄЗЇЙКЦЩЬ')
SEQUENCE_LENGTH  = 16
RECORD_INTERVAL  = 0.067   # ~15 fps — matches training cadence
CLASSIFY_EVERY   = 2        # run classifier after every N new frames
CONFIRM_COUNT    = 5        # majority of recent results needed to accept a gesture


def _calc_landmark_list(image, landmarks):
    h, w = image.shape[:2]
    return [[min(int(lm.x * w), w - 1), min(int(lm.y * h), h - 1)]
            for lm in landmarks.landmark]

def _pre_process_landmark(landmark_list):
    tmp = copy.deepcopy(landmark_list)
    bx, by = tmp[0]
    for p in tmp:
        p[0] -= bx; p[1] -= by
    flat = list(itertools.chain.from_iterable(tmp))
    mx = max(map(abs, flat)) or 1
    return [v / mx for v in flat]


class DynamicGestureProcessor(VideoProcessorBase):
    """Sliding-window classifier with majority voting for robust gesture recognition."""

    def __init__(self):
        import csv as _csv
        from model.dynamic_classifier.dynamic_classifier import DynamicGestureClassifier
        self._lock       = threading.Lock()
        self._window     = deque(maxlen=SEQUENCE_LENGTH)  # rolling 16-frame window
        self._history    = deque(maxlen=10)                # recent classification results
        self._new_frames = 0                               # frames added since last classify
        self._last_t     = 0.0
        self._result     = None   # confirmed letter
        self._best_guess = None   # last single-classification guess (for overlay)
        self._classifier = DynamicGestureClassifier()
        with open('model/dynamic_classifier/dynamic_classifier_label.csv',
                  encoding='utf-8-sig') as f:
            self._labels = [row[0] for row in _csv.reader(f) if row]
        self._hands = mp.solutions.hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5,
        )

    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        img = cv2.flip(img, 1)

        now = time.time()
        if now - self._last_t >= RECORD_INTERVAL:
            self._last_t = now
            rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            results = self._hands.process(rgb)
            if results.multi_hand_landmarks:
                lm_list = _calc_landmark_list(img, results.multi_hand_landmarks[0])
                processed = _pre_process_landmark(lm_list)
                with self._lock:
                    if self._result is None:
                        self._window.append(processed)
                        self._new_frames += 1
                        if (len(self._window) == SEQUENCE_LENGTH
                                and self._new_frames >= CLASSIFY_EVERY):
                            self._new_frames = 0
                            self._try_classify()
                mp.solutions.drawing_utils.draw_landmarks(
                    img, results.multi_hand_landmarks[0],
                    mp.solutions.hands.HAND_CONNECTIONS)

        with self._lock:
            result  = self._result
            buf_len = len(self._window)
            top, top_cnt = (Counter(self._history).most_common(1)[0]
                            if self._history else (None, 0))

        if result:
            cv2.putText(img, f"OK: {result} -- natisknit' knopku",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 220, 0), 2)
        elif top:
            cv2.putText(img, f"{top}  {top_cnt}/{CONFIRM_COUNT}",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (80, 200, 80), 2)
        else:
            cv2.putText(img, f"Zbyrayu: {buf_len}/{SEQUENCE_LENGTH}",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (160, 160, 160), 2)
        return av.VideoFrame.from_ndarray(img, format="bgr24")

    def _try_classify(self):
        """Called while holding self._lock."""
        idx = self._classifier(list(self._window))
        if 0 <= idx < len(self._labels):
            letter = self._labels[idx]
            self._best_guess = letter
            self._history.append(letter)
            top, top_cnt = Counter(self._history).most_common(1)[0]
            if top_cnt >= CONFIRM_COUNT:
                self._result = top

    def get_result(self):
        with self._lock:
            return self._result, len(self._window)

    def reset(self):
        with self._lock:
            self._window.clear()
            self._history.clear()
            self._new_frames = 0
            self._result     = None
            self._best_guess = None


def change_level(level):
    st.session_state.clear()
    st.session_state["level"] = level
    if level != "menu":
        reset_game()


def reset_game():
    levels = {
        "easy": (["ЛАМПА", "МЕТА", "СИЛА", "ЛИСТ", "ТЕПЛО", "ПАН", "СЕЛО", "МАТИ", "ПОЛЕ", "САЛО",
                  "ЛОТО", "ТОН", "СТАН", "СМОЛА", "ЛИПА", "СИН", "НАСИП", "ЛОТОС", "НОГА",
                  # words with dynamic letters (Д, З, К, Й, Ь):
                  "КІТ", "ДІМ", "ЗИМА", "МАЙ", "ДЕНЬ", "КАЗКА", "КЛАС", "ЗУБИ", "ДАНО", "КІНЬ"],),
        "medium": (["МІСТО", "ІСПИТ", "РОБОТА", "МОТИВ", "НЕБО", "МІСТ", "ВИСОТА", "СУМА", "ПЕРО",
                    "ЧОРНИЛА", "ТІСТО", "СТІЛ", "ЛІТОПИС", "ВІТЕР", "ТУМАН", "ВЕЧІР", "ПОБУТ",
                    "БОЛОТО", "ЛІТР", "СТОВП", "БЕТОН",
                    # words with dynamic letters:
                    "КНИГА", "ЗАДАЧА", "ДОРОГА", "КОЗАК", "ЗАКОН", "КІМНАТА", "ЗБРОЯ", "ДЕРЕВО"],),
        "hard": (["УСПІХ", "ГУМОР", "ШИЯ", "ЮРИСТ", "ЧЕМПІОН", "СИМВОЛ", "ФАХ", "СПАЛАХ",
                  "ІНЖЕНЕР", "ЛЮБОВ", "ПЕЧИВО", "ЛИСТЯ", "ФІЛОЛОГІЯ", "ФОРМА", "ГОРА", "ХВІСТ",
                  "ФАНЕРА", "ШТАНИ", "СТРУМ",
                  # words with dynamic letters:
                  "ЩАСТЯ", "ЗНАННЯ", "ЯКІСТЬ", "КОЗАЦЬКИЙ", "ДЕРЖАВА", "КІЛЬКІСТЬ"],),
    }
    words = levels[st.session_state["level"]][0]
    word = random.choice(words)
    st.session_state["random_word"] = word
    st.session_state["current_index"] = 0
    st.session_state["letter_states"] = ["pending"] * len(word)
    st.session_state["wrong_gesture"] = None
    st.session_state["game_won"] = False
    st.session_state["recognized_letter"] = ""
    st.session_state["dynamic_mode"] = False
    st.session_state["dynamic_buffer"] = []


def render_word(word, letter_states, current_index):
    parts = []
    for i, letter in enumerate(word):
        state = letter_states[i]
        if state == "correct":
            css_class = "word-letter correct"
        elif i == current_index:
            css_class = "word-letter current"
        else:
            css_class = "word-letter pending"
        parts.append(f'<div class="{css_class}">{letter}</div>')
    return f'<div class="word-display">{"".join(parts)}</div>'


def app():
    utils.load_css("style.css")

    if "level" not in st.session_state:
        st.session_state.level = "menu"

    # ── Level selection ───────────────────────────────────────────
    if st.session_state.level == "menu":
        st.markdown('''
        <div class="page-hero">
            <div class="title_header">Гра</div>
            <p>Оберіть рівень складності та починайте</p>
        </div>
        ''', unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)

        level_meta = [
            (col1, "Легкий",   "Прості слова",   "easy_button",   "easy"),
            (col2, "Середній", "Складніші слова",         "medium_button", "medium"),
            (col3, "Складний", "Для досвідчених",                         "hard_button",   "hard"),
        ]

        for col, name, desc, key, level in level_meta:
            with col:
                st.markdown(f'''
                <div class="level-header">
                    <div class="level-name">{name}</div>
                    <div class="level-desc">{desc}</div>
                </div>
                ''', unsafe_allow_html=True)
                st.button("Грати", on_click=change_level, args=(level,), key=key, use_container_width=True)

    # ── Active game ───────────────────────────────────────────────
    else:
        level_titles = {
            "easy":   "Легкий рівень",
            "medium": "Середній рівень",
            "hard":   "Складний рівень",
        }

        level = st.session_state.level
        st.markdown(f'<div class="title_subheader">{level_titles[level]}</div>', unsafe_allow_html=True)

        if "random_word" not in st.session_state or "letter_states" not in st.session_state:
            reset_game()

        word = st.session_state["random_word"]
        letter_states = st.session_state["letter_states"]
        current_index = st.session_state["current_index"]
        game_won = st.session_state.get("game_won", False)
        wrong_gesture = st.session_state.get("wrong_gesture")

        # ── Word display ──────────────────────────────────────────
        st.markdown(render_word(word, letter_states, current_index), unsafe_allow_html=True)
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        if game_won:
            st.markdown(
                '<div class="game-stat" style="text-align:center;margin-top:12px;">'
                '<div class="game-stat-value">Чудово! Ви склали все слово! 🎉</div>'
                '</div>',
                unsafe_allow_html=True,
            )
        else:
            col1, col2 = st.columns(2)

            current_letter = word[current_index] if current_index < len(word) else None
            is_dynamic = current_letter in DYNAMIC_LETTERS if current_letter else False

            with col1:
                if "camera_key" not in st.session_state:
                    st.session_state.camera_key = 0

                if is_dynamic:
                    if not dynamic_model_exists():
                        st.error(
                            "Модель динамічних жестів не знайдено. "
                            "Запустіть `python train_dynamic.py` у папці Dynamic-Gestures-Training."
                        )
                    else:
                        # Live video stream — processor collects 16 frames automatically
                        ctx = webrtc_streamer(
                            key=f"dynamic_{current_letter}",
                            mode=WebRtcMode.SENDRECV,
                            video_processor_factory=DynamicGestureProcessor,
                            media_stream_constraints={"video": True, "audio": False},
                            async_processing=True,
                        )
                        # Result saved by the button survives processor recreation on rerun
                        pending = st.session_state.pop("dynamic_pending", None)
                        if pending is not None:
                            if ctx.video_processor:
                                ctx.video_processor.reset()
                            if pending:
                                st.session_state["recognized_letter"] = pending
                                recognition.process_letter()
                            st.rerun()
                        elif ctx.video_processor:
                            result, frame_count = ctx.video_processor.get_result()
                            if result is not None:
                                ctx.video_processor.reset()
                                if result:
                                    st.session_state["recognized_letter"] = result
                                    recognition.process_letter()
                                st.rerun()
                            else:
                                st.caption("Тримайте жест — дочекайтесь підтвердження на відео, потім натисніть кнопку")
                                if st.button("✅ Підтвердити жест",
                                             key=f"submit_dyn_{current_index}",
                                             use_container_width=True):
                                    # Read result NOW and save before the rerun loses it
                                    r, _ = ctx.video_processor.get_result()
                                    if r is not None:
                                        st.session_state["dynamic_pending"] = r
                                    st.rerun()
                else:
                    img_file = st.camera_input(
                        "Покажіть жест / Show your gesture",
                        key=f"camera_{st.session_state.camera_key}"
                    )
                    if img_file is not None:
                        letter, annotated_image = recognition.process_frame(img_file)
                        if letter:
                            st.session_state["recognized_letter"] = letter
                            recognition.process_letter()
                            st.session_state.camera_key += 1
                            st.rerun()
                        else:
                            st.warning("Руку не виявлено / No hand detected. Спробуйте ще / Try again.")

            with col2:
                if current_index < len(word):
                    st.markdown(f'''
                    <div class="game-stat">
                        <div class="game-stat-label">Покажіть жест для літери</div>
                        <div class="game-stat-value" style="font-size:56px;line-height:1.1;">{current_letter}</div>
                    </div>
                    ''', unsafe_allow_html=True)

                wrong_value = wrong_gesture if wrong_gesture else "&nbsp;"
                wrong_color = "hsl(0,60%,50%)" if wrong_gesture else "transparent"
                st.markdown(f'''
                <div class="game-stat" style="margin-top:12px;">
                    <div class="game-stat-label">Ваш жест (неправильно)</div>
                    <div class="game-stat-value" style="font-size:56px;line-height:1.1;color:{wrong_color};">{wrong_value}</div>
                </div>
                ''', unsafe_allow_html=True)

        st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
        st.button("Назад до меню", on_click=lambda: change_level("menu"), key="back_1button", use_container_width=True)
