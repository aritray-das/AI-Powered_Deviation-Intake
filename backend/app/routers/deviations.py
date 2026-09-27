"""
routers/deviations.py
---------------------
All deviation-related API endpoints.

Endpoints
---------
POST /process          - Run AI pipeline on pasted text (no DB write)
POST /process/pdf      - Upload PDF, extract text, run AI pipeline (no DB write)
POST /deviations       - Save a reviewed deviation record to MySQL
GET  /deviations       - Retrieve all saved deviation records (newest first)

Design note
-----------
The AI pipeline is intentionally NOT wired to auto-save. The frontend
displays AI results in an editable form; the user saves via POST /deviations
only after reviewing. This keeps human oversight in the loop.
"""

from typing import List

import fitz  # PyMuPDF
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.ai.pipeline import run_pipeline, run_edit_interaction
from app.database import get_db
from app.models import Deviation
from app.schemas import (
    AIProcessResult,
    AssessmentFields,
    DeviationCreate,
    DeviationResponse,
    ExtractedFields,
    PDFExtractResponse,
    ProcessTextRequest,
    EditInteractionRequest,
    EditInteractionResponse,
)

router = APIRouter()


# ── Helper ─────────────────────────────────────────────────────────────────────

def _pipeline_result_to_schema(result: dict) -> AIProcessResult:
    """
    Convert the raw GraphState dict returned by run_pipeline() into the
    AIProcessResult Pydantic schema the API returns to the frontend.

    Raises HTTPException 500 if the pipeline reported an internal error.
    """
    if result.get("error"):
        # Do not leak internal error details to the caller
        raise HTTPException(
            status_code=500,
            detail="The AI pipeline encountered an error while processing the input. "
                   "Please try again or contact support.",
        )

    extracted_data = result.get("extracted") or {}
    assessment_data = result.get("assessment") or {}

    return AIProcessResult(
        extracted=ExtractedFields(**extracted_data),
        assessment=AssessmentFields(**assessment_data),
    )


# ── POST /extract/pdf ──────────────────────────────────────────────────────────
# Implements the preferred PDF workflow:
#   1. Upload PDF  →  raw text returned here (user inspects it)
#   2. User clicks "Process with AI"
#   3. Frontend sends text to POST /process  →  AI result
# This keeps human oversight between PDF extraction and AI processing.

def _extract_text_from_document_upload(file_content: bytes, filename: str) -> tuple:
    """
    Shared document text-extraction logic used by both /extract/pdf and /process/pdf.
    Now supports both PDF and DOCX formats.
    Returns (raw_text: str, page_count: int).
    Raises HTTPException on invalid/empty document.
    """
    lower_filename = filename.lower()
    raw_text = ""
    page_count = 1

    if lower_filename.endswith(".pdf"):
        try:
            doc = fitz.open(stream=file_content, filetype="pdf")
        except Exception:
            raise HTTPException(
                status_code=400,
                detail="Could not open the uploaded file as a PDF. "
                       "Ensure the file is a valid, non-corrupted PDF.",
            )
        page_count = len(doc)
        for page in doc:
            raw_text += page.get_text()
        doc.close()
    elif lower_filename.endswith(".docx") or lower_filename.endswith(".doc"):
        try:
            import docx
            from io import BytesIO
            doc = docx.Document(BytesIO(file_content))
            raw_text = "\n".join([p.text for p in doc.paragraphs])
        except Exception:
            raise HTTPException(
                status_code=400,
                detail="Could not extract text from the Word document. "
                       "Note that older .doc formats might not be supported.",
            )
    else:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file format. Only PDF and DOC/DOCX are allowed.",
        )

    if not raw_text.strip():
        raise HTTPException(
            status_code=400,
            detail="This document does not contain extractable text. "
                   "Scanned/image-only PDFs are not supported — OCR is not implemented. "
                   "Please use a document with selectable text, or paste the text directly.",
        )

    return raw_text, page_count


@router.post(
    "/extract/pdf",
    response_model=PDFExtractResponse,
    summary="Extract raw text from a PDF (no AI processing)",
    tags=["AI Processing"],
)
async def extract_pdf_text(file: UploadFile = File(...)):
    """
    Step 1 of the preferred PDF workflow.

    Accepts a text-based PDF, extracts its text using PyMuPDF, and returns
    the raw text WITHOUT running AI. The frontend displays this text to the
    user, who can inspect it and then click 'Process with AI' to send it
    to POST /process.

    This preserves human oversight between PDF extraction and AI processing.
    OCR is NOT supported.
    """
    if not file.filename or not (file.filename.lower().endswith(".pdf") or file.filename.lower().endswith(".docx") or file.filename.lower().endswith(".doc")):
        raise HTTPException(
            status_code=400,
            detail="Uploaded file must be a PDF or Word document (.doc/.docx).",
        )

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    raw_text, page_count = _extract_text_from_document_upload(content, file.filename)

    return PDFExtractResponse(
        extracted_text=raw_text,
        page_count=page_count,
        filename=file.filename,
    )


