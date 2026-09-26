"""
schemas.py
----------
Pydantic schemas used for request validation and response serialisation.
These are separate from the SQLAlchemy models — models talk to the DB,
schemas talk to the API layer.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from app.models import SeverityEnum, InputSourceEnum, StatusEnum


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
    page_count: int = Field(description="Number of pages in the uploaded PDF")
    filename: str = Field(description="Original filename of the uploaded PDF")


# ── Extracted fields (what the AI fills in from raw text) ─────────────────────
class ExtractedFields(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    department: Optional[str] = None
    product_name: Optional[str] = None
    batch_number: Optional[str] = None
    equipment_id: Optional[str] = None
    process_parameter: Optional[str] = None
    standard_value: Optional[str] = None
    actual_value: Optional[str] = None
    deviation_duration: Optional[str] = None
    date_of_occurrence: Optional[str] = None
    detected_by: Optional[str] = None
    immediate_action_taken: Optional[str] = None


# ── Assessment fields (what the AI assesses after extraction) ─────────────────
class AssessmentFields(BaseModel):
    impact_assessment: Optional[str] = None
    severity: Optional[SeverityEnum] = None
    severity_reason: Optional[str] = None
    ai_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)


# ── Combined AI result returned from POST /process ────────────────────────────
class AIProcessResult(BaseModel):
    extracted: ExtractedFields
    assessment: AssessmentFields


# ── Request body for POST /deviations (save to DB) ────────────────────────────
class DeviationCreate(ExtractedFields, AssessmentFields):
    """
    All user-editable fields merged into one flat schema.
    The user may have changed any AI-populated value before saving.
    """
    raw_input_text: Optional[str] = None
    input_source: Optional[InputSourceEnum] = None
    original_filename: Optional[str] = None
    status: StatusEnum = StatusEnum.Logged


# ── Response schema for a saved deviation record ──────────────────────────────
class DeviationResponse(DeviationCreate):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}  # enables ORM mode (replaces orm_mode in Pydantic v2)
