"""
test_pipeline.py
----------------
Standalone test for the Phase 2 LangGraph pipeline.
Run from the backend/ directory:

    python test_pipeline.py

Does NOT require the FastAPI server or database to be running.
Does NOT print or log the GROQ_API_KEY.
"""

import json
import sys
from app.ai.pipeline import run_pipeline

# -- Sample deviation text ------------------------------------------------------
# Realistic API manufacturing temperature excursion — covers all extractable fields.

SAMPLE_DEVIATION = """
Deviation Report
Date of Report: July 15, 2024
Reported By: John Smith, Process Operator

Product: Metformin HCl API
Batch Number: MHC-2024-0715
Department: Manufacturing — Reactor Unit B
Equipment: Reactor R-204

DEVIATION DESCRIPTION:
During the synthesis of Metformin HCl (Batch MHC-2024-0715), the reaction temperature
in Reactor R-204 deviated from the approved process parameter range during Step 3
(Condensation Reaction). The approved temperature range for this critical step is
70–75°C. At approximately 14:23 hours, the DCS alarm indicated a temperature reading
of 82°C. The temperature remained above the upper specification limit for approximately
15 minutes before operator intervention brought it back within the approved range at
14:38 hours on July 15, 2024.

IMMEDIATE ACTIONS TAKEN:
1. Batch MHC-2024-0715 was immediately placed on hold pending QA review.
2. QA Manager Sarah Lee was notified verbally and via email.
3. The reactor temperature was manually adjusted back to within specification.
4. Thermocouple TC-204 was flagged for calibration verification by the engineering team.
5. A retained sample from the in-process batch was sent to QC for additional purity testing.

Detected by: Process Operator John Smith via DCS high-temperature alarm.
"""


def pretty(label: str, data: dict) -> None:
    """Print a labelled JSON block — redacts nothing since no secrets are in data."""
    print(f"\n{'=' * 60}")
    print(f"  {label}")
    print('=' * 60)
    print(json.dumps(data, indent=2, default=str))


def main():
    print("\n[TEST]  AIVOA.AI -- Deviation Intake Pipeline Test")
    print("-" * 60)
    print("Input text (first 120 chars):")
    print(SAMPLE_DEVIATION.strip()[:120] + "...")

    print("\n[...] Running pipeline (extract -> assess)...")

    result = run_pipeline(SAMPLE_DEVIATION)

    # -- Check for errors -------------------------------------------------------
    if result.get("error"):
        print(f"\n[FAIL] Pipeline error: {result['error']}")
        sys.exit(1)

    # -- Print results ----------------------------------------------------------
    pretty("NODE 1 OUTPUT — Extracted Deviation Fields", result["extracted"])
    pretty("NODE 2 OUTPUT — AI Impact & Severity Assessment", result["assessment"])

    # -- Quick validation -------------------------------------------------------
    print(f"\n{'-' * 60}")
    print("[CHECK] Validation checks:")

    extracted = result["extracted"] or {}
    assessment = result["assessment"] or {}

    checks = [
        ("extract node returned data",        bool(extracted)),
        ("title extracted",                   bool(extracted.get("title"))),
        ("batch_number extracted",            bool(extracted.get("batch_number"))),
        ("process_parameter extracted",       bool(extracted.get("process_parameter"))),
        ("standard_value extracted",          bool(extracted.get("standard_value"))),
        ("actual_value extracted",            bool(extracted.get("actual_value"))),
        ("assess node returned data",         bool(assessment)),
        ("severity is Critical/Major/Minor",  assessment.get("severity") in {"Critical", "Major", "Minor"}),
        ("impact_assessment present",         bool(assessment.get("impact_assessment"))),
        ("severity_reason present",           bool(assessment.get("severity_reason"))),
        ("ai_confidence is 0–1 float",        isinstance(assessment.get("ai_confidence"), float)
                                               and 0.0 <= assessment.get("ai_confidence", -1) <= 1.0),
    ]

    all_passed = True
    for label, passed in checks:
        status = "  [PASS]" if passed else "  [FAIL]"
        print(f"  {status}  {label}")
        if not passed:
            all_passed = False

    print("-" * 60)
    if all_passed:
        print("[OK] All checks passed -- Phase 2 pipeline is working correctly.\n")
    else:
        print("[WARN] Some checks failed -- review the output above.\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
