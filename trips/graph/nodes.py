from langgraph.types import interrupt
from services.destination_service import filter_destinations
from services.itinerary_service import generate_trip_itinerary, revise_trip_itinerary


def collect_details(state: dict) -> dict:
    """קבלת פרטי הטיול - אתחול שדות ברירת מחדל."""
    return {
        "missing_details": state.get("missing_details", []),
        "candidate_destinations": state.get("candidate_destinations", []),
        "selected_destinations": state.get("selected_destinations", []),
        "itinerary": state.get("itinerary", ""),
        "teacher_feedback": state.get("teacher_feedback", ""),
        "approval_status": state.get("approval_status", ""),
    }


def validate_details(state: dict) -> dict:
    """בדיקת שלמות הנתונים - זיהוי שדות חסרים."""
    required = {
        "grade": "כיתה",
        "students_count": "מספר תלמידים",
        "budget_per_student": "תקציב לתלמיד",
        "region": "אזור",
        "duration": "משך הטיול",
    }
    missing = []
    for field, label in required.items():
        value = state.get(field)
        if value is None or value == "" or value == 0:
            missing.append({"field": field, "label": label})
    return {"missing_details": missing}


def ask_clarification(state: dict) -> dict:
    """שאלת הבהרה - עצירה לקבלת מידע חסר מהמורה."""
    missing = state.get("missing_details", [])
    questions = [
        {"field": m["field"], "question": f"אנא הזן: {m['label']}"}
        for m in missing
    ]
    answers = interrupt({"questions": questions})
    result = dict(answers)
    result["missing_details"] = []
    return result


def find_destinations(state: dict) -> dict:
    """חיפוש יעדים מתוך מאגר הנתונים המקומי."""
    candidates = filter_destinations(
        grade=state.get("grade", ""),
        region=state.get("region", ""),
        budget=state.get("budget_per_student", 0),
        interests=state.get("interests", []),
    )
    return {"candidate_destinations": candidates}


def evaluate_options(state: dict) -> dict:
    """הערכת ודירוג יעדים לפי התאמה."""
    candidates = state.get("candidate_destinations", [])
    if not candidates:
        return {"selected_destinations": []}

    interests = state.get("interests", [])
    budget = state.get("budget_per_student", 0)

    scored = []
    for dest in candidates:
        score = 0
        if interests:
            matches = len(set(dest.get("categories", [])) & set(interests))
            score += matches * 10
        if budget > 0:
            cost_ratio = dest.get("estimated_cost", 0) / budget
            score += max(0, (1 - cost_ratio)) * 5
        scored.append({**dest, "score": round(score, 2)})

    scored.sort(key=lambda x: x["score"], reverse=True)
    return {"selected_destinations": scored[:5]}


def generate_itinerary(state: dict) -> dict:
    """יצירת מסלול טיול מפורט בעזרת GPT."""
    itinerary = generate_trip_itinerary(
        grade=state.get("grade", ""),
        students_count=state.get("students_count", 0),
        budget_per_student=state.get("budget_per_student", 0),
        region=state.get("region", ""),
        duration=state.get("duration", ""),
        interests=state.get("interests", []),
        constraints=state.get("constraints", ""),
        destinations=state.get("selected_destinations", []),
    )
    return {"itinerary": itinerary}


def teacher_review(state: dict) -> dict:
    """עצירה לקבלת אישור מהמורה - Human in the Loop."""
    review = interrupt({
        "type": "teacher_review",
        "itinerary": state.get("itinerary", ""),
    })
    return {
        "teacher_feedback": review.get("feedback", ""),
        "approval_status": "approved" if review.get("approved") else "revision_needed",
    }


def revise_plan(state: dict) -> dict:
    """עדכון המסלול לפי משוב המורה."""
    revised = revise_trip_itinerary(
        current_itinerary=state.get("itinerary", ""),
        feedback=state.get("teacher_feedback", ""),
        destinations=state.get("selected_destinations", []),
        grade=state.get("grade", ""),
        budget_per_student=state.get("budget_per_student", 0),
    )
    return {"itinerary": revised}


def finalize_trip(state: dict) -> dict:
    """הצגת התוכנית הסופית."""
    return {"approval_status": "final"}
