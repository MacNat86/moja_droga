import json
from pathlib import Path


class CalculatorService:
    def __init__(self):
        config_path = Path(__file__).parent.parent / "data" / "recruitment_data.json"
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = json.load(f)

    def calculate_exam_points(self, polish_pct: float, math_pct: float, foreign_pct: float) -> dict:
        weights = self.config["exam_weights"]
        p_pts = polish_pct * weights["polish"]
        m_pts = math_pct * weights["mathematics"]
        f_pts = foreign_pct * weights["foreign_language"]
        total = round(p_pts + m_pts + f_pts, 2)
        return {
            "polish": round(p_pts, 2),
            "math": round(m_pts, 2),
            "foreign": round(f_pts, 2),
            "total": total
        }

    def calculate_grades_points(self, grades_dict: dict, scored_subjects: list = None) -> float:
        grade_points_map = self.config["grade_points"]
        total_grades = 0.0

        if scored_subjects:
            for subj in scored_subjects:
                grade = grades_dict.get(subj, 5)  # Domyślnie 5 jeśli brak
                total_grades += grade_points_map.get(str(grade), 17)
        else:
            # Ogólna prognoza 4 przedmiotów (np. pol, mat, obcy, dodatkowy)
            for subj, grade in list(grades_dict.items())[:4]:
                total_grades += grade_points_map.get(str(grade), 17)

        return min(float(total_grades), 72.0)

    def calculate_total_points(self, exam_data: dict, grades_pts: float, honors: bool, volunteering: bool,
                               achievement_key: str) -> dict:
        add_cfg = self.config["additional_points"]
        honors_pts = add_cfg["honors_strip"] if honors else 0
        vol_pts = add_cfg["volunteering"] if volunteering else 0
        ach_pts = add_cfg["achievements"].get(achievement_key, 0)

        exam_total = exam_data["total"]
        overall = round(exam_total + grades_pts + honors_pts + vol_pts + ach_pts, 2)

        return {
            "exam_total": exam_total,
            "grades_pts": grades_pts,
            "honors_pts": honors_pts,
            "vol_pts": vol_pts,
            "ach_pts": ach_pts,
            "overall": overall
        }