"""
state.py
--------
Defines the shared state object that flows through every node in the LangGraph
pipeline. Each node receives the full state and returns a dict of the keys it
wants to update — LangGraph merges those updates in automatically.
"""

from typing import Any, Dict, Optional
from typing_extensions import TypedDict


class GraphState(TypedDict):
    """
    The single data structure shared across all pipeline nodes.

    Fields
    ------
    raw_text    : The original deviation text supplied by the user (paste or PDF).
    extracted   : Dict populated by the 'extract' node with structured deviation fields.
    assessment  : Dict populated by the 'assess' node with impact/severity data.
    error       : Set by any node that encounters a recoverable error.
                  Downstream nodes should check this and skip processing if set.
    """
    raw_text: str
    extracted: Optional[Dict[str, Any]]
    assessment: Optional[Dict[str, Any]]
    error: Optional[str]
