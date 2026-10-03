import streamlit as st
from services.school_service import SchoolService
from services.probability_service import ProbabilityService

# Konfiguracja strony
st.set_page_config(
    page_title="Moja Droga – Kraków 2026",
    page_icon="🎓",
    layout="wide"
)


# Inicjalizacja serwisów
@st.cache_resource
def get_services():
    return SchoolService(), ProbabilityService()


school_service, prob_service = get_services()

# Tabela przeliczania ocen na punkty rekrutacyjne
GRADE_POINTS = {
    "6 (celujący)": 18,
    "5 (bardzo dobry)": 17,
    "4 (dobry)": 14,
    "3 (dostateczny)": 8,
    "2 (dopuszczający)": 2
}


def match_requirement_to_user_subject(req_str: str) -> str:
    """
    Rygorystycznie mapuje ciąg tekstowy z wymogów klasy na konkretny przedmiot ze świadectwa ucznia.
    Zapobiega przypadkowemu zastępowaniu przedmiotów ścisłych/humanistycznych przez języki obce oraz myleniu WF z Fizyką.
    """
    req = str(req_str).lower().strip()

    # 1. NAJPIERW sprawdzamy nazwy wielowyrazowe i skróty (zanim krótkie fragmenty jak "fiz" przechwycą słowa)
    if "wychowanie fizyczne" in req or req == "wf":
        return "Wychowanie fizyczne"
    if "edukacja dla bezpieczeństwa" in req or req == "edb":
        return "Edukacja dla bezpieczeństwa"
    if "wiedza o społeczeństwie" in req or "wos" in req:
        return "Wiedza o społeczeństwie"
    if "drugi" in req:
        return "Drugi język obcy"

    # 2. Przedmioty jednowyrazowe (ścisłe dopasowanie po nazwie/skrócie)
    if "fizyka" in req or req == "fiz":
        return "Fizyka"
    if "geografia" in req or "geo" in req:
        return "Geografia"
    if "historia" in req or "hist" in req:
        return "Historia"
    if "biologia" in req or "biol" in req:
        return "Biologia"
    if "chemia" in req or "chem" in req:
        return "Chemia"
    if "informatyka" in req or "inf" in req:
        return "Informatyka"
    if "muzyka" in req:
        return "Muzyka"
    if "plastyka" in req:
        return "Plastyka"
    if "matematyka" in req or "mat" in req:
        return "Matematyka"
    if "polski" in req:
        return "Język polski"

    # 3. Pierwszy (wiodący) język obcy
    lang_keywords = ["angielski", "niemiecki", "hiszpański", "francuski", "włoski", "rosyjski", "łaciński",
                     "język obcy", "ang"]
    if any(lang in req for lang in lang_keywords):
        return "Pierwszy język obcy"

    return None


def calculate_class_score(grades: dict, exam_pts: float, achieve_pts: float, cls_info: dict):
    """
    Wylicza punkty rekrutacyjne dedykowane dla konkretnej klasy:
    - Język polski (obowiązkowy)
    - Matematyka (obowiązkowa)
    - 2 przedmioty wskazane przez profil/wymagania klasy (lub najlepsze pozostałe w przypadku braku danych)
    """
    p_pol = GRADE_POINTS.get(grades.get("Język polski", "4 (dobry)"), 14)
    p_mat = GRADE_POINTS.get(grades.get("Matematyka", "4 (dobry)"), 14)

    # Najpierw sprawdzamy, czy w JSONie jest jawna lista 'counted_subjects', a jeśli nie – bierzemy 'extensions'
    req_list = cls_info.get("counted_subjects") or cls_info.get("extensions") or []

    counted_subjects = []
    used_user_subject_keys = ["Język polski", "Matematyka"]
    total_other_pts = 0

    # Krok A: Dopasowanie wg wymagań klasy
    for req in req_list:
        if len(counted_subjects) >= 2:
            break

        mapped_user_sub = match_requirement_to_user_subject(req)
        if mapped_user_sub and mapped_user_sub not in used_user_subject_keys:
            pts = GRADE_POINTS.get(grades.get(mapped_user_sub, ""), 0)
            total_other_pts += pts
            counted_subjects.append(mapped_user_sub)
            used_user_subject_keys.append(mapped_user_sub)

    # Krok B: Jeśli profil podał mniej niż 2 pasujące przedmioty, uzupełniamy najwyższymi ocenami z pozostałych
    if len(counted_subjects) < 2:
        remaining = []
        for sub, val in grades.items():
            if sub not in used_user_subject_keys:
                remaining.append((GRADE_POINTS.get(val, 0), sub))

        # Sortowanie po punktach malejąco
        remaining.sort(key=lambda x: x[0], reverse=True)

        needed = 2 - len(counted_subjects)
        for pts, sub in remaining[:needed]:
            total_other_pts += pts
            counted_subjects.append(sub)
            used_user_subject_keys.append(sub)

    total_score = min(200.0, exam_pts + p_pol + p_mat + total_other_pts + achieve_pts)
    return total_score, counted_subjects


