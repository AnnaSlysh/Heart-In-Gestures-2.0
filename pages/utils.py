import streamlit as st
import os

def load_css(file_name):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', file_name)
    with open(path, "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)