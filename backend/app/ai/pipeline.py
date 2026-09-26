"""
pipeline.py
-----------
Assembles the LangGraph StateGraph from the two node functions.

Graph topology (linear):
    START → extract_node → assess_node → END

The compiled graph exposes a single method: graph.invoke({"raw_text": "..."})
which runs both nodes synchronously and returns the final GraphState.

This module is the only import needed by the FastAPI endpoint in Phase 3.
"""

from langgraph.graph import StateGraph, END

from app.ai.state import GraphState
from app.ai.nodes import extract_node, assess_node

# ── Build the graph ────────────────────────────────────────────────────────────

def build_pipeline():
    """
    Constructs and compiles the LangGraph deviation intake pipeline.
    Returns a compiled graph ready to call with .invoke().
    """
    builder = StateGraph(GraphState)

    # Register nodes
    builder.add_node("extract", extract_node)
    builder.add_node("assess", assess_node)

    # Wire edges: START → extract → assess → END
    builder.set_entry_point("extract")
    builder.add_edge("extract", "assess")
    builder.add_edge("assess", END)

    return builder.compile()


# ── Singleton compiled graph ───────────────────────────────────────────────────
# Compiled once at import time and reused across all requests.
# This avoids re-compiling the graph on every API call.
deviation_pipeline = build_pipeline()


def run_pipeline(raw_text: str) -> GraphState:
    """
    Public entry point used by FastAPI in Phase 3.

    Parameters
    ----------
    raw_text : str
        The raw deviation text (from a paste or PDF extraction).

    Returns
    -------
    GraphState
        The final state after both nodes have run, containing:
        - state["extracted"]   → dict of structured deviation fields
        - state["assessment"]  → dict with impact, severity, reason, confidence
        - state["error"]       → None on success, error message string on failure
    """
    initial_state: GraphState = {
        "raw_text": raw_text,
        "extracted": None,
        "assessment": None,
        "error": None,
    }
    return deviation_pipeline.invoke(initial_state)
