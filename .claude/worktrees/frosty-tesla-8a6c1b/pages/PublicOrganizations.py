import streamlit as st
import utils

def app():
    utils.load_css("style.css")

    if 'language' not in st.session_state:
        st.session_state.language = 'uk'

    # Language toggle
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
            'title': "Партнери / ГО",
            'tagline': "Організації, що об'єднують людей з порушеннями слуху",
            'utog_title': "УТОГ",
            'utog_logo': "https://cnap-pl.gov.ua/UTOG_OVAL.png",
            'utog_text': (
                "Всеукраїнська громадська організація людей з вадами слуху, заснована у <strong>1933 році</strong>. "
                "Є членом Всесвітньої федерації глухих. "
                "Регіональні та територіальні організації УТОГ об'єднують понад <strong>50 000 громадян</strong> України з порушеннями слуху та мови."
            ),
            'invasport_title': "ІНВАСПОРТ",
            'invasport_logo': "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcT2LzUJRpQ_EDlyT0Wgkl9ccfboOfBD3f6n3A&s",
            'invasport_text': (
                "Всеукраїнська громадська організація спортивного спрямування. "
                "Спортивна федерація глухих України забезпечує розвиток <strong>олімпійського руху</strong> і спорту "
                "для людей з вадами слуху по всій країні."
            ),
            'pog_title': "ПОГ — Центр соціального бізнесу",
            'pog_logo': "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRa7-D_kDabaXFJgBVHmstmmsyAZfTLstru9A&s",
            'pog_text': (
                "Надає послуги перекладу жестової мови у будь-якому зручному форматі. "
                "Оскільки багато сучасних слів не існують у жестовій мові, "
                "команда активно використовує <strong>українську дактильну абетку</strong>. "
                "Також проводить заходи з безбар'єрності."
            ),
        },
        'en': {
            'title': "Partners / NGOs",
            'tagline': "Organisations uniting people with hearing impairments",
            'utog_title': "UTOG",
            'utog_logo': "https://cnap-pl.gov.ua/UTOG_OVAL.png",
            'utog_text': (
                "The All-Ukrainian Public Organisation of People with Hearing Impairments, founded in <strong>1933</strong>. "
                "A member of the World Federation of the Deaf. "
                "Regional and territorial UTOG organisations unite over <strong>50,000 Ukrainian citizens</strong> "
                "with hearing and speech impairments."
            ),
            'invasport_title': "INVASPORT",
            'invasport_logo': "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcT2LzUJRpQ_EDlyT0Wgkl9ccfboOfBD3f6n3A&s",
            'invasport_text': (
                "An all-Ukrainian public sports organisation. "
                "The Sports Federation of the Deaf of Ukraine ensures the development of the "
                "<strong>Olympic movement</strong> and sports for people with hearing disabilities across the country."
            ),
            'pog_title': "POG — Centre for Social Business",
            'pog_logo': "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRa7-D_kDabaXFJgBVHmstmmsyAZfTLstru9A&s",
            'pog_text': (
                "Provides sign language interpretation services in any convenient format. "
                "Since many modern words have no sign equivalent, the team actively uses the "
                "<strong>Ukrainian dactylic alphabet</strong>. "
                "They also organise accessibility and barrier-free events."
            ),
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

    # Partner cards — fully self-contained HTML so the box wraps everything
    partners = [
        ('utog_title', 'utog_logo', 'utog_text'),
        ('invasport_title', 'invasport_logo', 'invasport_text'),
        ('pog_title', 'pog_logo', 'pog_text'),
    ]

    for title_key, logo_key, body_key in partners:
        st.markdown(f'''
        <div class="partner-card" style="display:flex; align-items:flex-start; gap:24px;">
            <img src="{t[logo_key]}" width="110" style="border-radius:12px; flex-shrink:0; object-fit:contain;">
            <div>
                <div class="partner-name">{t[title_key]}</div>
                <div class="partner-body">{t[body_key]}</div>
            </div>
        </div>
        ''', unsafe_allow_html=True)
