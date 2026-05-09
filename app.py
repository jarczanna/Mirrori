import streamlit as st

st.set_page_config(page_title="Mirrori", page_icon="🪞")

page = st.sidebar.selectbox("Widok", ["Użytkowniczka", "Stylistka"])

if page == "Użytkowniczka":
    st.title("🪞 Mirrori")
    st.write("Analiza sylwetki")
    
    uploaded_file = st.file_uploader("Wgraj zdjęcie sylwetki (bez twarzy)", type=["jpg", "jpeg", "png"])
    
    if uploaded_file:
        st.image(uploaded_file, width=300)
        st.success("Zdjęcie wgrane!")

elif page == "Stylistka":
    st.title("Panel stylistki")
    st.write("Tu będzie kolejka do weryfikacji")
