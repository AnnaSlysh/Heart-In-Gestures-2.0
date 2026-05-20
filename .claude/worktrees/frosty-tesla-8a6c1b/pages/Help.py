import streamlit as st
import utils

def app():
    utils.load_css("style.css")

    if 'language' not in st.session_state:
        st.session_state.language = 'uk'

    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
    col_empty, col1, col2, col_empty2 = st.columns([2, 1, 1, 2])
    with col1:
        if st.button("Українська", use_container_width=True, key="ua_btn_help"):
            st.session_state.language = 'uk'
    with col2:
        if st.button("English", use_container_width=True, key="en_btn_help"):
            st.session_state.language = 'en'

    texts = {
        'uk': {
            'title': "Допомогти проєкту",
            'tagline': "Разом будуємо інклюзивне майбутнє",
            'join_title': "Приєднуйтесь до нас",
            'join_text': (
                "Станьте частиною нашої спільноти — разом ми можемо змінити світ!<br><br>"
                "З питань та пропозицій звертайтесь: "
                "<a href='mailto:hartingestures@gmail.com'>hartingestures@gmail.com</a>"
            ),
            'feedback_title': "Ваші відгуки — важливі для нас",
            'feedback_text': (
                "<strong>Нам важлива ваша думка!</strong> "
                "Якщо у вас є ідеї щодо покращення гри або ви хочете поділитися враженнями — напишіть нам!<br><br>"
                "<a href='https://docs.google.com/forms/d/e/1FAIpQLScAlVmTQe6wKm4U7bqtnEbU8pravDP0XuGnP7ZlMWWw9SPSHA/viewform?usp=header' target='_blank'>Надіслати відгук</a>"
            ),
            'spread_title': "Розповсюдження інформації",
            'spread_text': (
                "Розкажіть про наш проєкт друзям, у соцмережах чи на заходах. "
                "Це допомагає знайти нову аудиторію та потенційних партнерів.<br><br>"
                "<a href='https://www.instagram.com/heartingestures_/profilecard/?igsh=bHd2bGJnaWg4Ynp4' target='_blank'>Наш Instagram</a>"
            ),
            'partner_title': "Партнерство",
            'partner_text': (
                "Ми відкриті для співпраці з організаціями, що поділяють наші цінності!<br>"
                "Напишіть нам: "
                "<a href='mailto:hartingestures@gmail.com'>hartingestures@gmail.com</a>"
            ),
            'sign_off': "З повагою, команда Grlpwr"
        },
        'en': {
            'title': "Support the Project",
            'tagline': "Together we build an inclusive future",
            'join_title': "Join Us",
            'join_text': (
                "Become part of our community — together we can change the world!<br><br>"
                "For questions and suggestions: "
                "<a href='mailto:hartingestures@gmail.com'>hartingestures@gmail.com</a>"
            ),
            'feedback_title': "Your Feedback Matters",
            'feedback_text': (
                "<strong>Your opinion is important to us!</strong> "
                "If you have ideas for improving the game or want to share your impressions — write to us!<br><br>"
                "<a href='https://docs.google.com/forms/d/e/1FAIpQLScAlVmTQe6wKm4U7bqtnEbU8pravDP0XuGnP7ZlMWWw9SPSHA/viewform?usp=header' target='_blank'>Send Feedback</a>"
            ),
            'spread_title': "Spread the Word",
            'spread_text': (
                "Tell your friends about our project, share it on social media or at events. "
                "This helps us find a new audience and potential partners.<br><br>"
                "<a href='https://www.instagram.com/heartingestures_/profilecard/?igsh=bHd2bGJnaWg4Ynp4' target='_blank'>Our Instagram</a>"
            ),
            'partner_title': "Partnership",
            'partner_text': (
                "We are open to cooperation with organisations that share our values!<br>"
                "Write to us: "
                "<a href='mailto:hartingestures@gmail.com'>hartingestures@gmail.com</a>"
            ),
            'sign_off': "Respectfully, Grlpwr Team"
        }
    }

    lang = st.session_state.language
    t = texts[lang]

    st.markdown(f'''
    <div class="page-hero">
        <div class="title_header">{t["title"]}</div>
        <p>{t["tagline"]}</p>
    </div>
    ''', unsafe_allow_html=True)

    for title_key, body_key in [
        ('join_title', 'join_text'),
        ('feedback_title', 'feedback_text'),
        ('spread_title', 'spread_text'),
        ('partner_title', 'partner_text'),
    ]:
        st.markdown(f'''
        <div class="card">
            <div class="card-title">{t[title_key]}</div>
            <div class="card-body">{t[body_key]}</div>
        </div>
        ''', unsafe_allow_html=True)

    st.markdown(f'''
    <div style="text-align:center; margin-top:28px; font-family:'Inter',sans-serif;
                font-size:16px; font-weight:600; color:#2D6A4F;">
        {t["sign_off"]}
    </div>
    ''', unsafe_allow_html=True)
