class ProbabilityService:
    @staticmethod
    def assess_chance(user_base_points: float, historical_cutoffs: dict) -> dict:
        if not historical_cutoffs:
            return {
                "latest_year": "Brak",
                "latest_cutoff": 0.0,
                "school_max": 0.0,
                "assessment": "Brak historycznych progów. Ocena szans jest niemożliwa.",
                "scenarios": {}
            }

        sorted_years = sorted(historical_cutoffs.keys())
        latest_year = sorted_years[-1]
        latest_cutoff = historical_cutoffs[latest_year]
        max_cutoff = max(historical_cutoffs.values())

        safe_margin = max_cutoff + 3.0

        # Wyliczanie 3 scenariuszy dla ucznia przed egzaminami
        # Zakładamy asymetryczny błąd: łatwiej stracić punkty na stresie niż nagle napisać dużo lepiej
        scenarios = {
            "pesymistyczny": max(0.0, round(user_base_points - 15.0, 1)),
            "realistyczny": round(user_base_points, 1),
            "optymistyczny": min(200.0, round(user_base_points + 10.0, 1))
        }

        # Ocena każdego scenariusza względem progu
        scenario_assessments = {}
        for name, points in scenarios.items():
            if points >= safe_margin:
                scenario_assessments[name] = ("Wysokie szanse", "#27ae60")  # Zielony
            elif points >= max_cutoff - 5.0:
                scenario_assessments[name] = ("Strefa ryzyka / Na styk", "#e67e22")  # Pomarańczowy
            else:
                scenario_assessments[name] = ("Niskie szanse", "#c0392b")  # Czerwony

        # Ogólny werdykt bazujący na scenariuszu realistycznym
        if scenario_assessments["realistyczny"][0] == "Wysokie szanse":
            general_assessment = "Przy obecnych szacunkach to bezpieczny wybór. Nawet w scenariuszu pesymistycznym zachowujesz szanse."
        elif scenario_assessments["realistyczny"][0] == "Strefa ryzyka / Na styk":
            general_assessment = "Jesteś na granicy progu. O przyjęciu zadecyduje dyspozycja w dniu egzaminu lub to, czy uda Ci się podciągnąć oceny."
        else:
            general_assessment = "Przy Twoich szacunkach to klasa 'marzeń'. Aby się dostać, musisz zrealizować scenariusz wysoce optymistyczny."

        return {
            "latest_year": latest_year,
            "latest_cutoff": latest_cutoff,
            "school_max": max_cutoff,
            "scenarios": scenarios,
            "scenario_assessments": scenario_assessments,
            "assessment": general_assessment,
            "all_cutoffs": historical_cutoffs
        }