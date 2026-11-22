from typing import TypedDict


class TripState(TypedDict, total=False):
    grade: str
    students_count: int
    budget_per_student: float
    region: str
    duration: str
    interests: list[str]
    constraints: str
    missing_details: list[dict]
    candidate_destinations: list[dict]
    selected_destinations: list[dict]
    itinerary: str
    teacher_feedback: str
    approval_status: str
