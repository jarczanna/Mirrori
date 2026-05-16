import streamlit as st

st.set_page_config(
    page_title="Mirrori - Stylizacja AI",
    page_icon="👗",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("## 👗 Stylizacja AI")
st.markdown("Twoja osobista stylistka — zatwierdzona przez człowieka.")
st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### Jestem klientką")
    st.markdown("Chcę poznać swój styl i otrzymać rekomendacje.")
    st.page_link("pages/1_user.py", label="Zacznij tutaj →", icon="👗")

with col2:
    st.markdown("### Jestem stylistką")
    st.markdown("Chcę przejrzeć i zatwierdzić analizy użytkowniczek.")
    st.page_link("pages/2_stylistka.py", label="Panel stylistki →", icon="🪡")
