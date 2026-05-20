import streamlit as st
import utils

def app():
    utils.load_css("style.css")

    if 'language' not in st.session_state:
        st.session_state.language = 'uk'

    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
    col_empty, col1, col2, col_empty2 = st.columns([2, 1, 1, 2])
    with col1:
        if st.button("Українська", use_container_width=True, key="ua_btn_learning"):
            st.session_state.language = 'uk'
    with col2:
        if st.button("English", use_container_width=True, key="en_btn_learning"):
            st.session_state.language = 'en'

    texts = {
        'uk': {
            'title': "Навчальні матеріали",
            'tagline': "Відео та ресурси для вивчення жестового алфавіту",
            'subtitle1': "Корисні посилання",
            'subtitle2': "Легкий рівень",
            'subtitle3': "Середній рівень",
            'subtitle4': "Складний рівень",
            'links': (
                '<a href="https://spreadthesign.com/uk.ua/search/?cls=1" target="_blank">Spread The Sign — онлайн-словник жестів</a><br><br>'
                '<a href="https://megogo.net/ua/view/3820211-kurs-zhestovo-movi-ukra-nskoyu-movoyu.html" target="_blank">Курс жестової мови на Megogo</a>'
            )
        },
        'en': {
            'title': "Educational Materials",
            'tagline': "Videos and resources for learning the sign alphabet",
            'subtitle1': "Useful Links",
            'subtitle2': "Easy Level",
            'subtitle3': "Medium Level",
            'subtitle4': "Hard Level",
            'links': (
                '<a href="https://spreadthesign.com/uk.ua/search/?cls=1" target="_blank">Spread The Sign — online sign dictionary</a><br><br>'
                '<a href="https://megogo.net/ua/view/3820211-kurs-zhestovo-movi-ukra-nskoyu-movoyu.html" target="_blank">Sign language course on Megogo</a>'
            )
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

    st.markdown(f'<div class="section-tag">{t["subtitle1"]}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="card"><div class="card-body">{t["links"]}</div></div>', unsafe_allow_html=True)
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    def render_video_section(label, pairs):
        st.markdown(f'<div class="section-tag">{label}</div>', unsafe_allow_html=True)
        st.markdown("<div style='margin-bottom:12px;'></div>", unsafe_allow_html=True)
        left = pairs[::2]
        right = pairs[1::2]
        col1, col2 = st.columns(2)
        for col, items in [(col1, left), (col2, right)]:
            with col:
                for url, letter in items:
                    st.video(url)
                    st.markdown(
                        f'<div class="letter-badge">{letter}</div>',
                        unsafe_allow_html=True
                    )
                    st.markdown("<div style='margin-bottom:12px;'></div>", unsafe_allow_html=True)

    easy_pairs = [
        ("https://www.youtube.com/watch?v=Y3yPvsOLc5k", "А"),
        ("https://www.youtube.com/watch?v=8j7KZnsBfhY", "Е"),
        ("https://www.youtube.com/watch?v=B78Ou5oPtdo", "И"),
        ("https://www.youtube.com/watch?v=02Cb_huQRmw", "О"),
        ("https://www.youtube.com/watch?v=B78Ou5oPtdo", "Н"),
        ("https://www.youtube.com/watch?v=m2pcbkZKQCU", "П"),
        ("https://www.youtube.com/watch?v=LJjonvptVAo", "С"),
        ("https://www.youtube.com/watch?v=WeBxscv_iFE", "Т"),
        ("https://www.youtube.com/watch?v=nJfXbqjyaB4", "Л"),
        ("https://www.youtube.com/watch?v=9ivfqYlRQw4", "М"),
    ]
    render_video_section(t['subtitle2'], easy_pairs)
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    medium_pairs = [
        ("https://www.youtube.com/watch?v=Y3yPvsOLc5k", "А"),
        ("https://www.youtube.com/watch?v=A4kQCBdG5HA", "Б"),
        ("https://www.youtube.com/watch?v=q_6cni-XkUY", "В"),
        ("https://www.youtube.com/watch?v=8j7KZnsBfhY", "Е"),
        ("https://www.youtube.com/watch?v=B78Ou5oPtdo", "И"),
        ("https://www.youtube.com/watch?v=uCRSEbYOys4", "І"),
        ("https://www.youtube.com/watch?v=B78Ou5oPtdo", "Н"),
        ("https://www.youtube.com/watch?v=nJfXbqjyaB4", "Л"),
        ("https://www.youtube.com/watch?v=9ivfqYlRQw4", "М"),
        ("https://www.youtube.com/watch?v=02Cb_huQRmw", "О"),
        ("https://www.youtube.com/watch?v=m2pcbkZKQCU", "П"),
        ("https://www.youtube.com/watch?v=2Xzzg2Qk_zA", "Р"),
        ("https://www.youtube.com/watch?v=LJjonvptVAo", "С"),
        ("https://www.youtube.com/watch?v=WeBxscv_iFE", "Т"),
        ("https://www.youtube.com/watch?v=LfGdX20yQ_g", "У"),
    ]
    render_video_section(t['subtitle3'], medium_pairs)
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    hard_pairs = [
        ("https://www.youtube.com/watch?v=Y3yPvsOLc5k", "А"),
        ("https://www.youtube.com/watch?v=A4kQCBdG5HA", "Б"),
        ("https://www.youtube.com/watch?v=q_6cni-XkUY", "В"),
        ("https://www.youtube.com/watch?v=X2ymxV1SB_M", "Г"),
        ("https://www.youtube.com/watch?v=8j7KZnsBfhY", "Е"),
        ("https://www.youtube.com/watch?v=teAEIt6anLE", "Ж"),
        ("https://www.youtube.com/watch?v=B78Ou5oPtdo", "И"),
        ("https://www.youtube.com/watch?v=uCRSEbYOys4", "І"),
        ("https://www.youtube.com/watch?v=nJfXbqjyaB4", "Л"),
        ("https://www.youtube.com/watch?v=9ivfqYlRQw4", "М"),
        ("https://www.youtube.com/watch?v=B78Ou5oPtdo", "Н"),
        ("https://www.youtube.com/watch?v=02Cb_huQRmw", "О"),
        ("https://www.youtube.com/watch?v=m2pcbkZKQCU", "П"),
        ("https://www.youtube.com/watch?v=2Xzzg2Qk_zA", "Р"),
        ("https://www.youtube.com/watch?v=LJjonvptVAo", "С"),
        ("https://www.youtube.com/watch?v=WeBxscv_iFE", "Т"),
        ("https://www.youtube.com/watch?v=LfGdX20yQ_g", "У"),
        ("https://www.youtube.com/watch?v=b41xE7IH5DM", "Ф"),
        ("https://www.youtube.com/watch?v=S1Mz4FtK3y0", "Х"),
        ("https://www.youtube.com/watch?v=o-UzR-smI90", "Ч"),
        ("https://www.youtube.com/watch?v=uqcAzaxvmQg", "Ш"),
        ("https://www.youtube.com/watch?v=s5pHhi0l_ZY", "Ю"),
        ("https://www.youtube.com/watch?v=Ziqz_58nOVo", "Я"),
    ]
    render_video_section(t['subtitle4'], hard_pairs)
