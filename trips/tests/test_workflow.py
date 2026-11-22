import pytest
from services.destination_service import filter_destinations, parse_grade
from graph.nodes import validate_details, evaluate_options, collect_details


class TestParseGrade:
    def test_hebrew_letters(self):
        assert parse_grade("א") == 1
        assert parse_grade("ד") == 4
        assert parse_grade("יב") == 12

    def test_numeric(self):
        assert parse_grade("6") == 6
        assert parse_grade("12") == 12

    def test_unknown(self):
        assert parse_grade("xyz") == 0


class TestFilterDestinations:
    def test_filter_by_region(self):
        results = filter_destinations(grade="ד", region="צפון", budget=200)
        assert all(d["region"] == "צפון" for d in results)

    def test_filter_by_budget(self):
        results = filter_destinations(grade="ד", region="כל הארץ", budget=40)
        assert all(d["estimated_cost"] <= 40 for d in results)

    def test_filter_by_grade(self):
        results = filter_destinations(grade="א", region="כל הארץ", budget=200)
        assert all(d["min_grade"] <= 1 <= d["max_grade"] for d in results)

    def test_no_results_strict_budget(self):
        results = filter_destinations(grade="ו", region="ירושלים", budget=5)
        assert results == []

    def test_all_country(self):
        results = filter_destinations(grade="ו", region="כל הארץ", budget=200)
        assert len(results) > 0

    def test_interest_sorting(self):
        results = filter_destinations(
            grade="ד", region="כל הארץ", budget=200, interests=["מדע", "חינוך"]
        )
        if len(results) >= 2:
            first_cats = set(results[0].get("categories", []))
            assert first_cats & {"מדע", "חינוך"}


class TestValidateDetails:
    def test_complete(self):
        state = {
            "grade": "ד",
            "students_count": 30,
            "budget_per_student": 100,
            "region": "צפון",
            "duration": "יום שלם",
        }
        result = validate_details(state)
        assert result["missing_details"] == []

    def test_missing_fields(self):
        state = {
            "grade": "ד",
            "students_count": 0,
            "budget_per_student": 100,
            "region": "",
            "duration": "יום שלם",
        }
        result = validate_details(state)
        fields = [m["field"] for m in result["missing_details"]]
        assert "students_count" in fields
        assert "region" in fields

    def test_all_missing(self):
        result = validate_details({})
        assert len(result["missing_details"]) == 5


class TestEvaluateOptions:
    def test_empty_candidates(self):
        result = evaluate_options({"candidate_destinations": []})
        assert result["selected_destinations"] == []

    def test_selects_top_five(self):
        candidates = [{"id": i, "name": f"dest_{i}", "categories": ["טבע"],
                        "estimated_cost": 50} for i in range(10)]
        state = {
            "candidate_destinations": candidates,
            "interests": ["טבע"],
            "budget_per_student": 100,
        }
        result = evaluate_options(state)
        assert len(result["selected_destinations"]) == 5

    def test_scoring_prefers_interest_match(self):
        candidates = [
            {"id": 1, "name": "a", "categories": ["מדע", "חינוך"], "estimated_cost": 50},
            {"id": 2, "name": "b", "categories": ["ספורט"], "estimated_cost": 50},
        ]
        state = {
            "candidate_destinations": candidates,
            "interests": ["מדע", "חינוך"],
            "budget_per_student": 100,
        }
        result = evaluate_options(state)
        assert result["selected_destinations"][0]["id"] == 1


class TestCollectDetails:
    def test_defaults(self):
        result = collect_details({})
        assert result["missing_details"] == []
        assert result["candidate_destinations"] == []
        assert result["itinerary"] == ""
