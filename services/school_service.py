import json
import re


class SchoolService:
    def __init__(self, json_path="data/schools.json"):
        self.json_path = json_path

        # Słownik do ujednolicania nazw przedmiotów (synonimy i skróty)
        self.SUBJECT_MAPPING = {
            "j. polski": "Język polski",
            "j.polski": "Język polski",
            "język polski": "Język polski",
            "polski": "Język polski",

            "j. angielski": "Język angielski",
            "j.angielski": "Język angielski",
            "język angielski": "Język angielski",
            "angielski": "Język angielski",

            "j. niemiecki": "Język niemiecki",
            "j.niemiecki": "Język niemiecki",
            "język niemiecki": "Język niemiecki",
            "niemiecki": "Język niemiecki",

            "j. hiszpański": "Język hiszpański",
            "j.hiszpański": "Język hiszpański",
            "język hiszpański": "Język hiszpański",

            "j. francuski": "Język francuski",
            "j.francuski": "Język francuski",
            "język francuski": "Język francuski",

            "j. rosyjski": "Język rosyjski",
            "j.rosyjski": "Język rosyjski",
            "język rosyjski": "Język rosyjski",

            "j. włoski": "Język włoski",
            "j. łaciński": "Język łaciński",

            "matematyka": "Matematyka",
            "matem.": "Matematyka",

            "fizyka": "Fizyka",
            "fiz.": "Fizyka",

            "chemia": "Chemia",
            "chem.": "Chemia",

            "biologia": "Biologia",
            "biol.": "Biologia",

            "geografia": "Geografia",
            "geogr.": "Geografia",

            "historia": "Historia",
            "hist.": "Historia",

            "informatyka": "Informatyka",
            "inf.": "Informatyka",

            "wos": "Wiedza o społeczeństwie",
            "w.o.s.": "Wiedza o społeczeństwie",
            "wiedza o społeczeństwie": "Wiedza o społeczeństwie",

            "historia i teraźniejszość": "Historia i teraźniejszość",
            "hit": "Historia i teraźniejszość"
        }

    def _normalize_subject(self, subject_name: str) -> str:
        """Przekształca skróty i różne warianty pisowni w jedną standardową nazwę."""
        if not subject_name:
            return ""
        clean = subject_name.strip().lower()
        return self.SUBJECT_MAPPING.get(clean, subject_name.strip().capitalize())

    def _extract_individual_subjects(self, ext_input) -> list:
        """Dzieli ciągi znaków zawierające 'lub', '/', 'oraz' na pojedyncze znormalizowane przedmioty."""
        if isinstance(ext_input, str):
            ext_list = [ext_input]
        else:
            ext_list = ext_input or []

        clean_subjects = []
        for item in ext_list:
            if not item:
                continue

            # Zamiana separatorów i spójników na przecinki (z pominięciem zwrotu 'historia i teraźniejszość')
            text = str(item)
            text = re.sub(r'\s+(lub|oraz|i/lub)\s+', ',', text, flags=re.IGNORECASE)
            text = text.replace('/', ',').replace(';', ',')

            parts = text.split(',')
            for part in parts:
                norm = self._normalize_subject(part)
                if norm and norm not in clean_subjects:
                    clean_subjects.append(norm)

        return clean_subjects

    def _roman_to_int(self, roman_str):
        roman_dict = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
        total = 0
        prev_value = 0
        for char in reversed(roman_str.upper()):
            val = roman_dict.get(char, 0)
            if val < prev_value:
                total -= val
            else:
                total += val
                prev_value = val
        return total if total > 0 else 999

    def _extract_number(self, school_name):
        match = re.search(r'^\s*([IVXLCDM]+)\s+', school_name)
        if match:
            return self._roman_to_int(match.group(1))
        return 999

    def get_all_available_extensions(self):
        """Pobiera uporządkowaną listę unikalnych, pojedynczych przedmiotów rozszerzonych."""
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            return []

        extensions_set = set()
        for school in data:
            for cls in school.get("classes", []):
                # Rozbijamy połączone wpisy (np. 'fizyka lub informatyka') na osobne pozycje
                extracted_subjects = self._extract_individual_subjects(cls.get("extensions", []))
                for sub in extracted_subjects:
                    extensions_set.add(sub)

        return sorted(list(extensions_set))

    def get_schools_in_krakow(self, stype="wszystkie", search_query="", required_extensions=None):
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            return []

        filtered_schools = []

        # Normalizujemy szukany przedmiot
        req_ext_normalized = [self._normalize_subject(e) for e in required_extensions] if required_extensions else []

        for school in data:
            if stype != "wszystkie" and school.get("type") != stype:
                continue

            if search_query and search_query.lower() not in school.get("name", "").lower():
                continue

            matching_classes = []
            for cls in school.get("classes", []):
                # Ekstrahujemy i normalizujemy wszystkie przedmioty dostępne w danej klasie
                cls_extensions_norm = self._extract_individual_subjects(cls.get("extensions", []))

                # Porównujemy wymagane rozszerzenie z rozbitymi przedmiotami klasy
                if all(req in cls_extensions_norm for req in req_ext_normalized):
                    matching_classes.append(cls)

            if matching_classes:
                school_copy = dict(school)
                school_copy["classes"] = matching_classes
                filtered_schools.append(school_copy)
            elif not req_ext_normalized:
                filtered_schools.append(school)

        filtered_schools.sort(key=lambda x: self._extract_number(x.get("name", "")))
        return filtered_schools

    def get_class_details(self, school_id, class_id):
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for school in data:
                if school.get("id") == school_id:
                    for cls in school.get("classes", []):
                        if cls.get("class_id") == class_id:
                            return school, cls
        except Exception:
            pass
        return None, None