import streamlit as st
import random
import utils

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from model.keypoint_classifier import recognition
from model.dynamic_classifier.dynamic_classifier import model_exists as dynamic_model_exists

DYNAMIC_LETTERS  = frozenset('ҐДЄЗЇЙКЦЩЬ')
SEQUENCE_FRAMES  = 15


def change_level(level):
    st.session_state.clear()
    st.session_state["level"] = level
    if level != "menu":
        reset_game()


def reset_game():
    levels = {
        "easy": (["ЛАМПА", "МЕТА", "СИЛА", "ЛИСТ", "ТЕПЛО", "ПАН", "СЕЛО", "МАТИ", "ПОЛЕ", "САЛО", "ЛОТО", "ТОН", "СТАН", "СМОЛА", "ЛИПА", "СИН", "НАСИП", "ЛОТОС",
                  "КІТ", "ЗУБ", "ДЕНЬ", "КОТ", "КАЗКА", "ЗИМА", "НОГА", "КИТ", "ДІМ", "ЛЕД"],),
        "medium": (["МІСТО", "ІСПИТ", "РОБОТА", "МОТИВ", "НЕБО", "МІСТ", "ВИСОТА", "СУМА", "ПЕРО", "ЧОРНИЛА", "ТІСТО", "СТІЛ", "ЛІТОПИС", "ВІТЕР", "ТУМАН", "ВЕЧІР", "ПОБУТ", "БОЛОТО", "ЛІТР", "СТОВП", "БЕТОН",
                    "КОЗАК", "ДЕРЕВО", "ЗЕРНО", "КОБРА", "ДВЕРІ", "ЗІРКА", "ЙОЛОП", "КІНЕЦЬ", "ДОЩ", "ЦИРК"],),
        "hard": (["УСПІХ", "ГУМОР", "ШИЯ", "ЮРИСТ", "ЧЕМПІОН", "СИМВОЛ", "ФАХ", "СПАЛАХ", "ІНЖЕНЕР", "ЛЮБОВ", "ПЕЧИВО", "ЛИСТЯ", "ФІЛОЛОГІЯ", "ФОРМА", "ГОРА", "ХВІСТ", "ФАНЕРА", "ШТАНИ", "СТРУМ",
                  "ДЕРЖАВА", "КОЗАЦТВО", "ЄДНІСТЬ", "ЗБРОЯРСТВO", "ЦІННІСТЬ", "ЩЕДРІСТЬ", "ДРУЖБА", "КУЛЬТУРА"],),
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
            (col1, "Легкий",   "Прості слова,\nідеально для початку",   "easy_button",   "easy"),
            (col2, "Середній", "Складніші слова,\nдля практики",         "medium_button", "medium"),
            (col3, "Складний", "Для досвідчених,\nрізноманітні слова",   "hard_button",   "hard"),
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

        col1, col2 = st.columns(2)

        with col1:
            if game_won:
                st.markdown(
                    '<div class="game-stat" style="text-align:center;margin-top:12px;">'
                    '<div class="game-stat-value">Чудово! Ви склали все слово! 🎉</div>'
                    '</div>',
                    unsafe_allow_html=True,
                )
            else:
                if "camera_key" not in st.session_state:
                    st.session_state.camera_key = 0
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
            if not game_won and current_index < len(word):
                current_letter = word[current_index]
                st.markdown(f'''
                <div class="game-stat">
                    <div class="game-stat-label">Покажіть жест для літери</div>
                    <div class="game-stat-value" style="font-size:56px;line-height:1.1;">{current_letter}</div>
                </div>
                ''', unsafe_allow_html=True)

            if not game_won:
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
