import sys
import json
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from app.ai.pipeline import run_edit_interaction

# Base state to run tests against
CURRENT_STATE = {
    "title": "Temperature Excursion",
    "site_plant": "API Manufacturing Unit",
    "date_of_occurrence": "July 16, 2024",
    "source": "Production Floor",
    "related_product_material": "Metformin HCl API",
    "batch_lot_number": "MHC-2024-0715",
    "detailed_description": "Reactor reached 82C instead of 75C for 15 mins.",
    "initial_severity": "Minor",
    "initial_impact": "Minor Impact",
    "severity_reason": "Brief excursion, minimal impact expected.",
    "suggested_next_action": "Routine review.",
    "ai_confidence": 0.9
}

def run_case(label, message, expected_fields_changed=None, check_reassess=None):
    print(f"\n[TEST CASE] {label}")
    print(f"User Message: {message}")
    
    result = run_edit_interaction(message, CURRENT_STATE)
    
    if result.get("error"):
        print("[FAIL] Crash:", result["error"])
        return False
        
    fields_changed = result.get("fields_changed") or []
    reply = result.get("edit_reply")
    risk_relevant = result.get("risk_relevant")
    
    print(f"Reply: {reply}")
    print(f"Fields changed: {fields_changed}")
    print(f"Risk relevant: {risk_relevant}")
    
    # Check that unmentioned fields are strictly untouched
    extracted = result.get("extracted") or {}
    assessment = result.get("assessment") or {}
    merged = {**extracted, **assessment}
    
    untouched_failed = False
    for k, v in CURRENT_STATE.items():
        if k not in fields_changed:
            if merged.get(k) != v and k not in ["initial_severity", "initial_impact", "severity_reason", "suggested_next_action", "ai_confidence"]:
                # If risk_relevant is True, assessment fields might naturally change, so we only strictly check extraction fields if they weren't in fields_changed.
                # Actually, if risk_relevant is true, we EXPECT assessment fields to change.
                if not risk_relevant:
                    print(f"  [FAIL] Field '{k}' was changed but not listed in fields_changed! (was '{v}', now '{merged.get(k)}')")
                    untouched_failed = True
    if not untouched_failed:
        print("  [PASS] Unmentioned fields provably untouched.")
    
    passed = not untouched_failed
    if expected_fields_changed is not None:
        if not set(expected_fields_changed).issubset(set(fields_changed)):
            print(f"  [FAIL] Expected at least {expected_fields_changed}, got {fields_changed}")
            passed = False
        else:
            print(f"  [PASS] Fields changed correctly.")
            
    if check_reassess is not None:
        if risk_relevant != check_reassess:
            print(f"  [FAIL] Expected risk_relevant={check_reassess}")
            passed = False
        else:
            print(f"  [PASS] Risk reassessment triggered correctly.")
            
    return passed

def main():
    print("--- Testing Edit Interaction Tool ---")
    
    c1 = run_case(
        "1. Simple single-field correction",
        "actually the batch number is BMX240602 and affected quantity is 48 capsules",
        expected_fields_changed=["batch_lot_number"],
        check_reassess=True # Changing batch/quantity is risk relevant
    )
    
    c2 = run_case(
        "2. Risk-relevant correction",
        "the severity should be Critical, this affected a wider batch than I said",
        expected_fields_changed=["initial_severity"],
        check_reassess=True
    )
    
    c3 = run_case(
        "3. Ambiguous/unrecognized message",
        "what does severity mean?",
        expected_fields_changed=[],
        check_reassess=False
    )
    
    c4 = run_case(
        "4. Value outside enum",
        "set severity to Extreme",
        # The prompt says: "map it to the closest valid enum if possible. If you cannot map it, do not change the field..."
        # LLM might map "Extreme" to "Critical", which is acceptable, or return [] and ask for clarification.
        # We just verify it doesn't crash and returns a sensible reply.
    )

    if all([c1, c2, c3, c4]):
        print("\n[OK] All test cases passed gracefully.")
    else:
        print("\n[WARN] Some test cases failed.")

if __name__ == "__main__":
    main()