# ── POST /process ──────────────────────────────────────────────────────────────

@router.post(
    "/process",
    response_model=AIProcessResult,
    summary="Run AI pipeline on deviation text",
    tags=["AI Processing"],
)
def process_text(body: ProcessTextRequest):
    """
    Accept raw deviation text, run the LangGraph extract→assess pipeline,
    and return structured AI output.

    Does NOT save anything to the database.
    The frontend uses this response to pre-populate the Log Deviation form
    for the user to review and edit before saving.
    """
    text = body.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text must not be empty.")

    result = run_pipeline(text)
    return _pipeline_result_to_schema(result)


# ── POST /process/pdf ──────────────────────────────────────────────────────────

@router.post(
    "/process/pdf",
    response_model=AIProcessResult,
    summary="Upload a PDF and run AI pipeline on its extracted text",
    tags=["AI Processing"],
)
async def process_pdf(file: UploadFile = File(...)):
    """
    Combined PDF upload + AI processing in one step.

    Accepts a text-based PDF, extracts text via PyMuPDF, then immediately
    runs the LangGraph pipeline. Does NOT save to the database.

    NOTE: For the preferred workflow where the user inspects extracted text
    before AI processing, use POST /extract/pdf first, then POST /process.
    This endpoint is retained for convenience and backward compatibility.
    OCR is NOT supported.
    """
    if not file.filename or not (file.filename.lower().endswith(".pdf") or file.filename.lower().endswith(".docx") or file.filename.lower().endswith(".doc")):
        raise HTTPException(
            status_code=400,
            detail="Uploaded file must be a PDF or Word document (.doc/.docx).",
        )

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    raw_text, _ = _extract_text_from_document_upload(content, file.filename)
    result = run_pipeline(raw_text)
    return _pipeline_result_to_schema(result)


# ── POST /deviations/edit ──────────────────────────────────────────────────────

@router.post(
    "/deviations/edit",
    response_model=EditInteractionResponse,
    summary="Parse a natural language correction and update the deviation form",
    tags=["AI Processing"],
)
def edit_deviation_interaction(body: EditInteractionRequest):
    """
    Accepts a user's natural language correction and the current state of the form.
    Returns the specific fields updated, a confirmation reply, and potentially
    recalculated risk assessment fields if the change was risk-relevant.
    """
    message = body.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Edit message must not be empty.")

    result = run_edit_interaction(message, body.current_state)

    if result.get("error"):
        raise HTTPException(
            status_code=500,
            detail="The AI pipeline encountered an error while processing the edit. "
                   "Please try again or contact support."
        )

    # Combine updated extracted and assessment into one flat dict for the frontend
    updated_state = {**(result.get("extracted") or {}), **(result.get("assessment") or {})}

    return EditInteractionResponse(
        updated_state=updated_state,
        reply=result.get("edit_reply") or "I have processed your request.",
        fields_changed=result.get("fields_changed") or []
    )



# ── POST /deviations ───────────────────────────────────────────────────────────

@router.post(
    "/deviations",
    response_model=DeviationResponse,
    status_code=201,
    summary="Save a reviewed deviation record to the database",
    tags=["Deviations"],
)
def create_deviation(body: DeviationCreate, db: Session = Depends(get_db)):
    """
    Persist a deviation record that the user has reviewed (and possibly edited)
    after AI pre-population.

    This endpoint is intentionally separate from /process — the user must
    explicitly save, preserving human oversight in the QA workflow.

    The raw_input_text field should be sent by the frontend to maintain
    the full audit trail in the database.
    """
    try:
        # Convert Pydantic schema → dict, then unpack into the ORM model.
        # model_dump() preserves Python enum instances, which SQLAlchemy expects.
        db_deviation = Deviation(**body.model_dump())
        db.add(db_deviation)
        db.commit()
        db.refresh(db_deviation)
        return db_deviation
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to save the deviation record. Please try again.",
        ) from exc


# ── GET /deviations ────────────────────────────────────────────────────────────

@router.get(
    "/deviations",
    response_model=List[DeviationResponse],
    summary="Retrieve all saved deviation records",
    tags=["Deviations"],
)
def list_deviations(db: Session = Depends(get_db)):
    """
    Return all saved deviation records ordered newest-first (by id descending).
    """
    try:
        records = (
            db.query(Deviation)
            .order_by(Deviation.id.desc())
            .all()
        )
        return records
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve deviation records. Please try again.",
        ) from exc
