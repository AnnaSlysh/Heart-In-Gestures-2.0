import streamlit as st
import utils
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def app():
    utils.load_css("style.css")

    if 'language' not in st.session_state:
        st.session_state.language = 'uk'

    # Language toggle
    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
    col_empty, col1, col2, col_empty2 = st.columns([1, 2, 2, 1])
    with col1:
        if st.button("Українська", use_container_width=True, key="ua_btn_about_final"):
            st.session_state.language = 'uk'
    with col2:
        if st.button("English", use_container_width=True, key="en_btn_about_final"):
            st.session_state.language = 'en'

    texts = {
        'uk': {
            'about_us': "Про нас",
            'tagline': "Heart in Gestures — гра для вивчення жестового алфавіту",
            'about_text': (
                "Ми — група підлітків, учасниці міжнародного проекту <strong>Technovation Girls</strong>. "
                "Ми довго обирали тему і зупинилися на інклюзії. "
                "Наша мрія — допомагати дітям з вадами слуху вливатися у сучасне суспільство, "
                "рухатися вперед і не відчувати себе зайвими. "
                "Так народилась ідея доступної гри для навчання жестового українського алфавіту, "
                "яка об'єднує людей різних культур і середовищ."
            ),
            'mission_icon': "",
            'mission': "Місія",
            'mission_text': "Сприяти розвитку інклюзивного суспільства, де кожен має голос.",
            'vision_icon': "",
            'vision': "Візія",
            'vision_text': (
                "Світ, у якому мовне різноманіття сприймається як сила, "
                "а кожна людина — незалежно від її здатності чути — "
                "має рівний доступ до спілкування, освіти й можливостей."
            ),
            'goal_icon': "",
            'goal': "Мета",
            'goal_text': (
                "Сприяти побудові інклюзивного суспільства, де жестова мова є природною частиною взаємодії, "
                "а технології стають засобом рівності, підтримки та взаєморозуміння."
            )
        },
        'en': {
            'about_us': "About Us",
            'tagline': "Heart in Gestures — a game for learning the sign alphabet",
            'about_text': (
                "We are a group of teenagers participating in the international project <strong>Technovation Girls</strong>. "
                "We spent a long time choosing our topic and settled on inclusion. "
                "Our dream is to help children with hearing impairments integrate into modern society, "
                "move forward, and not feel left out. "
                "This sparked the idea for an accessible game to teach the Ukrainian sign language alphabet, "
                "bringing together people from different cultures and backgrounds."
            ),
            'mission_icon': "",
            'mission': "Mission",
            'mission_text': "To promote the development of an inclusive society where everyone has a voice.",
            'vision_icon': "",
            'vision': "Vision",
            'vision_text': (
                "A world where linguistic diversity is embraced as a strength, "
                "and every person — regardless of their ability to hear — "
                "has equal access to communication, education, and opportunities."
            ),
            'goal_icon': "",
            'goal': "Goal",
            'goal_text': (
                "To help build an inclusive society where sign language is a natural part of interaction, "
                "and technology becomes a means of equality, support, and understanding."
            )
        }
    }

    lang = st.session_state.language
    t = texts[lang]

    # Hero section
    st.markdown(f'''
    <div class="page-hero">
        <div class="title_header">{t["about_us"]}</div>
        <p style="color:#ffffff; font-family:'Nunito',sans-serif; font-size:16px; margin-top:8px; font-weight:600;">
            {t["tagline"]}
        </p>
    </div>
    ''', unsafe_allow_html=True)

    # Banner image
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        svg_path = "images/icon.svg"
        if os.path.exists(svg_path):
            st.image(svg_path, use_container_width=True)

    # Mission / Vision / Goal cards
    for title_key, body_key in [
        ('mission', 'mission_text'),
        ('vision', 'vision_text'),
        ('goal', 'goal_text'),
    ]:
        st.markdown(f'''
        <div class="card">
            <div class="card-title">{t[title_key]}</div>
            <div class="card-body">{t[body_key]}</div>
        </div>
        ''', unsafe_allow_html=True)
