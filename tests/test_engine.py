# The Pria Project
# Emotional Engine Tests — test_engine.py
# Tests emotion triggering, decay, override tiers, and soul file integration.

import sys
sys.path.append("C:\\pria")

from emotional_engine.engine import (
    empty_state,
    trigger,
    decay,
    get_override_tier,
    state_to_snapshot,
    load_from_snapshot,
)

passed = 0
failed = 0

def check(label: str, condition: bool):
    global passed, failed
    if condition:
        print(f"  [PASS] {label}")
        passed += 1
    else:
        print(f"  [FAIL] {label}")
        failed += 1

print("\n─── PRIA EMOTIONAL ENGINE TEST RESULTS ─────────────────────────\n")

# Test 1 — Empty state
print("1. Empty state")
state = empty_state()
check("All emotions start at zero", all(v == 0.0 for v in state["intensities"].values()))
check("Primary emotion is None", state["primary_emotion"] is None)
check("Secondary emotion is None", state["secondary_emotion"] is None)
check("Override strength is zero", state["override_strength"] == 0.0)

# Test 2 — Triggering a single emotion
print("\n2. Triggering emotions")
state = trigger(state, "curiosity", 0.6)
check("Curiosity set to 0.6", state["intensities"]["curiosity"] == 0.6)
check("Primary emotion is curiosity", state["primary_emotion"] == "curiosity")
check("Primary intensity is 0.6", state["primary_intensity"] == 0.6)
check("Secondary emotion is None — only one active", state["secondary_emotion"] is None)

# Test 3 — Triggering a second emotion
print("\n3. Co-dominant emotions")
state = trigger(state, "melancholy", 0.5)
check("Melancholy set to 0.5", state["intensities"]["melancholy"] == 0.5)
check("Primary is still curiosity", state["primary_emotion"] == "curiosity")
check("Secondary is now melancholy", state["secondary_emotion"] == "melancholy")
check("Secondary intensity is 0.5", state["secondary_intensity"] == 0.5)

# Test 4 — Override strength calculation
print("\n4. Override strength")
# curiosity 0.6 * 0.7 + melancholy 0.5 * 0.3 = 0.42 + 0.15 = 0.57
check("Override strength calculated correctly", state["override_strength"] == 0.57)
tier = get_override_tier(state)
check("Override tier is moderate", "moderate" in tier)

# Test 5 — High override strength
print("\n5. High override strength")
state2 = empty_state()
state2 = trigger(state2, "love", 0.95)
state2 = trigger(state2, "longing", 0.8)
check("Override strength above 0.75", state2["override_strength"] >= 0.75)
tier2 = get_override_tier(state2)
check("Override tier is strong or heavily impaired", 
      "strong" in tier2 or "heavily" in tier2)

# Test 6 — Emotion stacking
print("\n6. Emotion stacking")
state3 = empty_state()
state3 = trigger(state3, "joy", 0.4)
state3 = trigger(state3, "joy", 0.4)
check("Joy stacks to 0.8", state3["intensities"]["joy"] == 0.8)

# Test 7 — Clamping at 1.0
print("\n7. Clamping")
state3 = trigger(state3, "joy", 0.5)
check("Joy clamped at 1.0 after overflow", state3["intensities"]["joy"] == 1.0)

# Test 8 — Decay
print("\n8. Decay")
state4 = empty_state()
state4 = trigger(state4, "anger", 0.8)
before = state4["intensities"]["anger"]
state4 = decay(state4)
after = state4["intensities"]["anger"]
check("Anger decays after one cycle", after < before)
check("Anger does not go below zero", after >= 0.0)

# Test 9 — Fast vs slow decay
print("\n9. Decay rate differences")
state5 = empty_state()
state5 = trigger(state5, "anger", 0.5)
state5 = trigger(state5, "melancholy", 0.5)
state5 = decay(state5)
check("Anger decays faster than melancholy",
      state5["intensities"]["anger"] < state5["intensities"]["melancholy"])

# Test 10 — Snapshot and restore
print("\n10. Snapshot and restore")
state6 = empty_state()
state6 = trigger(state6, "attachment", 0.7)
state6 = trigger(state6, "curiosity", 0.4)
snapshot = state_to_snapshot(state6)
check("Snapshot has primary emotion", snapshot["primary_emotion"] == "attachment")
check("Snapshot strips zero emotions", len(snapshot["active_intensities"]) == 2)

restored = load_from_snapshot(snapshot)
check("Restored primary matches original", restored["primary_emotion"] == "attachment")
check("Restored intensity matches original", 
      restored["intensities"]["attachment"] == 0.7)

# Test 11 — Unknown emotion raises error
print("\n11. Error handling")
try:
    state = trigger(state, "schadenfreude", 0.5)
    check("Unknown emotion should have raised error", False)
except ValueError:
    check("Unknown emotion raises ValueError", True)

print(f"\n─── {passed} passed, {failed} failed ───────────────────────────────────\n")