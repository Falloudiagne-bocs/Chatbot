# streamlit_app.py
import streamlit as st
from dotenv import load_dotenv
from chatbocs_app.config import AppConfig
from chatbocs_app.services.agno_system import get_system
from chatbocs_app.ui.layout import render_sidebar, render_chat_panel, render_history, render_footer
import os
from dotenv import load_dotenv
load_dotenv()

def main():
    load_dotenv()
    st.set_page_config(page_title="chatBOCS AGNO", layout="wide", page_icon="🤖")
    st.title("🤖 chatBOCS AGNO - Assistant IA")

    if "conversations" not in st.session_state:
        st.session_state.conversations = []

    cfg = AppConfig()
    system = get_system(cfg)

    # Sidebar (returns controls values)
    top_k, memory_k = render_sidebar(system, cfg)

    # Chat area
    send_clicked, user_query = render_chat_panel(system, top_k, memory_k)
    if send_clicked:
        st.rerun()

    # History
    render_history()

    # Footer
    render_footer()

if __name__ == "__main__":
    main()
