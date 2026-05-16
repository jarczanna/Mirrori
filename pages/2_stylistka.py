import streamlit as st
import json
import os
from dotenv import load_dotenv
from services import supabase_service as db

load_dotenv()

st.set_page_config(page_title="Panel stylistki", page_icon="🪡", layout="wide")

# ─── AUTORYZACJA ─────────────────────────────

def check_auth():
    if "stylistka_auth" not in st.session_state:
        st.session_state.stylistka_auth = False

    if not st.session_state.stylistka_auth:
        st.markdown("### 🪡 Panel stylistki")
        password = st.text_input("Hasło", type="password")
        if st.button("Wejdź"):
            correct = os.environ.get("STYLISTKA_PASSWORD", "")
            if password == correct:
                st.session_state.stylistka_auth = True
                st.rerun()
            else:
                st.error("Nieprawidłowe hasło.")
        st.stop()

check_auth()

# ─── HEADER ──────────────────────────────────

st.markdown("## 🪡 Panel stylistki")
st.markdown("---")

tab1, tab2 = st.tabs(["📋 Kolejka do weryfikacji", "✅ Zatwierdzone"])

# ─── TAB 1: KOLEJKA ──────────────────────────

with tab1:
    pending = db.get_pending_analyses()

    if not pending:
        st.info("Brak analiz oczekujących na weryfikację.")
    else:
        st.caption(f"{len(pending)} analiz czeka na weryfikację")

        for analysis in pending:
            user_email = analysis.get("users", {}).get("email", "—")
            user_plan = analysis.get("users", {}).get("plan", "essential")
            created = analysis.get("created_at", "")[:10]

            with st.expander(f"👤 {user_email} · {user_plan.upper()} · {created}", expanded=True):
                col_photo, col_data = st.columns([1, 2])

                # Zdjęcie sylwetki
                with col_photo:
                    photo_url = analysis.get("photo_url")
                    if photo_url:
                        st.image(photo_url, caption="Zdjęcie sylwetki", width=280)
                    else:
                        st.warning("Brak zdjęcia")

                # Dane z ankiety i analiza AI
                with col_data:
                    st.markdown("**Ankieta użytkowniczki**")
                    ankieta = analysis.get("ankieta_json", {})
                    if ankieta:
                        st.markdown(f"- **Motywacja:** {ankieta.get('motywacja', '—')}")
                        st.markdown(f"- **Styl życia:** {', '.join(ankieta.get('styl_zycia', []))}")
                        st.markdown(f"- **Preferencje:** {', '.join(ankieta.get('styl_preferowany', []))}")
                        st.markdown(f"- **Czego nie lubi:** {ankieta.get('czego_nie_lubi', '—')}")
                        st.markdown(f"- **Budżet:** {ankieta.get('budzet', '—')}")
                        st.markdown(f"- **Wzrost:** {ankieta.get('wzrost', '—')} cm")

                    st.markdown("---")
                    st.markdown("**Analiza AI**")
                    ai_json = analysis.get("ai_analysis_json", {})

                    if ai_json:
                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.markdown(f"**Typ sylwetki:** {ai_json.get('typ_sylwetki', '—')}")
                            st.markdown(f"**Kolorystyka:** {ai_json.get('kolorystyka', '—')}")
                            st.markdown(f"**Podton:** {ai_json.get('podton_skory', '—')}")
                        with col_b:
                            prop = ai_json.get("proporcje", {})
                            st.markdown(f"**Ramiona:** {prop.get('ramiona', '—')}")
                            st.markdown(f"**Talia:** {prop.get('talia', '—')}")
                            st.markdown(f"**Biodra:** {prop.get('biodra', '—')}")

                        pewnosc = ai_json.get("pewnosc_analizy", "—")
                        kolor = "🟢" if pewnosc == "wysoka" else "🟡" if pewnosc == "srednia" else "🔴"
                        st.caption(f"{kolor} Pewność analizy AI: **{pewnosc}**")

                        if ai_json.get("uwagi"):
                            st.warning(f"⚠️ Uwagi AI: {ai_json['uwagi']}")
                    else:
                        st.warning("Brak analizy AI")

                # Akcje stylistki
                st.markdown("---")
                st.markdown("**Twoja decyzja**")

                TYPY_SYLWETKI = {
                    "A — trójkąt (węższe ramiona, szersze biodra)": "A",
                    "H — prostokąt (ramiona i biodra podobnej szerokości)": "H",
                    "X — klepsydra (ramiona i biodra podobne, zaznaczona talia)": "X",
                    "V — odwrócony trójkąt (szersze ramiona, węższe biodra)": "V",
                    "O — owal (zaokrąglona sylwetka)": "O",
                }

                ai_typ = ai_json.get("typ_sylwetki", "A") if ai_json else "A"
                ai_pewnosc = ai_json.get("pewnosc_typu", 0) if ai_json else 0

                # Znajdź domyślny wybór na podstawie wyniku AI
                domyslny = next(
                    (k for k, v in TYPY_SYLWETKI.items() if v == ai_typ),
                    list(TYPY_SYLWETKI.keys())[0]
                )

                st.caption(f"AI zaproponowało: **{ai_typ}** z pewnością **{ai_pewnosc}%**")

                wybrany_label = st.selectbox(
                    "Typ sylwetki (zatwierdź lub zmień):",
                    options=list(TYPY_SYLWETKI.keys()),
                    index=list(TYPY_SYLWETKI.keys()).index(domyslny),
                    key=f"typ_{analysis['id']}"
                )
                wybrany_typ = TYPY_SYLWETKI[wybrany_label]

                komentarz = st.text_input(
                    "Komentarz dla użytkowniczki (opcjonalnie)",
                    placeholder="Np. Zwróć uwagę na podkreślenie talii...",
                    key=f"comment_{analysis['id']}"
                )

                # Buduj korektę tylko jeśli zmieniono typ
                def build_korekta():
                    if not ai_json:
                        return None
                    if wybrany_typ != ai_typ:
                        korekta = dict(ai_json)
                        korekta["typ_sylwetki"] = wybrany_typ
                        return korekta
                    return None

                col_btn1, col_btn2 = st.columns([1, 4])
                with col_btn1:
                    if st.button("✅ Zatwierdź", key=f"approve_{analysis['id']}", type="primary"):
                        korekta_json = build_korekta()
                        db.approve_analysis(
                            analysis_id=analysis["id"],
                            korekta=korekta_json,
                            komentarz=komentarz or None
                        )
                        final = korekta_json or ai_json
                        if final and "typ_sylwetki" in final:
                            db.add_style_case(analysis["id"], final)
                        # Usuń zdjęcie z Storage po zatwierdzeniu (RODO)
                        user_id = analysis.get("user_id")
                        if user_id:
                            db.delete_sylwetka(user_id)
                        st.success("Zatwierdzono! Użytkowniczka zobaczy wynik.")
                        st.rerun()

# ─── TAB 2: ZATWIERDZONE ─────────────────────

with tab2:
    sb = db.get_service_client()
    approved = (
        sb.table("analyses")
        .select("*, users(email, plan)")
        .in_("status", ["approved", "corrected"])
        .order("updated_at", desc=True)
        .limit(50)
        .execute()
    )
    data = approved.data or []

    if not data:
        st.info("Brak zatwierdzonych analiz.")
    else:
        st.caption(f"{len(data)} zatwierdzonych analiz")
        for a in data:
            email = a.get("users", {}).get("email", "—")
            status = a.get("status", "—")
            updated = a.get("updated_at", "")[:10]
            ikona = "✅" if status == "approved" else "✏️"
            st.markdown(f"{ikona} **{email}** · {status} · {updated}")
