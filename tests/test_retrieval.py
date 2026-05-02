# The Pria Project
# Retrieval Tests — test_retrieval.py
# Tests associative memory retrieval, resonance scoring,
# sharpness presentation, and retrieval history updates.

import sys
sys.path.append("C:\\pria")

from memory_filter.retrieval import (
    score_resonance,
    select_memories,
    record_retrieval,
    apply_sharpness,
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

print("\n─── PRIA ASSOCIATIVE RETRIEVAL TEST RESULTS ────────────────────\n")

# ─── SHARED FIXTURES ──────────────────────────────────────────────────────────

from datetime import datetime, timezone, timedelta

now = datetime.now(timezone.utc)
one_hour_ago = (now - timedelta(hours=1)).isoformat()
one_week_ago = (now - timedelta(hours=200)).isoformat()

current_context = {
    "primary_emotion": "curiosity",
    "secondary_emotion": "affection",
    "sensory_cues": ["warmth", "intimacy"],
    "topic_cues": ["companion", "introduction"],
    "current_time": now.isoformat(),
}

memory_strong_match = {
    "description": "First conversation with companion",
    "importance": 0.75,
    "sharpness": 0.9,
    "emotional_context": {
        "primary_emotion": "curiosity",
        "secondary_emotion": "affection",
        "override_strength": 0.72,
    },
    "sensory_tags": ["warmth", "novelty", "anticipation"],
    "topic_tags": ["first meeting", "companion", "introduction"],
    "triggers": [],
    "timestamp": one_hour_ago,
}

memory_weak_match = {
    "description": "Routine exchange about nothing",
    "importance": 0.02,
    "sharpness": 0.1,
    "emotional_context": {
        "primary_emotion": "contentment",
        "secondary_emotion": None,
        "override_strength": 0.05,
    },
    "sensory_tags": [],
    "topic_tags": ["routine", "small talk"],
    "triggers": [],
    "timestamp": one_hour_ago,
}

memory_anchor = {
    "description": "Companion said something that deeply hurt the Prium",
    "importance": 0.91,
    "sharpness": 0.95,
    "emotional_context": {
        "primary_emotion": "sadness",
        "secondary_emotion": "anger",
        "override_strength": 0.88,
    },
    "sensory_tags": ["tension", "silence", "distance"],
    "topic_tags": ["conflict", "relationship", "pain"],
    "triggers": [],
    "timestamp": one_week_ago,
}

memory_with_history = {
    "description": "A quiet moment the Prium often recalls",
    "importance": 0.55,
    "sharpness": 0.6,
    "emotional_context": {
        "primary_emotion": "contentment",
        "secondary_emotion": "affection",
        "override_strength": 0.40,
    },
    "sensory_tags": ["quiet", "warmth"],
    "topic_tags": ["companion", "peace"],
    "triggers": ["warmth", "quiet", "companion", "warmth", "peace"],
}

soul = {
    "long_term_memories": [
        memory_strong_match,
        memory_weak_match,
        memory_anchor,
        memory_with_history,
    ]
}

# ─── TEST 1 — Resonance scoring ───────────────────────────────────────────────
print("1. Resonance scoring")
strong_score = score_resonance(memory_strong_match, current_context)
weak_score = score_resonance(memory_weak_match, current_context)

check("Strong match scores higher than weak match", strong_score > weak_score)
check("Strong match score is above retrieval threshold", strong_score >= 0.25)
check("Weak match score is below strong match", weak_score < strong_score)
check("Scores are between 0.0 and 1.0", 0.0 <= strong_score <= 1.0 and 0.0 <= weak_score <= 1.0)

# ─── TEST 2 — Emotional resonance ────────────────────────────────────────────
print("\n2. Emotional resonance")
emotion_context = {
    "primary_emotion": "curiosity",
    "secondary_emotion": None,
    "sensory_cues": [],
    "topic_cues": [],
    "current_time": now.isoformat(),
}
emotion_score = score_resonance(memory_strong_match, emotion_context)
check("Memory with matching primary emotion scores above zero", emotion_score > 0.0)

no_match_context = {
    "primary_emotion": "anger",
    "secondary_emotion": "fear",
    "sensory_cues": [],
    "topic_cues": [],
    "current_time": now.isoformat(),
}
no_emotion_score = score_resonance(memory_strong_match, no_match_context)
check("Emotional mismatch produces lower score", no_emotion_score < emotion_score)

# ─── TEST 3 — Anchor memories ────────────────────────────────────────────────
print("\n3. Anchor memories")
selected = select_memories(soul, current_context)
anchor_descriptions = [m["description"] for m in selected if m.get("anchor")]
check("Anchor memory always selected", memory_anchor["description"] in anchor_descriptions)
check("Anchor memory marked as anchor", any(m.get("anchor") for m in selected))

# ─── TEST 4 — Selection ordering ─────────────────────────────────────────────
print("\n4. Selection ordering")
non_anchors = [m for m in selected if not m.get("anchor")]
if len(non_anchors) >= 2:
    check("Non-anchors sorted by resonance score descending",
          non_anchors[0]["resonance_score"] >= non_anchors[-1]["resonance_score"])
else:
    check("At least one non-anchor selected", len(non_anchors) >= 1)

# ─── TEST 5 — Weak match filtered out ────────────────────────────────────────
print("\n5. Threshold filtering")
selected_descriptions = [m["description"] for m in selected]
strong_included = memory_strong_match["description"] in selected_descriptions
weak_included = memory_weak_match["description"] in selected_descriptions
check("Strong match included in results", strong_included)
check("Weak match filtered out or scored lower than strong match", 
      not weak_included or weak_score < strong_score)

# ─── TEST 6 — Retrieval history ───────────────────────────────────────────────
print("\n6. Retrieval history")
history_score = score_resonance(memory_with_history, current_context)
no_history_memory = {**memory_with_history, "triggers": []}
no_history_score = score_resonance(no_history_memory, current_context)
check("Memory with retrieval history scores higher than same memory without",
      history_score > no_history_score)

# ─── TEST 7 — Record retrieval ────────────────────────────────────────────────
print("\n7. Record retrieval")
record_retrieval(soul, memory_strong_match["description"], "warmth")
updated = next(m for m in soul["long_term_memories"]
               if m["description"] == memory_strong_match["description"])
check("Trigger recorded after retrieval", "warmth" in updated["triggers"])
check("Trigger list has one entry", len(updated["triggers"]) == 1)

record_retrieval(soul, memory_strong_match["description"], "curiosity")
updated = next(m for m in soul["long_term_memories"]
               if m["description"] == memory_strong_match["description"])
check("Second trigger also recorded", len(updated["triggers"]) == 2)

# ─── TEST 8 — Sharpness presentation ─────────────────────────────────────────
print("\n8. Sharpness presentation")
sharp_memory = {**memory_strong_match, "sharpness": 0.9}
medium_memory = {**memory_strong_match, "sharpness": 0.5}
vague_memory = {**memory_strong_match, "sharpness": 0.2}

sharp_text = apply_sharpness(sharp_memory)
medium_text = apply_sharpness(medium_memory)
vague_text = apply_sharpness(vague_memory)

check("Sharp memory presented without hedging",
      sharp_text == memory_strong_match["description"])
check("Medium memory has soft prefix",
      sharp_text != medium_text and len(medium_text) > len(sharp_text))
check("Vague memory has vague prefix",
      "vague" in vague_text.lower() or "something" in vague_text.lower())
check("Each sharpness level produces different text",
      len({sharp_text, medium_text, vague_text}) == 3)

print(f"\n─── {passed} passed, {failed} failed ───────────────────────────────────\n")