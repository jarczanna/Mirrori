import streamlit as st

st.set_page_config(
    page_title="Stylizacja AI",
    page_icon="👗",
    layout="centered",
    initial_sidebar_ebar_state="collapsed"
)

st.markdown("## 👗 Stylizacja AI")
st.markdown("Twoja osobista stylistka — zatwierdzona przez człowieka.")
st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### Jestem klientką")
    st.markdown("Chcę poznać swój styl i otrzymać rekomendacje.")
    if st.button("Zacznij tutaj →", use_container_width=True):
        st.switch_page("pages/1_user.py")

with col2:
    st.markdown("### Jestem stylistką")
    st.markdown("Chcę przejrzeć i zatwierdzić analizy użytkowniczek.")
    if st.button("Panel stylistki →", use_container_width=True):
        st.switch_page("pages/2_stylistka.py")
