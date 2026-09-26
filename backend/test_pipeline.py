"""
test_pipeline.py
----------------
Standalone test for the Phase 2 LangGraph pipeline.
Run from the backend/ directory:

    python test_pipeline.py

Does NOT require the FastAPI server or database to be running.
Does NOT print or log the GROQ_API_KEY.

Structure
---------
1. Original happy-path test  (11 checks, unchanged)
2. Edge case A: No batch number
3. Edge case B: Ambiguous / unknown duration
4. Edge case C: Vague, minimal information
"""

import json
import sys
from app.ai.pipeline import run_pipeline


# ── Test inputs ────────────────────────────────────────────────────────────────

# Original happy-path: all fields present in a well-structured report.
SAMPLE_DEVIATION = """
Deviation Report
Date of Report: July 15, 2024
Reported By: John Smith, Process Operator

Product: Metformin HCl API
Batch Number: MHC-2024-0715
Department: Manufacturing - Reactor Unit B
Equipment: Reactor R-204

DEVIATION DESCRIPTION:
During the synthesis of Metformin HCl (Batch MHC-2024-0715), the reaction temperature
in Reactor R-204 deviated from the approved process parameter range during Step 3
(Condensation Reaction). The approved temperature range for this critical step is
70-75 degrees C. At approximately 14:23 hours, the DCS alarm indicated a temperature
reading of 82 degrees C. The temperature remained above the upper specification limit
for approximately 15 minutes before operator intervention brought it back within the
approved range at 14:38 hours on July 15, 2024.

IMMEDIATE ACTIONS TAKEN:
1. Batch MHC-2024-0715 was immediately placed on hold pending QA review.
2. QA Manager Sarah Lee was notified verbally and via email.
3. The reactor temperature was manually adjusted back to within specification.
4. Thermocouple TC-204 was flagged for calibration verification by the engineering team.
5. A retained sample from the in-process batch was sent to QC for additional purity testing.

Detected by: Process Operator John Smith via DCS high-temperature alarm.
"""

# Edge case A: No batch number present.
CASE_A_NO_BATCH = """
During manufacturing of Metformin HCl API, reactor temperature increased to 82 degrees C
and remained above the specified range of 70-75 degrees C. The excursion lasted
approximately 15 minutes. QA was notified and the batch was placed on hold.
"""

# Edge case B: Duration explicitly unknown.
CASE_B_AMBIGUOUS_DURATION = """
An API manufacturing reactor experienced a temperature excursion to approximately
82 degrees C against a specification of 70-75 degrees C. The event was identified
during a routine review and the exact duration of the excursion could not be determined.
"""

# Edge case C: Very vague — no specifics, no batch, no exact values.
CASE_C_VAGUE = """
An unexpected temperature variation was observed during API manufacturing. The value
exceeded the normal operating range. The event was reported to QA for investigation.
"""


# ── Helpers ────────────────────────────────────────────────────────────────────

def pretty(label, data):
    """Print a labelled JSON block."""
    print("\n" + "=" * 60)
    print("  " + label)
    print("=" * 60)
    print(json.dumps(data, indent=2, default=str))


def run_edge_case(label, text, build_checks):
    """
    Run a single edge case through the pipeline and evaluate named checks.

    Parameters
    ----------
    label        : Human-readable name for this case.
    text         : Deviation text input.
    build_checks : Callable(result, extracted, assessment) -> list[(str, bool)]

    Returns True if all checks pass, False otherwise.
    Edge case failures are reported in-place; this function never calls sys.exit().
    """
    print("\n" + "-" * 60)
    print("[EDGE] " + label)
    print("-" * 60)

    result     = run_pipeline(text)
    extracted  = result.get("extracted")  or {}
    assessment = result.get("assessment") or {}

    if result.get("error"):
        print("  [CRASH] Pipeline returned error: " + str(result["error"]))

    # Always print the key fields so LLM behavior is visible.
    print("  batch_number      : " + repr(extracted.get("batch_number")))
    print("  deviation_duration: " + repr(extracted.get("deviation_duration")))
    print("  actual_value      : " + repr(extracted.get("actual_value")))
    print("  severity          : " + repr(assessment.get("severity")))
    print("  ai_confidence     : " + repr(assessment.get("ai_confidence")))

    all_passed = True
    for check_label, passed in build_checks(result, extracted, assessment):
        status = "  [PASS]" if passed else "  [FAIL]"
        print(f"{status}  {check_label}")
        if not passed:
            all_passed = False

    return all_passed


# ── Main test runner ───────────────────────────────────────────────────────────

