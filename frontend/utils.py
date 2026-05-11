import streamlit as st

def clear_temp():
    pattern = ("temp_", "tg_","t_")
    for key in list(st.session_state.keys()):
        if key.startswith(pattern):
            del st.session_state[key]

