from ai.models import get_llm
from ai.prompts import ITINERARY_PROMPT, REVISION_PROMPT
from langchain_core.prompts import ChatPromptTemplate


def _format_destinations(destinations: list[dict]) -> str:
    lines = []
    for d in destinations:
        lines.append(
            f"- {d['name']}: {d['description']} "
            f"(עלות: ₪{d['estimated_cost']}, משך: {d['duration_hours']} שעות)"
        )
    return "\n".join(lines) if lines else "אין יעדים זמינים"


def generate_trip_itinerary(
    grade: str,
    students_count: int,
    budget_per_student: float,
    region: str,
    duration: str,
    interests: list[str],
    constraints: str,
    destinations: list[dict],
) -> str:
    llm = get_llm()
    prompt = ChatPromptTemplate.from_template(ITINERARY_PROMPT)
    chain = prompt | llm

    result = chain.invoke(
        {
            "grade": grade,
            "students_count": students_count,
            "budget_per_student": budget_per_student,
            "region": region,
            "duration": duration,
            "interests": ", ".join(interests) if interests else "לא צוין",
            "constraints": constraints or "אין",
            "destinations": _format_destinations(destinations),
        }
    )
    return result.content


def revise_trip_itinerary(
    current_itinerary: str,
    feedback: str,
    destinations: list[dict],
    grade: str,
    budget_per_student: float,
) -> str:
    llm = get_llm()
    prompt = ChatPromptTemplate.from_template(REVISION_PROMPT)
    chain = prompt | llm

    result = chain.invoke(
        {
            "current_itinerary": current_itinerary,
            "feedback": feedback,
            "destinations": _format_destinations(destinations),
            "grade": grade,
            "budget_per_student": budget_per_student,
        }
    )
    return result.content
