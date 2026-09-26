"""
schemas.py
----------
Pydantic schemas for request validation and response serialisation (v2).
Aligned to the reference UI field list.

Enforcement pattern (same as SeverityEnum in v1):
  1. Literal type in nodes.py  -> LLM structurally cannot return an invalid value
  2. Pydantic enum here         -> API layer rejects invalid values on POST /deviations
  3. Enum column in models.py   -> DB rejects invalid values at write time
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from app.models import SeverityEnum, SourceEnum, InitialImpactEnum, InputSourceEnum, StatusEnum


# ── POST /process request body ────────────────────────────────────────────────
class ProcessTextRequest(BaseModel):
    """Request body for POST /process — plain deviation text submitted by the user."""
    text: str = Field(..., min_length=1, description="Raw deviation text to process with AI")


# ── POST /extract/pdf response ────────────────────────────────────────────────
class PDFExtractResponse(BaseModel):
    """
    Response from POST /extract/pdf.
    Returns only the raw extracted text — no AI processing.
    The frontend displays this to the user who then triggers AI separately.
    """
    extracted_text: str = Field(description="Full text extracted from the PDF by PyMuPDF")
    page_count: int     = Field(description="Number of pages in the uploaded PDF")
    filename: str       = Field(description="Original filename of the uploaded PDF")


# ── Extracted fields (what the AI fills in from the deviation text) ───────────
class ExtractedFields(BaseModel):
    """
    Fields extracted by the AI from raw deviation text.
    Matches the Log Deviation form in the reference UI.
    detailed_description absorbs the formerly separate fields:
      process_parameter, standard_value, actual_value, equipment_id,
      deviation_duration, detected_by, immediate_action_taken, description.
    """
    title:                    Optional[str] = None
    site_plant:               Optional[str] = None
    date_of_occurrence:       Optional[str] = None                              # kept as str; see judgment call note
    source:                   Optional[SourceEnum] = None
    related_product_material: Optional[str] = None
    batch_lot_number:         Optional[str] = None
    detailed_description:     Optional[str] = Field(None, max_length=2000)     # UI limit: 2000 chars


# ── Assessment fields (AI risk assessment section) ────────────────────────────
class AssessmentFields(BaseModel):
    initial_severity:      Optional[SeverityEnum]      = None
    initial_impact:        Optional[InitialImpactEnum] = None
    severity_reason:       Optional[str]               = None
    suggested_next_action: Optional[str]               = None
    ai_confidence:         Optional[float]             = Field(None, ge=0.0, le=1.0)


# ── Combined AI result returned from POST /process ────────────────────────────
class AIProcessResult(BaseModel):
    extracted:  ExtractedFields
    assessment: AssessmentFields


# ── Request body for POST /deviations (save to DB) ────────────────────────────
class DeviationCreate(ExtractedFields, AssessmentFields):
    """
    All user-editable fields merged into one flat schema.
    The user may have changed any AI-populated value before saving.
    System fields (raw_input_text, input_source, original_filename, status)
    are included here because the frontend sends them on save.
    """
    raw_input_text:    Optional[str]             = None
    input_source:      Optional[InputSourceEnum] = None
    original_filename: Optional[str]             = None
    status:            StatusEnum                = StatusEnum.Logged


# ── Response schema for a saved deviation record ──────────────────────────────
class DeviationResponse(DeviationCreate):
    id:         int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}   # ORM mode (Pydantic v2)
