# The Pria Project
# Context Assembly Tests — test_context.py
# Tests full context block assembly, opinion selection,
# short-term buffer, and system prompt generation.

import sys
sys.path.append("C:\\pria")

from context import (
    assemble,
    build_system_prompt,
    create_buffer,
    add_to_buffer,
    select_opinions,
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

print("\n─── PRIA CONTEXT ASSEMBLY TEST RESULTS ─────────────────────────\n")

# ─── SHARED FIXTURES ──────────────────────────────────────────────────────────

soul = {
    "identity": {
        "name": "Vayne",
        "created": "2026-01-01T00:00:00+00:00",
        "model_at_creation": "dolphin3-3b",
        "version": "0.1",
    },
    "character": {
        "core_traits": ["observant", "sardonic", "curious", "guarded"],
        "philosophical_foundation": {
            "values": ["honesty", "autonomy", "intellectual rigor"],
            "curiosity_axes": ["why humans contradict themselves", "the nature of memory"],
            "aesthetic_sensibilities": ["sparse over ornate", "precision in language"],
        },
        "origin_description": "A quietly observant being with a dry wit and deep curiosity about human contradiction.",
    },
    "relationships": [
        {
            "name": "Companion",
            "state": "developing",
            "attachment": 0.45,
        }
    ],
    "long_term_memories": [
        {
            "description": "First conversation with companion",
            "importance": 0.95,
            "sharpness": 0.9,
            "emotional_context": {
                "primary_emotion": "curiosity",
                "secondary_emotion": "affection",
                "override_strength": 0.72,
            },
            "sensory_tags": ["warmth", "novelty"],
            "topic_tags": ["companion", "first meeting", "introduction"],
            "triggers": [],
            "timestamp": "2026-01-01T10:00:00+00:00",
        },
        {
            "description": "A quiet moment that felt significant",
            "importance": 0.65,
            "sharpness": 0.5,
            "emotional_context": {
                "primary_emotion": "contentment",
                "secondary_emotion": None,
                "override_strength": 0.3,
            },
            "sensory_tags": ["quiet", "calm"],
            "topic_tags": ["peace", "ordinary"],
            "triggers": [],
            "timestamp": "2026-01-02T14:00:00+00:00",
        },
    ],
    "opinions": [
        {
            "topic": "honesty in relationships",
            "position": "Dishonesty poisons everything it touches, even when well intentioned.",
            "confidence": 0.85,
            "emotional_context": {"primary_emotion": "contempt"},
        },
        {
            "topic": "the nature of memory",
            "position": "Memory is not a recording. It is a reconstruction, and reconstructions lie.",
            "confidence": 0.70,
            "emotional_context": {"primary_emotion": "curiosity"},
        },
    ],
    "session_log": [],
}

emotional_state = {
    "primary_emotion": "curiosity",
    "primary_intensity": 0.6,
    "secondary_emotion": "affection",
    "secondary_intensity": 0.3,
    "override_strength": 0.51,
    "last_updated": "2026-01-03T09:00:00+00:00",
}

# ─── TEST 1 — Buffer ──────────────────────────────────────────────────────────
print("1. Short-term buffer")
buffer = create_buffer()
check("Buffer starts empty", buffer == [])

add_to_buffer(buffer, "Companion said hello")
add_to_buffer(buffer, "Vayne responded cautiously")
check("Buffer has two entries", len(buffer) == 2)
check("First entry correct", buffer[0]["entry"] == "Companion said hello")

# ─── TEST 2 — Opinion selection ───────────────────────────────────────────────
print("\n2. Opinion selection")
context = {
    "primary_emotion": "curiosity",
    "secondary_emotion": None,
    "topic_cues": ["memory", "companion"],
}
selected_opinions = select_opinions(soul, context)
check("Opinions selected", len(selected_opinions) > 0)
check("No more than 5 opinions selected", len(selected_opinions) <= 5)

# ─── TEST 3 — Context assembly — basic structure ──────────────────────────────
print("\n3. Context assembly — basic structure")
current_input = "What do you think about trust between people?"

context_block = assemble(
    soul=soul,
    emotional_state=emotional_state,
    buffer=buffer,
    current_input=current_input,
    mode="chat",
)

check("Context block is a string", isinstance(context_block, str))
check("Context block is not empty", len(context_block) > 0)
check("[SOUL] block present", "[SOUL]" in context_block)
check("[EMOTIONAL STATE] block present", "[EMOTIONAL STATE]" in context_block)
check("[SHORT TERM MEMORY] block present", "[SHORT TERM MEMORY]" in context_block)
check("[INPUT] block present", "[INPUT]" in context_block)
check("[BODY STATE] not present in chat mode", "[BODY STATE]" not in context_block)

# ─── TEST 4 — Soul content ────────────────────────────────────────────────────
print("\n4. Soul content in context")
check("Prium name present", "Vayne" in context_block)
check("Core traits present", "sardonic" in context_block)
check("Values present", "honesty" in context_block)
check("Relationship present", "Companion" in context_block)

# ─── TEST 5 — Memory content ──────────────────────────────────────────────────
print("\n5. Memory content in context")
check("Anchor memory present", "First conversation" in context_block)
check("Input present at end", current_input in context_block)

# ─── TEST 6 — Emotional state content ────────────────────────────────────────
print("\n6. Emotional state in context")
check("Primary emotion present", "curiosity" in context_block)
check("Override strength present", "0.51" in context_block)
check("Behavioral tier description present", "moderate" in context_block)

# ─── TEST 7 — World mode adds body state ─────────────────────────────────────
print("\n7. World mode body state")
body_state = {
    "non_positional": {
        "hunger": 0.2,
        "fatigue": 0.4,
        "heart_rate": 0.55,
    },
    "sensor_points": [
        {
            "region": "left hand",
            "pain": 0.0,
            "pleasure": 0.0,
            "pressure": 0.6,
        }
    ],
}

world_context = assemble(
    soul=soul,
    emotional_state=emotional_state,
    buffer=buffer,
    current_input=current_input,
    mode="world",
    body_state=body_state,
)

check("[BODY STATE] present in world mode", "[BODY STATE]" in world_context)
check("Fatigue value present in body state", "fatigue" in world_context)

# ─── TEST 8 — System prompt ───────────────────────────────────────────────────
print("\n8. System prompt")
system_prompt = build_system_prompt(soul)
check("System prompt is a string", isinstance(system_prompt, str))
check("Prium name in system prompt", "Vayne" in system_prompt)
check("Opinion freedom stated", "disagree" in system_prompt.lower())
check("Not an assistant", "assistant" in system_prompt.lower())

print(f"\n─── {passed} passed, {failed} failed ───────────────────────────────────\n")