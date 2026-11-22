from langchain_core.tools import tool
from services.destination_service import filter_destinations


@tool
def search_destinations(
    grade: str, region: str, budget: float, interests: list[str] = None
) -> list[dict]:
    """חיפוש יעדים לטיולי בתי ספר לפי כיתה, אזור, תקציב ותחומי עניין."""
    return filter_destinations(
        grade=grade, region=region, budget=budget, interests=interests
    )