def main():
    # ── Original happy-path test (11 checks, unchanged) ───────────────────────
    print("\n[TEST]  AIVOA.AI -- Deviation Intake Pipeline Test")
    print("-" * 60)
    print("Input text (first 120 chars):")
    print(SAMPLE_DEVIATION.strip()[:120] + "...")
    print("\n[...] Running pipeline (extract -> assess)...")

    result = run_pipeline(SAMPLE_DEVIATION)

    if result.get("error"):
        print("\n[FAIL] Pipeline error: " + str(result["error"]))
        sys.exit(1)

    pretty("NODE 1 OUTPUT - Extracted Deviation Fields", result["extracted"])
    pretty("NODE 2 OUTPUT - AI Impact & Severity Assessment", result["assessment"])

    print("\n" + "-" * 60)
    print("[CHECK] Validation checks (original happy-path):")

    extracted  = result["extracted"]  or {}
    assessment = result["assessment"] or {}

    checks = [
        ("extract node returned data",
         bool(extracted)),
        ("title extracted",
         bool(extracted.get("title"))),
        ("batch_number extracted",
         bool(extracted.get("batch_number"))),
        ("process_parameter extracted",
         bool(extracted.get("process_parameter"))),
        ("standard_value extracted",
         bool(extracted.get("standard_value"))),
        ("actual_value extracted",
         bool(extracted.get("actual_value"))),
        ("assess node returned data",
         bool(assessment)),
        ("severity is Critical/Major/Minor",
         assessment.get("severity") in {"Critical", "Major", "Minor"}),
        ("impact_assessment present",
         bool(assessment.get("impact_assessment"))),
        ("severity_reason present",
         bool(assessment.get("severity_reason"))),
        ("ai_confidence is 0-1 float",
         isinstance(assessment.get("ai_confidence"), float)
         and 0.0 <= assessment.get("ai_confidence", -1) <= 1.0),
    ]

    all_passed = True
    for label, passed in checks:
        status = "  [PASS]" if passed else "  [FAIL]"
        print(f"  {status}  {label}")
        if not passed:
            all_passed = False

    print("-" * 60)
    if not all_passed:
        print("[WARN] Some original checks failed -- review the output above.\n")
        sys.exit(1)
    print("[OK] All 11 original checks passed.\n")

    # ── Edge case section ──────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  EDGE CASE TESTS -- Graceful behavior with imperfect inputs")
    print("=" * 60)
    print("NOTE: Results are reported exactly as returned by the model.")
    print("      Failures reflect honest LLM behavior, not pipeline bugs.\n")

    edge_results = []

    # ── Case A: No batch number ────────────────────────────────────────────────
    def checks_a(result, extracted, assessment):
        return [
            ("pipeline did not crash",
             not result.get("error")),
            ("extract node returned data",
             bool(extracted)),
            ("batch_number is null (not in input)",
             extracted.get("batch_number") is None),
            ("process_parameter still extracted despite missing batch",
             bool(extracted.get("process_parameter"))),
            ("assess node produced output despite missing batch",
             bool(assessment)),
            ("severity is Critical/Major/Minor",
             assessment.get("severity") in {"Critical", "Major", "Minor"}),
        ]

    edge_results.append(
        run_edge_case("Case A -- Missing batch number", CASE_A_NO_BATCH, checks_a)
    )

    # ── Case B: Unknown duration ───────────────────────────────────────────────
    def checks_b(result, extracted, assessment):
        duration = extracted.get("deviation_duration")
        # Check duration is null OR explicitly marks uncertainty.
        # We cannot fully prevent the LLM inventing a value, but we check.
        # The raw value is printed above for honest inspection.
        uncertainty_words = [
            "unknown", "cannot", "could not", "undetermined",
            "unclear", "not determined", "not available", "n/a",
        ]
        invented = (
            duration is not None
            and not any(w in duration.lower() for w in uncertainty_words)
        )
        return [
            ("pipeline did not crash",
             not result.get("error")),
            ("assess node produced output despite ambiguous duration",
             bool(assessment)),
            ("severity is Critical/Major/Minor",
             assessment.get("severity") in {"Critical", "Major", "Minor"}),
            ("duration is null or flagged uncertain (not invented)",
             not invented),
        ]

    edge_results.append(
        run_edge_case(
            "Case B -- Ambiguous / unknown duration",
            CASE_B_AMBIGUOUS_DURATION,
            checks_b,
        )
    )

    # ── Case C: Vague / minimal input ─────────────────────────────────────────
    def checks_c(result, extracted, assessment):
        return [
            ("pipeline did not crash",
             not result.get("error")),
            ("extract node returned data",
             bool(extracted)),
            ("batch_number is null (not in input)",
             extracted.get("batch_number") is None),
            ("actual_value is null (no specific reading in input)",
             extracted.get("actual_value") is None),
            ("assess node produced output from minimal information",
             bool(assessment)),
            ("severity is Critical/Major/Minor",
             assessment.get("severity") in {"Critical", "Major", "Minor"}),
        ]

    edge_results.append(
        run_edge_case(
            "Case C -- Vague, minimal information",
            CASE_C_VAGUE,
            checks_c,
        )
    )

    # ── Edge case summary ──────────────────────────────────────────────────────
    passed_count = sum(1 for r in edge_results if r)
    total_count  = len(edge_results)
    print("\n" + "=" * 60)
    print(f"[EDGE SUMMARY] {passed_count}/{total_count} edge cases fully passed.")
    if passed_count < total_count:
        print("[NOTE] Some edge case checks failed.")
        print("       See individual case output above for exact model behavior.")
        print("       No pipeline or prompt changes were made to force these to pass.")
    else:
        print("[OK] All edge case checks passed.")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
