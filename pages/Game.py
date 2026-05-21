import streamlit as st
import random
import time
import threading
from collections import Counter
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
RECORD_INTERVAL  = 0.13    # ~7.7 fps — matches training data collection cadence


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
    """Button-triggered fixed-length recorder that mirrors the training data collector.

    The user presses a button, performs the gesture over ~2 seconds while
    SEQUENCE_LENGTH frames are captured at RECORD_INTERVAL spacing, then the
    classifier runs once on the complete burst — exactly how training data was made.
    """

    def __init__(self):
        import csv as _csv
        import os as _os
        from model.dynamic_classifier.dynamic_classifier import DynamicGestureClassifier
        self._lock       = threading.Lock()
        self._recording  = False   # True while collecting a burst
        self._seq        = []      # frames collected in the current burst
        self._last_t     = 0.0
        self._result     = None    # letter after classification
        self._load_error = None
        try:
            self._classifier = DynamicGestureClassifier()
            print("[DynamicGestureProcessor] dynamic classifier loaded OK", flush=True)
        except Exception as e:
            import traceback as _tb
            self._load_error = str(e)
            print(f"[DynamicGestureProcessor] load failed: {e}", flush=True)
            print(_tb.format_exc(), flush=True)
            self._classifier = None
        _label_path = _os.path.join(
            _os.path.dirname(_os.path.abspath(__file__)),
            '..', 'model', 'dynamic_classifier', 'dynamic_classifier_label.csv'
        )
        with open(_label_path, encoding='utf-8-sig') as f:
            self._labels = [row[0] for row in _csv.reader(f) if row]
        self._hands = mp.solutions.hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5,
        )

    # ── called from Streamlit main thread ────────────────────────────
    def start_recording(self):
        with self._lock:
            self._recording = True
            self._seq       = []
            self._last_t    = 0.0

    def get_result(self):
        with self._lock:
            return self._result, len(self._seq)

    def is_recording(self):
        with self._lock:
            return self._recording

    def reset(self):
        with self._lock:
            self._recording = False
            self._seq       = []
            self._last_t    = 0.0
            self._result    = None

    # ── WebRTC worker thread ──────────────────────────────────────────
    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        img = cv2.flip(img, 1)
        now = time.time()

        # Always detect hand for landmark overlay
        rgb     = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = self._hands.process(rgb)
        processed = None
        if results.multi_hand_landmarks:
            lm_list   = _calc_landmark_list(img, results.multi_hand_landmarks[0])
            processed = _pre_process_landmark(lm_list)
            mp.solutions.drawing_utils.draw_landmarks(
                img, results.multi_hand_landmarks[0],
                mp.solutions.hands.HAND_CONNECTIONS)

        # Capture frame into burst buffer at the training interval
        classify_now = False
        with self._lock:
            if self._recording and now - self._last_t >= RECORD_INTERVAL:
                self._last_t = now
                # Zero-fill if hand absent (mirrors data collector behaviour)
                self._seq.append(processed if processed is not None else [0.0] * 42)
                if len(self._seq) >= SEQUENCE_LENGTH:
                    self._recording = False
                    classify_now    = True

        # Classify outside the lock (can be slow)
        if classify_now:
            self._run_classify()

        # Read state for overlay
        with self._lock:
            recording = self._recording
            seq_len   = len(self._seq)
            result    = self._result

        # Overlay
        if result:
            cv2.putText(img, f"OK: {result}",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 220, 0), 2)
        elif recording:
            cv2.putText(img, f"Zapys: {seq_len}/{SEQUENCE_LENGTH}",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (80, 200, 80), 2)
        else:
            cv2.putText(img, "Gotovo — natysnit' 'Zapysaty'",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (160, 160, 160), 1)

        # Model-loaded badge
        badge = "LSTM: OK" if self._classifier else \
                f"LSTM: FAIL [{(self._load_error or '')[:35]}]"
        color = (0, 180, 0) if self._classifier else (0, 0, 220)
        cv2.putText(img, badge, (10, img.shape[0] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1)

        return av.VideoFrame.from_ndarray(img, format="bgr24")

    def _run_classify(self):
        """Classify self._seq. Safe to call outside lock."""
        if self._classifier is None or len(self._seq) < SEQUENCE_LENGTH:
            return
        idx = self._classifier(self._seq[:SEQUENCE_LENGTH])
        with self._lock:
            if 0 <= idx < len(self._labels):
                self._result = self._labels[idx]


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
            # Make both game columns stretch to equal height
            st.markdown("""
            <style>
            div[data-testid="stHorizontalBlock"]:has(div[data-testid="stCustomComponentV1"]) {
                align-items: stretch !important;
            }
            div[data-testid="stHorizontalBlock"]:has(div[data-testid="stCustomComponentV1"])
            > div[data-testid="stColumn"] {
                display: flex !important;
                flex-direction: column !important;
            }
            div[data-testid="stHorizontalBlock"]:has(div[data-testid="stCustomComponentV1"])
            > div[data-testid="stColumn"] > div[data-testid="stVerticalBlock"] {
                flex: 1 !important;
                display: flex !important;
                flex-direction: column !important;
            }
            </style>
            """, unsafe_allow_html=True)
            col1, col2 = st.columns(2)

            current_letter = word[current_index] if current_index < len(word) else None
            is_dynamic = current_letter in DYNAMIC_LETTERS if current_letter else False

            with col1:
                if is_dynamic:
                    ctx = webrtc_streamer(
                        key=f"dynamic_{current_letter}",
                        mode=WebRtcMode.SENDRECV,
                        video_processor_factory=DynamicGestureProcessor,
                        media_stream_constraints={"video": True, "audio": False},
                        async_processing=True,
                    )
                    if ctx.video_processor:
                        if ctx.video_processor._load_error:
                            st.error(f"⚠️ Модель не завантажена: {ctx.video_processor._load_error}")

                        result, seq_len = ctx.video_processor.get_result()
                        recording       = ctx.video_processor.is_recording()

                        if result is not None:
                            # Burst complete and classified — save and advance
                            ctx.video_processor.reset()
                            st.session_state["recognized_letter"] = result
                            recognition.process_letter()
                            st.rerun()
                        elif recording:
                            # Show progress while the burst is being recorded
                            st.caption(f"⏺ Запис: {seq_len}/{SEQUENCE_LENGTH} кадрів — тримайте жест...")
                            if st.button("✅ Підтвердити (готово)",
                                         key=f"confirm_dyn_{current_index}",
                                         use_container_width=True):
                                # Force-finish early if user is confident
                                r, _ = ctx.video_processor.get_result()
                                if r is not None:
                                    ctx.video_processor.reset()
                                    st.session_state["recognized_letter"] = r
                                    recognition.process_letter()
                                    st.rerun()
                        else:
                            if st.button("🔴 Записати жест",
                                         key=f"rec_dyn_{current_index}",
                                         use_container_width=True):
                                ctx.video_processor.start_recording()
                                st.rerun()
                else:
                    import hashlib as _hl
                    img_file = st.camera_input(
                        "Покажіть жест / Show your gesture",
                        key=f"camera_{current_index}",
                    )
                    if img_file is not None:
                        # Skip if this exact photo was already processed
                        photo_hash = _hl.md5(img_file.getvalue()).hexdigest()
                        if photo_hash != st.session_state.get("last_photo_hash"):
                            letter, _ = recognition.process_frame(img_file)
                            if letter:
                                st.session_state["last_photo_hash"] = photo_hash
                                st.session_state["recognized_letter"] = letter
                                recognition.process_letter()
                                st.rerun()
                            else:
                                st.warning("Руку не виявлено / No hand detected. Спробуйте ще / Try again.")

            with col2:
                wrong_value = wrong_gesture if wrong_gesture else "&nbsp;"
                wrong_color = "hsl(0,60%,50%)" if wrong_gesture else "transparent"
                target_html = (
                    f'<div class="game-stat">'
                    f'<div class="game-stat-label">Покажіть жест для літери</div>'
                    f'<div class="game-stat-value" style="font-size:56px;line-height:1.1;">{current_letter or ""}</div>'
                    f'</div>'
                ) if current_index < len(word) else ""
                wrong_html = (
                    f'<div class="game-stat">'
                    f'<div class="game-stat-label">Ваш жест (неправильно)</div>'
                    f'<div class="game-stat-value" style="font-size:56px;line-height:1.1;color:{wrong_color};">{wrong_value}</div>'
                    f'</div>'
                )
                st.markdown(
                    f'<div style="display:flex;flex-direction:column;justify-content:space-between;height:100%;gap:12px;">'
                    f'{target_html}{wrong_html}'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
        st.button("Назад до меню", on_click=lambda: change_level("menu"), key="back_1button", use_container_width=True)
