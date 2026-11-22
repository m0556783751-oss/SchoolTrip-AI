import json
import os
from services.destination_service import parse_grade


def budget_evaluator(run, example) -> dict:
    """בדיקת התאמה לתקציב."""
    output = run.outputs or {}
    destinations = output.get("selected_destinations", [])
    budget = example.inputs.get("budget_per_student", 0)

    if not destinations:
        return {"key": "budget_match", "score": 1.0}

    all_within = all(d.get("estimated_cost", 0) <= budget for d in destinations)
    return {"key": "budget_match", "score": 1.0 if all_within else 0.0}


def age_evaluator(run, example) -> dict:
    """בדיקת התאמה לגיל."""
    output = run.outputs or {}
    destinations = output.get("selected_destinations", [])
    grade = parse_grade(str(example.inputs.get("grade", "")))

    if not destinations or not grade:
        return {"key": "age_appropriate", "score": 1.0}

    all_ok = all(
        d.get("min_grade", 0) <= grade <= d.get("max_grade", 12)
        for d in destinations
    )
    return {"key": "age_appropriate", "score": 1.0 if all_ok else 0.0}


def region_evaluator(run, example) -> dict:
    """בדיקת התאמה לאזור."""
    output = run.outputs or {}
    destinations = output.get("selected_destinations", [])
    region = example.inputs.get("region", "")

    if not destinations or not region or region == "כל הארץ":
        return {"key": "region_match", "score": 1.0}

    all_match = all(d.get("region", "") == region for d in destinations)
    return {"key": "region_match", "score": 1.0 if all_match else 0.0}


def missing_details_evaluator(run, example) -> dict:
    """בדיקת זיהוי מידע חסר."""
    output = run.outputs or {}
    missing = output.get("missing_details", [])
    expected_missing = example.outputs.get("has_missing_details", False)

    if expected_missing:
        score = 1.0 if len(missing) > 0 else 0.0
    else:
        score = 1.0 if len(missing) == 0 else 0.0
    return {"key": "missing_detection", "score": score}


def structure_evaluator(run, example) -> dict:
    """בדיקת תקינות מבנה תשובה."""
    output = run.outputs or {}
    itinerary = output.get("itinerary", "")

    if not itinerary:
        has_missing = example.outputs.get("has_missing_details", False)
        no_dest = not example.outputs.get("has_destinations", True)
        if has_missing or no_dest:
            return {"key": "structure", "score": 1.0}
        return {"key": "structure", "score": 0.0}

    return {"key": "structure", "score": 1.0 if len(itinerary) > 100 else 0.0}


def run_experiment(experiment_name: str = "schooltrip-v1"):
    """הרצת ניסוי הערכה ב-LangSmith."""
    from langsmith import Client
    from langsmith.evaluation import evaluate
    from langgraph.checkpoint.memory import MemorySaver
    from graph.workflow import build_graph
    from uuid import uuid4

    client = Client()

    dataset_path = os.path.join(os.path.dirname(__file__), "dataset.json")
    with open(dataset_path, "r", encoding="utf-8") as f:
        test_cases = json.load(f)

    dataset_name = "SchoolTripAI"
    try:
        dataset = client.create_dataset(dataset_name)
    except Exception:
        datasets = list(client.list_datasets(dataset_name=dataset_name))
        dataset = datasets[0] if datasets else client.create_dataset(dataset_name)

    for case in test_cases:
        try:
            client.create_example(
                inputs=case["input"],
                outputs=case["expected"],
                dataset_id=dataset.id,
            )
        except Exception:
            pass

    def predict(inputs: dict) -> dict:
        g = build_graph(MemorySaver())
        cfg = {"configurable": {"thread_id": str(uuid4())}}
        g.invoke(inputs, cfg)
        snapshot = g.get_state(cfg)
        return dict(snapshot.values)

    results = evaluate(
        predict,
        data=dataset_name,
        evaluators=[
            budget_evaluator,
            age_evaluator,
            region_evaluator,
            missing_details_evaluator,
            structure_evaluator,
        ],
        experiment_prefix=experiment_name,
    )
    return results


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    results = run_experiment()
    print("Evaluation complete!")
