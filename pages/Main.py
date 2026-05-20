import streamlit as st
import GameRules
import Game
import Help
import AboutUs
import PublicOrganizations
import LearningMaterials
import utils

PAGES = {
    "Про проект": AboutUs,
    "Правила гри": GameRules,
    "Навчальні матеріали": LearningMaterials,
    "Гра": Game,
    "Допомогти проекту": Help,
    "Партнери/ГО": PublicOrganizations,
}

st.sidebar.title("Меню")
selection = st.sidebar.radio("Навігація", list(PAGES.keys()), label_visibility="collapsed")

page = PAGES[selection]
utils.load_css("style.css")
page.app()
