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

from app.ai.state import GraphState, EditGraphState
from app.ai.nodes import extract_node, assess_node, edit_node

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


def run_edit_interaction(message: str, current_state: dict) -> EditGraphState:
    """
    Public entry point for the edit interaction tool (Phase 4).
    
    Parameters
    ----------
    message : str
        The user's natural language correction.
    current_state : dict
        The current form state (ExtractedDeviation + AssessedDeviation).
        
    Returns
    -------
    EditGraphState
        State containing updated 'extracted'/'assessment', 'edit_reply', 'fields_changed',
        and potentially regenerated risk fields if 'risk_relevant' was true.
    """
    state: EditGraphState = {
        "edit_message": message,
        "current_state": current_state,
        "extracted": None,
        "assessment": None,
        "edit_reply": None,
        "fields_changed": None,
        "risk_relevant": None,
        "error": None
    }
    
    # 1. Parse the edit
    edit_result = edit_node(state)
    state.update(edit_result)
    
    if state.get("error"):
        return state
        
    # 2. Optionally re-run assessment if the edit was risk-relevant
    # 'edit_node' has populated 'extracted' with the newly merged state,
    # which is exactly what 'assess_node' reads to do its job.
    if state.get("risk_relevant") and state.get("fields_changed"):
        # We can pass `state` directly into assess_node because it expects a dict-like
        # object containing an "extracted" key and an "error" key, both of which EditGraphState provides.
        assess_result = assess_node(state)  # type: ignore
        if not assess_result.get("error") and assess_result.get("assessment"):
            state["assessment"] = assess_result["assessment"]
            
            # The edit_node might not have appended the recalculation confirmation,
            # or it might have. We'll leave the LLM's generated reply intact as instructed
            # in the prompt to append "and I will recalculate...".
            
    # 3. Final diff calculation: compute exactly which fields differ between current_state and final updated state
    final_merged = {**(state.get("extracted") or {}), **(state.get("assessment") or {})}
    computed_fields_changed = []
    for k, v in final_merged.items():
        if current_state.get(k) != v:
            computed_fields_changed.append(k)
            
    state["fields_changed"] = computed_fields_changed
    
    return state