# Nagłówek główny
st.title("🎓 Moja Droga – Wybór Szkoły Ponadpodstawowej")
st.caption("Kalkulator punktów i wyszukiwarka szkół dla ósmoklasistów w Krakowie")

# Zakładki aplikacji
tab1, tab2, tab3 = st.tabs(["1. Kalkulator Ocen i Egzaminów", "2. Wyszukiwarka Szkół", "3. Raport Szans"])

# -----------------------------------------------------------------------------
# ZAKŁADKA 1: KALKULATOR PEŁNEGO ŚWIADECTWA
# -----------------------------------------------------------------------------
with tab1:
    st.header("Krok 1: Wprowadź swoje przewidywane wyniki i oceny")

    col_ex, col_ach = st.columns(2)

    with col_ex:
        st.subheader("1. Wyniki z Egzaminu Ósmoklasisty (%)")

        ex_pol = st.number_input("Język polski (%)", min_value=0, max_value=100, value=80)
        pts_pol = ex_pol * 0.35
        st.caption(f"→ **{pts_pol:.2f} pkt** rekrutacyjnych (wynik % × 0,35)")

        ex_mat = st.number_input("Matematyka (%)", min_value=0, max_value=100, value=75)
        pts_mat = ex_mat * 0.35
        st.caption(f"→ **{pts_mat:.2f} pkt** rekrutacyjnych (wynik % × 0,35)")

        ex_eng = st.number_input("Język obcy (%)", min_value=0, max_value=100, value=90)
        pts_eng = ex_eng * 0.30
        st.caption(f"→ **{pts_eng:.2f} pkt** rekrutacyjnych (wynik % × 0,30)")

        exam_pts = pts_pol + pts_mat + pts_eng
        st.info(f"Suma punktów z egzaminów: **{exam_pts:.2f} / 100 pkt**")

    with col_ach:
        st.subheader("2. Dodatkowe osiągnięcia")
        honors = st.checkbox("Świadectwo z wyróżnieniem (z paskiem) [+7 pkt]", value=True)
        volunteering = st.checkbox("Wolontariat [+3 pkt]", value=True)
        extra_pts = st.number_input("Punkty za sukcesy w konkursach (max 18 pkt)", min_value=0.0, max_value=18.0,
                                    value=0.0)

        achieve_pts = (7.0 if honors else 0.0) + (3.0 if volunteering else 0.0) + extra_pts
        st.info(f"Punkty za osiągnięcia: **{achieve_pts:.2f} / 28 pkt**")

    st.subheader("3. Przewidywane oceny na świadectwie ukończenia szkoły")
    st.caption(
        "Wpisz oceny ze wszystkich przedmiotów. System automatycznie dobierze 2 właściwe przedmioty do przeliczenia punktów przy każdej analizowanej klasie.")

    grade_list = list(GRADE_POINTS.keys())

    col_g1, col_g2, col_g3 = st.columns(3)

    user_grades = {}
    with col_g1:
        user_grades["Język polski"] = st.selectbox("Język polski", grade_list, index=1)
        user_grades["Matematyka"] = st.selectbox("Matematyka", grade_list, index=1)
        user_grades["Pierwszy język obcy"] = st.selectbox("Pierwszy język obcy", grade_list, index=1)
        user_grades["Drugi język obcy"] = st.selectbox("Drugi język obcy", grade_list, index=1)
        user_grades["Historia"] = st.selectbox("Historia", grade_list, index=2)

    with col_g2:
        user_grades["Biologia"] = st.selectbox("Biologia", grade_list, index=1)
        user_grades["Chemia"] = st.selectbox("Chemia", grade_list, index=2)
        user_grades["Fizyka"] = st.selectbox("Fizyka", grade_list, index=2)
        user_grades["Geografia"] = st.selectbox("Geografia", grade_list, index=1)
        user_grades["Informatyka"] = st.selectbox("Informatyka", grade_list, index=1)

    with col_g3:
        user_grades["Wiedza o społeczeństwie"] = st.selectbox("Wiedza o społeczeństwie (WOS)", grade_list, index=2)
        user_grades["Wychowanie fizyczne"] = st.selectbox("Wychowanie fizyczne (WF)", grade_list, index=1)
        user_grades["Muzyka"] = st.selectbox("Muzyka", grade_list, index=1)
        user_grades["Plastyka"] = st.selectbox("Plastyka", grade_list, index=1)
        user_grades["Edukacja dla bezpieczeństwa"] = st.selectbox("Edukacja dla bezpieczeństwa (EDB)", grade_list,
                                                                  index=1)

    # Zapis stanu w sesji
    st.session_state['exam_pts'] = exam_pts
    st.session_state['achieve_pts'] = achieve_pts
    st.session_state['user_grades'] = user_grades

    # Przykładowy ogólny wynik bazowy (dla 2 najlepszych ocen w ogóle)
    base_score, base_subs = calculate_class_score(user_grades, exam_pts, achieve_pts, {"extensions": []})
    st.success(f"### Twój szacowany wynik bazowy: **{base_score:.2f} / 200 pkt**")
    st.caption(
        f"*Obliczono dla języka polskiego, matematyki oraz dwóch najwyżej punktowanych przedmiotów: {', '.join(base_subs)}.")

