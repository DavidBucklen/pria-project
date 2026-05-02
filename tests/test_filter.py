# The Pria Project
# Memory Filter Tests — test_filter.py
# Synthetic experience events to verify filter behavior.
# Each event has an expected outcome. We check if the filter agrees.

import sys
sys.path.append("C:\\pria")

from memory_filter.filter import filter_buffer

# ─── SYNTHETIC EVENTS ─────────────────────────────────────────────────────────

events = [
    {
        "description": "First conversation between Prium and companion",
        "identity_shaping":    True,
        "first_occurrence":    True,
        "relationship_change": True,
        "emotional_intensity": 0.8,
        "threshold_crossing":  False,
        "expected_persist":    True,
    },
    {
        "description": "Companion asks what the weather is like",
        "identity_shaping":    False,
        "first_occurrence":    False,
        "relationship_change": False,
        "emotional_intensity": 0.0,
        "threshold_crossing":  False,
        "expected_persist":    False,
    },
    {
        "description": "Companion says something that genuinely hurts the Prium",
        "identity_shaping":    False,
        "first_occurrence":    True,
        "relationship_change": True,
        "emotional_intensity": 0.9,
        "threshold_crossing":  True,
        "expected_persist":    True,
    },
    {
        "description": "Companion disappears for three days then returns",
        "identity_shaping":    False,
        "first_occurrence":    True,
        "relationship_change": True,
        "emotional_intensity": 0.6,
        "threshold_crossing":  False,
        "expected_persist":    True,
    },
    {
        "description": "Prium forms a strong opinion about something for the first time",
        "identity_shaping":    True,
        "first_occurrence":    True,
        "relationship_change": False,
        "emotional_intensity": 0.5,
        "threshold_crossing":  False,
        "expected_persist":    True,
    },
    {
        "description": "Routine exchange about nothing in particular",
        "identity_shaping":    False,
        "first_occurrence":    False,
        "relationship_change": False,
        "emotional_intensity": 0.1,
        "threshold_crossing":  False,
        "expected_persist":    False,
    },
    {
        "description": "Companion shares something deeply personal for the first time",
        "identity_shaping":    False,
        "first_occurrence":    True,
        "relationship_change": True,
        "emotional_intensity": 0.7,
        "threshold_crossing":  False,
        "expected_persist":    True,
    },
    {
        "description": "Prium makes a decision that goes against its own values",
        "identity_shaping":    True,
        "first_occurrence":    True,
        "relationship_change": False,
        "emotional_intensity": 0.8,
        "threshold_crossing":  True,
        "expected_persist":    True,
    },
]


# ─── RUN TESTS ────────────────────────────────────────────────────────────────

results = filter_buffer(events)

passed = 0
failed = 0

print("\n─── PRIA MEMORY FILTER TEST RESULTS ───────────────────────────\n")

for i, (event, result) in enumerate(zip(events, results)):
    expected = event["expected_persist"]
    actual = result["persist"]
    status = "PASS" if expected == actual else "FAIL"

    if status == "PASS":
        passed += 1
    else:
        failed += 1

    print(f"[{status}] Event {i + 1}: {result['description']}")
    print(f"       Score: {result['score']}  |  Persist: {result['persist']}  |  Immediate Write: {result['immediate_write']}")
    if status == "FAIL":
        print(f"       Expected persist: {expected}  —  got: {actual}")
    print()

print(f"─── {passed} passed, {failed} failed ───────────────────────────────────\n")