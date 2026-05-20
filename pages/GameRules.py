import streamlit as st
import os
import utils

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
            'title': "Правила гри",
            'tagline': "Як грати в Heart in Gestures",
            'rules': [
                "Обери рівень складності. Гра побудована на жестах алфавіту української мови. Гравець має нескінченну кількість спроб .",
                "На екрані з'явиться вікно камери — виконуй жести, і система розпізнає їх за допомогою скелетної моделі руки.",
                "Жести розпізнаються <strong> незалежно від руки </strong>.",
                "Слово відображається на екрані. Гравець повинен відтворити кожну літер за хронологією.",
                "Щоб гра зарахувала відповідь, тримай руку в одному положенні <strong> після чого натисни Take a photo </strong>. Якщо жест вже розпізнано, він позначається як «already captured».",
                "Букви <strong>Ґ Д Є З Ї Й К Ц Щ Ь</strong> відсутні — вони нестатичні.",
                "Гра доступна лише <strong>українською мовою</strong>.",
            ]
        },
        'en': {
            'title': "Game Rules",
            'tagline': "How to play Heart in Gestures",
            'rules': [
                "Choose a difficulty level. The game uses gestures of the Ukrainian sign alphabet. The player has an infinite number of attempts.",
                "A camera window will appear — perform gestures and the system will recognise them using a hand skeleton model.",
                "All gestures are recognized <strong> independently of the hand </strong>",
                "The word is displayed on the screen. The player must play each letter in chronological order.",
                "To have the game count your response, hold your hand in one position <strong> and then tap Take a photo </strong>. If the gesture has already been recognized, it will be marked as «already captured».",
                "The letters <strong>Ґ Д Є З Ї Й К Ц Щ Ь</strong> are absent — they are not static signs.",
                "The game is available in <strong>Ukrainian only</strong>.",
            ]
        }
    }

    lang = st.session_state.language
    t = texts[lang]

    # Hero
    st.markdown(f'''
    <div class="page-hero">
        <div class="title_header">{t["title"]}</div>
        <p style="color:#ffffff; font-family:'Nunito',sans-serif; font-size:16px; margin-top:8px; font-weight:600;">
            {t["tagline"]}
        </p>
    </div>
    ''', unsafe_allow_html=True)

    # Step cards
    for i, rule in enumerate(t['rules']):
        st.markdown(f'''
        <div class="step-card">
            <div class="step-number">{i + 1}</div>
            <div class="step-text">{rule}</div>
        </div>
        ''', unsafe_allow_html=True)

