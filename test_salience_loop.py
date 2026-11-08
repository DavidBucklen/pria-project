# The Pria Project
# Salience Loop Test — test_salience_loop.py
# Runs simulated exchanges through the real engine, retrieval and context
# functions (no model call) to check the salience / valence /
# memory-resonance loop: it should rise on strong exchanges, fall when
# input goes quiet, and never lock itself high.

import sys
sys.path.append("C:\\pria")

from emotional_engine.engine import (
    empty_state, trigger, decay, apply_appraisal,
    SALIENCE_CEILING, FEEDBACK_CAP,
)
from context import assemble

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


def make_soul() -> dict:
    """Three memories that resonate with 'warm companion memory' input."""
    memories = []
    for i in range(3):
        memories.append({
            "description": f"Memory {i}",
            "importance": 0.5,
            "sharpness": 0.5,
            "emotional_context": {"primary_emotion": "contentment"},
            "sensory_tags": ["warm", "quiet"],
            "topic_tags": ["companion", "memory"],
            "triggers": [],
            "timestamp": "2026-01-01T00:00:00+00:00",
        })
    return {
        "identity": {"name": "Test"},
        "character": {},
        "long_term_memories": memories,
        "opinions": [],
    }


def run_turn(state, soul, text, triggers):
    """One exchange in the same order demiurge.py uses."""
    state = decay(state)
    assemble(soul, state, [], text, mode="chat")
    for emotion, intensity in triggers:
        state = trigger(state, emotion, intensity)
    state = apply_appraisal(state, triggers)
    return state


def row(turn, state):
    print(f"    turn {turn:2d}  salience {state['salience']:.3f}  "
          f"valence {state['valence']:+.3f}  "
          f"resonance {state['memory_resonance']:.3f}")


print("\n─── PRIA SALIENCE LOOP TEST ────────────────────────────────────\n")

soul = make_soul()
state = empty_state()
turn = 0

# Phase A — five strong, positive exchanges with resonant input.
print("A. Five strong positive exchanges")
strong = [("joy", 0.2), ("curiosity", 0.2)]
saliences = []
for _ in range(5):
    turn += 1
    state = run_turn(state, soul, "warm companion memory", strong)
    saliences.append(state["salience"])
    row(turn, state)

check("Salience rose above 0.5", state["salience"] > 0.5)
check("Salience never exceeded the ceiling",
      max(saliences) <= SALIENCE_CEILING)
check("Valence is positive", state["valence"] > 0.0)
check("Memory resonance is non-zero (memories surfaced)",
      state["memory_resonance"] > 0.0)

# Phase B — twelve quiet exchanges, input still resonates with memories.
print("\nB. Forty quiet exchanges, input still resonant (every 5th shown)")
peak = state["salience"]
b_saliences = []
for _ in range(40):
    turn += 1
    state = run_turn(state, soul, "warm companion memory", [])
    b_saliences.append(state["salience"])
    if turn % 5 == 0:
        row(turn, state)

check("Salience fell well below its peak", state["salience"] < peak * 0.3)
check("Salience settled no higher than the feedback cap",
      state["salience"] <= FEEDBACK_CAP + 0.001)
check("Salience did not rise at any point during quiet turns",
      all(b_saliences[i] <= b_saliences[i - 1] + 0.001
          for i in range(1, len(b_saliences))))

# Phase C — six quiet exchanges, input that resonates with nothing.
print("\nC. Twelve quiet exchanges, nothing resonant")
for _ in range(12):
    turn += 1
    state = run_turn(state, soul, "zzz", [])
    row(turn, state)

check("Memory resonance is zero", state["memory_resonance"] == 0.0)
check("Salience is zero", state["salience"] == 0.0)
check("Valence has drifted close to neutral", abs(state["valence"]) < 0.1)

print(f"\n─── {passed} passed, {failed} failed ───────────────────────────────────\n")
