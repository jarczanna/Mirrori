import streamlit as st
import uuid
from services import supabase_service as db
from services import openai_service as ai

st.set_page_config(page_title="Mój styl", page_icon="👗", layout="centered")

# ─── SESSION STATE ───────────────────────────

if "user" not in st.session_state:
    st.session_state.user = None
if "step" not in st.session_state:
    st.session_state.step = "login"

# ─── HELPERS ─────────────────────────────────

def show_header():
    st.markdown("### 👗 Twoja osobista stylistka")
    st.markdown("---")

# ─── KROK 0: LOGIN / REJESTRACJA ─────────────

def step_login():
    show_header()
    st.subheader("Zacznij tutaj")

    email = st.text_input("Twój adres email")
    plan = st.radio("Wybierz plan", ["Essential — 29,99 zł/mies.", "Premium — 89 zł/mies."])
    plan_val = "essential" if "Essential" in plan else "premium"

    if st.button("Zaczynamy →"):
        if not email or "@" not in email:
            st.error("Podaj poprawny adres email.")
            return

        user = db.get_user_by_email(email)
        if not user:
            user = db.create_user(email, plan_val)

        st.session_state.user = user
        st.session_state.step = "ankieta" if not user["onboarding_completed"] else "wynik"
        st.rerun()

# ─── KROK 1: ANKIETA ─────────────────────────

def step_ankieta():
    show_header()
    st.subheader("Poznajmy się")
    st.caption("Odpowiedzi pomogą stylistce lepiej Cię zrozumieć. To zajmie ok. 3 minuty.")

    with st.form("ankieta_form"):
        st.markdown("**Twój styl życia**")
        styl_zycia = st.multiselect(
            "Gdzie głównie nosisz ubrania?",
            ["Biuro / praca hybrydowa", "Dom i codzienność", "Wyjścia i spotkania", "Sport i aktywność", "Eleganckie okazje"]
        )
        motywacja = st.text_area(
            "Co Cię skłoniło do szukania pomocy ze stylem?",
            placeholder="Np. po urodzeniu dziecka moje ciało się zmieniło i nie wiem co mi teraz pasuje..."
        )

        st.markdown("**Twoje preferencje**")
        styl_preferowany = st.multiselect(
            "Jaki styl Cię przyciąga?",
            ["Klasyczny / elegancki", "Casual / codzienny", "Minimalistyczny", "Kobiecy / romantyczny", "Sportowy", "Nie wiem — to chcę odkryć"]
        )
        czego_nie_lubi = st.text_area(
            "Czego absolutnie nie chcesz nosić?",
            placeholder="Np. zbyt obcisłe rzeczy, wzory, krótkie spódnice..."
        )

        st.markdown("**Twój budżet i zakupy**")
        budzet = st.select_slider(
            "Ile możesz przeznaczyć miesięcznie na ubrania?",
            options=["do 100 zł", "100–300 zł", "300–600 zł", "600–1000 zł", "powyżej 1000 zł"]
        )
        sklepy_ulubione = st.text_input(
            "Ulubione sklepy lub marki (opcjonalnie)",
            placeholder="Np. Zara, Reserved, H&M, Mango..."
        )

        st.markdown("**Twoja sylwetka**")
        wzrost = st.number_input("Wzrost (cm)", min_value=140, max_value=200, value=165)
        waga_feel = st.select_slider(
            "Jak się czujesz z aktualną sylwetką?",
            options=["Chcę ją ukryć", "Neutralnie", "Chcę ją podkreślić"]
        )

        submitted = st.form_submit_button("Dalej — wgraj zdjęcie →")

    if submitted:
        if not styl_zycia or not motywacja:
            st.error("Wypełnij przynajmniej styl życia i motywację.")
            return

        st.session_state.ankieta = {
            "styl_zycia": styl_zycia,
            "motywacja": motywacja,
            "styl_preferowany": styl_preferowany,
            "czego_nie_lubi": czego_nie_lubi,
            "budzet": budzet,
            "sklepy_ulubione": sklepy_ulubione,
            "wzrost": wzrost,
            "waga_feel": waga_feel
        }
        st.session_state.step = "zdjecie"
        st.rerun()

# ─── KROK 2: ZDJĘCIE ─────────────────────────

def step_zdjecie():
    show_header()
    st.subheader("Wgraj zdjęcie sylwetki")

    st.info(
        "📸 **Jak zrobić dobre zdjęcie?**\n\n"
        "- Stań prosto, całe ciało w kadrze (od stóp do głów)\n"
        "- Dopasowane lub obcisłe ubranie — żeby widać było sylwetkę\n"
        "- Jasne tło, dobre oświetlenie\n"
        "- Zdjęcie z przodu"
    )

    uploaded = st.file_uploader("Wybierz zdjęcie", type=["jpg", "jpeg", "png"])

    if uploaded:
        st.image(uploaded, caption="Podgląd", width=300)

        if st.button("Wyślij do analizy →"):
            with st.spinner("Przesyłam zdjęcie..."):
                file_bytes = uploaded.read()
                user_id = st.session_state.user["id"]
                photo_url = db.upload_sylwetka(user_id, file_bytes)

            with st.spinner("Tworzę analizę AI..."):
                ankieta = st.session_state.get("ankieta", {})
                analysis = db.create_analysis(user_id, photo_url, ankieta)
                import base64
                uploaded.seek(0)
                b64_image = base64.b64encode(uploaded.read()).decode("utf-8")
                ai_result = ai.analyze_sylwetka_b64(b64_image, ankieta)

                if "error" in ai_result:
                    st.error(f"Błąd analizy AI: {ai_result.get('error')}")
                    return

                db.save_ai_analysis(analysis["id"], ai_result)
                db.complete_onboarding(user_id)

            st.session_state.step = "oczekiwanie"
            st.rerun()

