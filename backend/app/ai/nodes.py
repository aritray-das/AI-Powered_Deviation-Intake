"""
nodes.py
--------
The two LangGraph node functions: extract_node and assess_node.

Each function:
  - Receives the full GraphState
  - Does one focused job using the LLM
  - Returns a dict of only the keys it updates (LangGraph merges these in)

Both nodes use `with_structured_output()` to enforce a Pydantic schema on the
LLM response, which gives us reliable, type-safe JSON without manual parsing.
"""

import json
from typing import Literal, Optional

from langchain_groq import ChatGroq
from pydantic import BaseModel, Field

from app.config import settings
from app.ai.state import GraphState
from app.ai.prompts import extract_prompt, assess_prompt


# ── Shared LLM instance ────────────────────────────────────────────────────────
# temperature=0 → deterministic output, which is what we want for structured
# data extraction in a regulated-industry QA context.
# NOTE: llama-3.3-70b-versatile is not available on this Groq account.
# Using openai/gpt-oss-120b (largest available model) as a replacement.
# To switch models, change the string below only.
_llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0,
    api_key=settings.GROQ_API_KEY,
)


# ── Pydantic output schemas (used with with_structured_output) ─────────────────

class ExtractedDeviation(BaseModel):
    """Structured deviation fields extracted from raw text by Node 1."""
    title: Optional[str] = Field(None, description="Concise 5-10 word summary of the deviation type")
    description: Optional[str] = Field(None, description="Full description of what happened")
    department: Optional[str] = Field(None, description="Department or unit where the deviation occurred")
    product_name: Optional[str] = Field(None, description="Name of the product being manufactured")
    batch_number: Optional[str] = Field(None, description="Batch or lot number")
    equipment_id: Optional[str] = Field(None, description="Equipment ID or name involved")
    process_parameter: Optional[str] = Field(None, description="The process parameter that deviated (e.g. temperature, pressure)")
    standard_value: Optional[str] = Field(None, description="The approved/specification value with units")
    actual_value: Optional[str] = Field(None, description="The actual observed value with units")
    deviation_duration: Optional[str] = Field(None, description="How long the deviation lasted")
    date_of_occurrence: Optional[str] = Field(None, description="Date the deviation occurred")
    detected_by: Optional[str] = Field(None, description="Person or system that detected the deviation")
    immediate_action_taken: Optional[str] = Field(None, description="Summary of all immediate corrective steps taken")


class AssessedDeviation(BaseModel):
    """Impact assessment and severity produced by Node 2."""
    impact_assessment: str = Field(
        description="Short paragraph (3-6 sentences) on potential quality and regulatory impact"
    )
    severity: Literal["Critical", "Major", "Minor"] = Field(
        description="GMP-aligned severity classification"
    )
    severity_reason: str = Field(
        description="2-4 sentence justification referencing specific extracted values"
    )
    ai_confidence: float = Field(
        ge=0.0, le=1.0,
        description="Self-reported confidence in the severity classification (0.0–1.0)"
    )


# ── Node 1: Extract ────────────────────────────────────────────────────────────

def extract_node(state: GraphState) -> dict:
    """
    Reads raw_text from state, calls the LLM with the extract prompt,
    and returns the structured deviation fields as a dict under 'extracted'.

    If the LLM call fails, sets 'error' in state so assess_node can skip.
    """
    raw_text = state.get("raw_text", "").strip()

    if not raw_text:
        return {"error": "raw_text is empty — nothing to extract.", "extracted": None}

    try:
        structured_llm = _llm.with_structured_output(ExtractedDeviation)
        chain = extract_prompt | structured_llm
        result: ExtractedDeviation = chain.invoke({"raw_text": raw_text})
        return {
            "extracted": result.model_dump(),
            "error": None,
        }
    except Exception as exc:
        return {
            "extracted": None,
            "error": f"extract_node failed: {str(exc)}",
        }


# ── Node 2: Assess ─────────────────────────────────────────────────────────────

def assess_node(state: GraphState) -> dict:
    """
    Reads the 'extracted' dict from state (populated by extract_node),
    calls the LLM with the assess prompt, and returns impact/severity data
    under 'assessment'.

    Skips processing and propagates the error if extract_node failed.
    """
    if state.get("error"):
        # Don't attempt assessment if extraction already failed
        return {"assessment": None}

    extracted = state.get("extracted") or {}

    # Format extracted fields as readable key: value pairs for the prompt
    extracted_fields_text = "\n".join(
        f"  {key.replace('_', ' ').title()}: {value if value is not None else 'Not found'}"
        for key, value in extracted.items()
    )

    try:
        structured_llm = _llm.with_structured_output(AssessedDeviation)
        chain = assess_prompt | structured_llm
        result: AssessedDeviation = chain.invoke({"extracted_fields": extracted_fields_text})
        return {
            "assessment": result.model_dump(),
            "error": None,
        }
    except Exception as exc:
        return {
            "assessment": None,
            "error": f"assess_node failed: {str(exc)}",
        }
