"""
models.py
---------
SQLAlchemy ORM model for the Deviation table.
Every column here maps directly to a database column in MySQL.
Alembic reads this model to auto-generate migration scripts.
"""

import enum
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Text, Float,
    Enum, DateTime, func
)

from app.database import Base


class SeverityEnum(enum.Enum):
    Critical = "Critical"
    Major = "Major"
    Minor = "Minor"


class InputSourceEnum(enum.Enum):
    pdf = "pdf"
    pasted_text = "pasted_text"


class StatusEnum(enum.Enum):
    Draft = "Draft"
    Logged = "Logged"


class Deviation(Base):
    """
    Single table that stores everything about one deviation record:
    extracted fields, AI assessment fields, system fields, and the
    original raw text for the audit trail.
    """
    __tablename__ = "deviations"

    # ── System-managed fields ──────────────────────────────────────────
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    status = Column(Enum(StatusEnum), nullable=False, default=StatusEnum.Draft)
    input_source = Column(Enum(InputSourceEnum), nullable=True)
    original_filename = Column(String(255), nullable=True)   # only set for PDF uploads
    raw_input_text = Column(Text, nullable=True)             # full original text, audit trail
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(),
                        onupdate=func.now(), nullable=False)

    # ── Extracted fields (AI-populated, user-editable) ─────────────────
    title = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    department = Column(String(255), nullable=True)
    product_name = Column(String(255), nullable=True)
    batch_number = Column(String(255), nullable=True)
    equipment_id = Column(String(255), nullable=True)
    process_parameter = Column(String(255), nullable=True)
    standard_value = Column(String(255), nullable=True)
    actual_value = Column(String(255), nullable=True)
    deviation_duration = Column(String(255), nullable=True)
    date_of_occurrence = Column(String(100), nullable=True)  # stored as string; user may type "2024-07-15" or "July 15"
    detected_by = Column(String(255), nullable=True)
    immediate_action_taken = Column(Text, nullable=True)

    # ── AI assessment fields (AI-populated, user-editable) ─────────────
    impact_assessment = Column(Text, nullable=True)
    severity = Column(Enum(SeverityEnum), nullable=True)
    severity_reason = Column(Text, nullable=True)
    ai_confidence = Column(Float, nullable=True)             # 0.0 – 1.0, self-reported by LLM
