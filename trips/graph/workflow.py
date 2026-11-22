from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from graph.state import TripState
from graph.nodes import (
    collect_details,
    validate_details,
    ask_clarification,
    find_destinations,
    evaluate_options,
    generate_itinerary,
    teacher_review,
    revise_plan,
    finalize_trip,
)
from graph.edges import (
    route_after_validation,
    route_after_evaluation,
    route_after_review,
)


def build_graph(checkpointer=None):
    if checkpointer is None:
        checkpointer = MemorySaver()

    builder = StateGraph(TripState)

    # --- Nodes ---
    builder.add_node("collect_details", collect_details)
    builder.add_node("validate_details", validate_details)
    builder.add_node("ask_clarification", ask_clarification)
    builder.add_node("find_destinations", find_destinations)
    builder.add_node("evaluate_options", evaluate_options)
    builder.add_node("generate_itinerary", generate_itinerary)
    builder.add_node("teacher_review", teacher_review)
    builder.add_node("revise_plan", revise_plan)
    builder.add_node("finalize_trip", finalize_trip)

    # --- Edges ---
    builder.add_edge(START, "collect_details")
    builder.add_edge("collect_details", "validate_details")

    # Conditional: validation → clarification loop or find destinations
    builder.add_conditional_edges("validate_details", route_after_validation)

    # Loop: clarification → collect_details → validate_details
    builder.add_edge("ask_clarification", "collect_details")

    builder.add_edge("find_destinations", "evaluate_options")

    # Conditional: no destinations → finalize, otherwise → generate
    builder.add_conditional_edges("evaluate_options", route_after_evaluation)

    builder.add_edge("generate_itinerary", "teacher_review")

    # Conditional: approved → finalize, otherwise → revise
    builder.add_conditional_edges("teacher_review", route_after_review)

    # Loop: revise → teacher_review
    builder.add_edge("revise_plan", "teacher_review")

    builder.add_edge("finalize_trip", END)

    return builder.compile(checkpointer=checkpointer)
