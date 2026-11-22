def route_after_validation(state: dict) -> str:
    """ניתוב מותנה: אם חסר מידע - שאלת הבהרה, אחרת - חיפוש יעדים."""
    if state.get("missing_details"):
        return "ask_clarification"
    return "find_destinations"


def route_after_evaluation(state: dict) -> str:
    """ניתוב מותנה: אם אין יעדים מתאימים - סיום, אחרת - יצירת מסלול."""
    if not state.get("selected_destinations"):
        return "finalize_trip"
    return "generate_itinerary"


def route_after_review(state: dict) -> str:
    """ניתוב מותנה: אם אושר - סיום, אחרת - שינויים."""
    if state.get("approval_status") == "approved":
        return "finalize_trip"
    return "revise_plan"
