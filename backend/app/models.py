"""
models.py
---------
SQLAlchemy ORM model for the Deviation table.
Schema realigned to match the reference UI field list (v2).

Removed fields (old): description, department, product_name, batch_number,
  equipment_id, process_parameter, standard_value, actual_value,
  deviation_duration, detected_by, immediate_action_taken, impact_assessment

Added fields (new): site_plant, source, related_product_material,
  batch_lot_number, detailed_description, initial_impact, suggested_next_action

Renamed fields: severity → initial_severity

Unchanged: id, status, input_source, original_filename, raw_input_text,
  created_at, updated_at, title, date_of_occurrence, severity_reason, ai_confidence
"""

import enum
from sqlalchemy import Column, Integer, String, Text, Float, Enum, DateTime, func

from app.database import Base

# Helper so SQLAlchemy stores enum .values (e.g. "Production Floor") not .names ("Production_Floor").
_values = lambda e: [m.value for m in e]


# ── Enums ──────────────────────────────────────────────────────────────────────

class SeverityEnum(enum.Enum):
    """Unchanged from v1. Field renamed to initial_severity in the table."""
    Critical = "Critical"
    Major = "Major"
    Minor = "Minor"


class SourceEnum(enum.Enum):
    """Where/how the deviation was identified. Matches reference UI source field."""
    Production_Floor       = "Production Floor"
    Laboratory             = "Laboratory"
    Audit_Finding          = "Audit Finding"
    Regulatory_Inspection  = "Regulatory Inspection"
    Self_Reported          = "Self-Reported"
    Other                  = "Other"


class InitialImpactEnum(enum.Enum):
    """Quality impact level. Separate from severity (which captures risk level)."""
    No_Impact       = "No Impact"
    Minor_Impact    = "Minor Impact"
    Major_Impact    = "Major Impact"
    Critical_Impact = "Critical Impact"


class InputSourceEnum(enum.Enum):
    pdf         = "pdf"
    pasted_text = "pasted_text"


class StatusEnum(enum.Enum):
    Draft  = "Draft"
    Logged = "Logged"


# ── ORM Model ──────────────────────────────────────────────────────────────────

class Deviation(Base):
    """
    Single table storing one deviation record: form fields, AI assessment,
    system fields, and the original raw text for the audit trail.
    """
    __tablename__ = "deviations"

    # ── System-managed fields (unchanged) ──────────────────────────────────────
    id                = Column(Integer, primary_key=True, index=True, autoincrement=True)
    status            = Column(Enum(StatusEnum), nullable=False, default=StatusEnum.Draft)
    input_source      = Column(Enum(InputSourceEnum), nullable=True)
    original_filename = Column(String(255), nullable=True)
    raw_input_text    = Column(Text, nullable=True)
    created_at        = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at        = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # ── Log Deviation form fields (AI-populated, user-editable) ────────────────
    title                    = Column(String(500), nullable=True)
    site_plant               = Column(String(255), nullable=True)
    date_of_occurrence       = Column(String(100), nullable=True)   # Stored as string; AI may return "July 15, 2024"
    source                   = Column(Enum(SourceEnum, values_callable=_values), nullable=True)
    related_product_material = Column(String(500), nullable=True)
    batch_lot_number         = Column(String(255), nullable=True)   # renamed from batch_number
    detailed_description     = Column(Text, nullable=True)          # absorbs: description, process_parameter,
                                                                    #   standard_value, actual_value, equipment_id,
                                                                    #   deviation_duration, detected_by, immediate_action_taken

    # ── AI Risk Assessment fields (AI-populated, user-editable) ────────────────
    initial_severity      = Column(Enum(SeverityEnum), nullable=True)    # renamed from severity; names==values so no values_callable needed
    initial_impact        = Column(Enum(InitialImpactEnum, values_callable=_values), nullable=True)
    severity_reason       = Column(Text, nullable=True)
    suggested_next_action = Column(Text, nullable=True)
    ai_confidence         = Column(Float, nullable=True)                 # 0.0–1.0, self-reported by LLM