# -----------------------------------------------------------------------------
# ZAKŁADKA 2: WYSZUKIWARKA SZKÓŁ
# -----------------------------------------------------------------------------
with tab2:
    st.header("Krok 2: Wybierz preferowane szkoły i przedmioty")

    col_f1, col_f2, col_f3 = st.columns([2, 1, 2])

    with col_f1:
        search_query = st.text_input("Szukaj po nazwie szkoły:", placeholder="np. I Liceum")

    with col_f2:
        school_type = st.selectbox("Typ szkoły:", ["wszystkie", "liceum", "technikum", "branzowa"])

    with col_f3:
        all_exts = school_service.get_all_available_extensions()
        selected_exts = st.multiselect(
            "Interesujące Cię rozszerzenia:",
            options=all_exts,
            placeholder="Wybierz z listy..."
        )

    matched_schools = school_service.get_schools_in_krakow(
        stype=school_type,
        search_query=search_query,
        required_extensions=selected_exts if selected_exts else None
    )
    st.session_state['matched_schools'] = matched_schools

    st.subheader(f"Znaleziono szkół spełniających kryteria: {len(matched_schools)}")

    grades = st.session_state.get('user_grades', {})
    ex_pts = st.session_state.get('exam_pts', 0.0)
    ac_pts = st.session_state.get('achieve_pts', 0.0)

    for school in matched_schools:
        with st.expander(f"🏫 **{school['name']}** ({school.get('type', '').capitalize()})"):
            for cls in school.get("classes", []):
                ext_str = ", ".join(cls.get("extensions", []))
                cutoff = cls.get("historical_cutoffs", {}).get("2026/2027", "Brak")

                # Wyliczenie punktów dedykowanych dokładnie pod tę klasę
                cls_score, cls_subs = calculate_class_score(grades, ex_pts, ac_pts, cls)

                st.write(
                    f"• **Klasa {cls['class_id']}** ({cls['profile']}) | Rozszerzenia: *{ext_str}* | "
                    f"Próg: **{cutoff} pkt** | Twój wynik do tej klasy: **{cls_score:.2f} pkt** "
                    f"*(punktowane: Pol, Mat, {', '.join(cls_subs)})*"
                )

# -----------------------------------------------------------------------------
# ZAKŁADKA 3: RAPORT PODSUMOWUJĄCY
# -----------------------------------------------------------------------------
with tab3:
    st.header("Krok 3: Raport szans rekrutacyjnych")

    grades = st.session_state.get('user_grades', {})
    ex_pts = st.session_state.get('exam_pts', 0.0)
    ac_pts = st.session_state.get('achieve_pts', 0.0)
    matched_schools = st.session_state.get('matched_schools', [])

    if not matched_schools or not grades:
        st.warning("Brak danych. Wypełnij najpierw kalkulator w KROKU 1 i wybierz filtry w KROKU 2.")
    else:
        report_data = []
        for school in matched_schools:
            for cls in school.get("classes", []):
                cls_score, cls_subs = calculate_class_score(grades, ex_pts, ac_pts, cls)

                cutoffs = cls.get("historical_cutoffs", {})
                assessment_res = prob_service.assess_chance(cls_score, cutoffs)

                latest_cutoff = assessment_res.get('latest_cutoff', 0.0)
                diff = cls_score - latest_cutoff if latest_cutoff else 0.0

                if diff >= 5.0:
                    status = "🟢 Bardzo wysoka"
                elif diff >= -5.0:
                    status = "🟡 Umiarkowana"
                else:
                    status = "🔴 Niska / Ryzykowna"

                report_data.append({
                    "Szkoła": school["name"],
                    "Klasa / Profil": f"Klasa {cls['class_id']} ({cls['profile']})",
                    "Punktowane przedmioty": f"Pol, Mat + {', '.join(cls_subs)}",
                    "Twój wynik": f"{cls_score:.2f} pkt",
                    "Próg 2026": f"{latest_cutoff} pkt",
                    "Różnica": f"{diff:+.2f} pkt",
                    "Ocena szans": status
                })

        st.dataframe(report_data, use_container_width=True)
