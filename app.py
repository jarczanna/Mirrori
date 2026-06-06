import streamlit as st

st.set_page_config(
    page_title="Mirrori",
    page_icon="👗",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("## 👗 Mirrori")
st.markdown("Twój osobisty stylista - analiza AI, zatwierdzona przez człowieka.")
st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### Jestem klientem")
    st.markdown("Chcę poznać swój styl i otrzymać rekomendacje.")
    if st.button("Zacznij tutaj →", use_container_width=True):
        st.switch_page("pages/1_user.py")

with col2:
    st.markdown("### Jestem stylistą")
    st.markdown("Chcę przejrzeć i zatwierdzić analizy użytkowników.")
    if st.button("Panel stylistki →", use_container_width=True):
        st.switch_page("pages/2_stylistka.py")