# ─── KROK 3: OCZEKIWANIE ─────────────────────

def step_oczekiwanie():
    show_header()
    st.subheader("Gotowe! 🎉")
    st.success(
        "Twoje zdjęcie i ankieta trafiły do stylistki.\n\n"
        "**Zatwierdzoną analizę otrzymasz w ciągu 48 godzin.**\n\n"
        "Wyślemy Ci email gdy będzie gotowa."
    )
    st.balloons()

    user = st.session_state.user
    analysis = db.get_user_analysis(user["id"])
    if analysis:
        st.session_state.step = "wynik"
        st.rerun()

# ─── KROK 4: WYNIK ───────────────────────────

def step_wynik():
    show_header()
    user = st.session_state.user
    analysis = db.get_user_analysis(user["id"])

    if not analysis:
        st.info("Twoja analiza jest w trakcie weryfikacji przez stylistkę. Wróć za chwilę.")
        if st.button("Odśwież"):
            st.rerun()
        return

    # Wybierz finalną analizę (korekta stylistki lub AI)
    final = analysis.get("stylistka_korekta") or analysis.get("ai_analysis_json") or {}

    st.markdown("## Twoja analiza stylu")
    st.success("✅ Zatwierdzone przez stylistkę")

    if analysis.get("stylistka_komentarz"):
        st.info(f"💬 Komentarz stylistki: {analysis['stylistka_komentarz']}")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Typ sylwetki", final.get("typ_sylwetki", "—").replace("_", " ").title())
        st.metric("Kolorystyka", final.get("kolorystyka", "—").title())
    with col2:
        st.metric("Podton skóry", final.get("podton_skory", "—").title())
        prop = final.get("proporcje", {})
        st.metric("Ramiona", prop.get("ramiona", "—").replace("_", " ").title())

    # Rekomendacje z fallbackiem dla starych analiz
    reko = final.get("rekomendacje_ogolne")
    unikac = final.get("czego_unikac")

    if not reko or not unikac:
        typ = final.get("typ_sylwetki", "")
        DOMYSLNE = {
            "A": {
                "reko": ["Podkreślaj górną część ciała", "Bluzki z detalami przy ramionach", "Spódnice A-line"],
                "unikac": ["Obcisłe spodnie bez balansu góry", "Wzory tylko na biodrach"]
            },
            "H": {
                "reko": ["Twórz iluzję talii paskami", "Sukienki z wcięciem w talii", "Bluzki z dekoltem V"],
                "unikac": ["Proste sukienki bez kształtu", "Oversizowe bluzy"]
            },
            "X": {
                "reko": ["Podkreślaj talię", "Dopasowane kroje", "Wrap dresses"],
                "unikac": ["Luźne workowate ubrania", "Proste kroje ukrywające sylwetkę"]
            },
            "V": {
                "reko": ["Równoważ proporcje szerszymi dołami", "Spodnie palazzo", "Spódnice rozkloszowane"],
                "unikac": ["Pagonki i szerokie ramiona", "Bluzki z dużymi detalami przy ramionach"]
            },
            "O": {
                "reko": ["Pionowe linie wyszczuplają", "Dobrze skrojone marynarki", "Dekolty V wydłużają"],
                "unikac": ["Duże wzory na brzuchu", "Zbyt obcisłe materiały"]
            }
        }
        defaults = DOMYSLNE.get(typ, {"reko": [], "unikac": []})
        reko = reko or defaults["reko"]
        unikac = unikac or defaults["unikac"]

    if reko:
        st.markdown("### Co Ci pasuje")
        for r in reko:
            st.markdown(f"✓ {r}")

    if unikac:
        st.markdown("### Czego unikać")
        for u in unikac:
            st.markdown(f"✗ {u}")

    if user["plan"] == "essential":
        st.markdown("---")
        st.markdown("### 🌟 Chcesz więcej?")
        st.markdown(
            "W planie **Premium** stylistka co miesiąc przygotuje dla Ciebie stylizacje "
            "z rzeczy które już masz w szafie — i powie Ci co założyć każdego tygodnia."
        )
        st.button("Przejdź na Premium — 89 zł/mies.")

# ─── ROUTER ──────────────────────────────────

step = st.session_state.step

if step == "login":
    step_login()
elif step == "ankieta":
    step_ankieta()
elif step == "zdjecie":
    step_zdjecie()
elif step == "oczekiwanie":
    step_oczekiwanie()
elif step == "wynik":
    step_wynik()
