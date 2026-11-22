import json
import os

GRADE_MAP = {
    "א": 1, "ב": 2, "ג": 3, "ד": 4, "ה": 5, "ו": 6,
    "ז": 7, "ח": 8, "ט": 9, "י": 10, "יא": 11, "יב": 12,
}


def parse_grade(grade_str: str) -> int:
    grade_str = grade_str.strip().replace("׳", "").replace("'", "")
    if grade_str.isdigit():
        return int(grade_str)
    return GRADE_MAP.get(grade_str, 0)


def load_destinations() -> list[dict]:
    data_path = os.path.join(
        os.path.dirname(__file__), "..", "data", "destinations.json"
    )
    with open(data_path, "r", encoding="utf-8") as f:
        return json.load(f)


def filter_destinations(
    grade: str,
    region: str,
    budget: float,
    interests: list[str] = None,
) -> list[dict]:
    destinations = load_destinations()
    grade_num = parse_grade(str(grade))

    filtered = []
    for dest in destinations:
        if grade_num and (
            grade_num < dest["min_grade"] or grade_num > dest["max_grade"]
        ):
            continue
        if region and region != "כל הארץ" and dest["region"] != region:
            continue
        if budget and dest["estimated_cost"] > budget:
            continue
        filtered.append(dest)

    if interests:
        filtered.sort(
            key=lambda d: len(set(d.get("categories", [])) & set(interests)),
            reverse=True,
        )

    return filtered
