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

Schema realignment (v2):
  ExtractedDeviation: now targets the reference UI Log Deviation form fields.
  AssessedDeviation:  now includes initial_impact and suggested_next_action.
"""

from typing import Literal, Optional

from langchain_groq import ChatGroq
from pydantic import BaseModel, Field

from app.config import settings
from app.ai.state import GraphState, EditGraphState
from app.ai.prompts import extract_prompt, assess_prompt, edit_prompt


# ── Shared LLM instance ────────────────────────────────────────────────────────
# temperature=0 → deterministic output for structured data extraction.
# NOTE: llama-3.3-70b-versatile is not available on this Groq account.
# Using openai/gpt-oss-120b (largest available model) as a replacement.
_llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0,
    api_key=settings.GROQ_API_KEY,
)


# ── Pydantic output schemas (used with with_structured_output) ─────────────────
# Literal types here enforce that the LLM structurally cannot return a value
# outside the allowed set — this is the first layer of the three-layer constraint.

class ExtractedDeviation(BaseModel):
    """Structured deviation fields extracted from raw text by Node 1 (v2)."""
    title: Optional[str] = Field(
        None,
        description="Concise 5-10 word summary of the deviation type"
    )
    site_plant: Optional[str] = Field(
        None,
        description="Manufacturing site or plant unit where the deviation occurred (e.g. 'API Manufacturing Unit', 'Reactor Unit B')"
    )
    date_of_occurrence: Optional[str] = Field(
        None,
        description="Date the deviation occurred (NOT the report date). Return the date as it appears in the text."
    )
    source: Optional[Literal[
        "Production Floor",
        "Laboratory",
        "Audit Finding",
        "Regulatory Inspection",
        "Self-Reported",
        "Other"
    ]] = Field(
        None,
        description="Where or how the deviation was identified. Choose the best match from the allowed values."
    )
    related_product_material: Optional[str] = Field(
        None,
        description="Name of the product or material involved (e.g. 'Metformin HCl API', 'Ibuprofen API')"
    )
    batch_lot_number: Optional[str] = Field(
        None,
        description="Batch or lot number of the affected material"
    )
    detailed_description: Optional[str] = Field(
        None,
        description=(
            "Comprehensive narrative description of the deviation. Include all of: "
            "what parameter deviated, the specification/standard value, the actual observed value, "
            "the equipment involved, how long the deviation lasted, who detected it and how, "
            "and what immediate corrective actions were taken. "
            "Write as a single cohesive paragraph. Maximum 2000 characters."
        )
    )


class AssessedDeviation(BaseModel):
    """Impact assessment and severity produced by Node 2 (v2)."""
    initial_severity: Literal["Critical", "Major", "Minor"] = Field(
        description="GMP-aligned severity classification"
    )
    initial_impact: Literal[
        "No Impact",
        "Minor Impact",
        "Major Impact",
        "Critical Impact"
    ] = Field(
        description="Quality impact level of the deviation on the product or process"
    )
    severity_reason: str = Field(
        description="2-4 sentence justification referencing specific extracted values (parameter, actual vs spec, duration)"
    )
    suggested_next_action: str = Field(
        description=(
            "Short, specific, actionable QA recommendation for immediate next step. "
            "Examples: 'Initiate CAPA investigation', 'Hold batch pending QA review', "
            "'Notify QA Head immediately', 'Perform OOS investigation'. "
            "One sentence, action-verb first."
        )
    )
    ai_confidence: float = Field(
        ge=0.0, le=1.0,
        description="Self-reported confidence in the severity and impact classification (0.0-1.0). Lower when key fields are missing or ambiguous."
    )


class PartialUpdate(BaseModel):
    """A partial set of fields to update, based on the user's edit message."""
    title: Optional[str] = None
    site_plant: Optional[str] = None
    date_of_occurrence: Optional[str] = None
    source: Optional[Literal["Production Floor", "Laboratory", "Audit Finding", "Regulatory Inspection", "Self-Reported", "Other"]] = None
    related_product_material: Optional[str] = None
    batch_lot_number: Optional[str] = None
    detailed_description: Optional[str] = None
    initial_severity: Optional[Literal["Critical", "Major", "Minor"]] = None
    initial_impact: Optional[Literal["No Impact", "Minor Impact", "Major Impact", "Critical Impact"]] = None
    severity_reason: Optional[str] = None
    suggested_next_action: Optional[str] = None


class EditDecision(BaseModel):
    """The decision made by the AI after parsing an edit message."""
    partial_update: PartialUpdate = Field(description="Only the fields that changed.")
    risk_relevant: bool = Field(description="True if the change might affect risk assessment.")
    reply: str = Field(description="Natural language confirmation of what changed, or a clarifying question.")


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
        structured_llm = _llm.with_structured_output(ExtractedDeviation, method="json_mode")
        chain  = extract_prompt | structured_llm
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
        return {"assessment": None}

    extracted = state.get("extracted") or {}

    extracted_fields_text = "\n".join(
        f"  {key.replace('_', ' ').title()}: {value if value is not None else 'Not found'}"
        for key, value in extracted.items()
    )

    try:
        structured_llm = _llm.with_structured_output(AssessedDeviation, method="json_mode")
        chain  = assess_prompt | structured_llm
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


# ── Node 3: Edit ───────────────────────────────────────────────────────────────

def edit_node(state: EditGraphState) -> dict:
    """
    Reads 'edit_message' and 'current_state' from state.
    Parses the natural language correction, determines which fields to update,
    and returns a merged extracted/assessment dictionary.
    """
    edit_message = state.get("edit_message", "")
    current_state = state.get("current_state") or {}

    if not edit_message:
        return {"error": "No edit message provided.", "fields_changed": []}

    try:
        structured_llm = _llm.with_structured_output(EditDecision, method="json_mode")
        chain = edit_prompt | structured_llm

        import json
        current_state_str = json.dumps(current_state, indent=2)
        result: EditDecision = chain.invoke({
            "current_state": current_state_str,
            "message": edit_message
        })

        update_dict = result.partial_update.model_dump(exclude_unset=True, exclude_none=True)
        fields_changed = list(update_dict.keys())

        # Merge updates with current_state to generate full new state
        new_state = current_state.copy()
        for k, v in update_dict.items():
            new_state[k] = v

        # Re-split into extracted and assessment
        extracted = {}
        assessment = {}
        for k, v in new_state.items():
            if k in ExtractedDeviation.model_fields:
                extracted[k] = v
            elif k in AssessedDeviation.model_fields:
                assessment[k] = v

        return {
            "extracted": extracted,
            "assessment": assessment,
            "edit_reply": result.reply,
            "fields_changed": fields_changed,
            "risk_relevant": result.risk_relevant,
            "error": None
        }
    except Exception as exc:
        return {
            "error": f"edit_node failed: {str(exc)}",
            "fields_changed": [],
            "risk_relevant": False
        }
