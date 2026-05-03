# The Pria Project
# Emotional Evaluator — evaluator.py
# Makes a second model call after each exchange to evaluate
# the emotional impact of what just happened on the Prium.
# Makes a third model call to detect people and relationships.
# Returns emotion triggers and detected people separately.

import json

# ─── CONFIGURATION ────────────────────────────────────────────────────────────

# Maximum intensity any single emotion can be triggered per exchange.
MAX_TRIGGER_INTENSITY = 0.2

# Minimum intensity threshold — below this we ignore the trigger.
MIN_TRIGGER_INTENSITY = 0.05

# Valid emotions the evaluator can trigger.
VALID_EMOTIONS = [
    "joy", "excitement", "anger", "fear", "anxiety",
    "contentment", "sadness", "melancholy", "longing", "resignation",
    "affection", "attachment", "loneliness", "love", "trust", "suspicion",
    "desire", "arousal", "lust", "curiosity", "frustration", "contempt",
    "awe", "unease", "playfulness"
]


# ─── EMOTIONAL EVALUATION ─────────────────────────────────────────────────────

def evaluate_exchange(
    adapter,
    soul: dict,
    human_message: str,
    prium_response: str,
    current_emotional_state: dict,
) -> list:
    """
    Evaluates the emotional impact of a single exchange on the Prium.
    Makes a second model call with a focused prompt.
    Returns a list of (emotion, intensity) tuples to trigger.
    """

    name = soul.get("identity", {}).get("name", "the Prium")
    traits = soul.get("character", {}).get("core_traits", [])
    foundation = soul.get("character", {}).get("philosophical_foundation", {})
    values = foundation.get("values", [])
    repulsions = foundation.get("repulsions", [])

    current_primary = current_emotional_state.get("primary_emotion", "none")
    current_override = current_emotional_state.get("override_strength", 0.0)

    evaluation_prompt = f"""You are evaluating the emotional impact of a conversation exchange on a specific individual named {name}.

{name}'s character:
Traits: {', '.join(traits)}
Values: {', '.join(values)}
Things they find distasteful: {', '.join(repulsions)}
Current emotional state: {current_primary} at override strength {current_override:.2f}

The exchange that just occurred:
Human said: {human_message}
{name} responded: {prium_response}

Based on {name}'s specific character and values, evaluate what emotional impact this exchange had on them.
Consider: Did anything said resonate with their values or violate them? Did anything trigger curiosity, discomfort, warmth, or unease specific to who they are?

Respond in JSON only. No other text. No markdown. No explanation.
Return only emotions that were genuinely triggered. Return an empty list if nothing significant happened.
Maximum 3 emotions per exchange. Intensity between 0.05 and 0.40.

Format:
[
  {{"emotion": "emotion_name", "intensity": 0.00}},
  {{"emotion": "emotion_name", "intensity": 0.00}}
]"""

    try:
        response = adapter.complete(evaluation_prompt)
        clean = _clean_json(response)
        triggers = json.loads(clean)

        valid_triggers = []
        for item in triggers:
            if not isinstance(item, dict):
                continue
            emotion = item.get("emotion", "").lower().strip()
            intensity = float(item.get("intensity", 0.0))
            if emotion in VALID_EMOTIONS:
                intensity = max(MIN_TRIGGER_INTENSITY, min(MAX_TRIGGER_INTENSITY, intensity))
                valid_triggers.append((emotion, intensity))

        return valid_triggers[:3]

    except (json.JSONDecodeError, ValueError, TypeError):
        return []


# ─── PERSON DETECTION ─────────────────────────────────────────────────────────

def detect_people(
    adapter,
    soul: dict,
    human_message: str,
    prium_response: str,
) -> list:
    """
    Detects people mentioned in the exchange using rule-based extraction.
    Watches for names following relationship words and standalone names.
    Returns a list of person dictionaries ready to be written to the soul file.
    """
    import re

    # Build list of already known people.
    known_names = [
        (p.get("real_name") or p.get("name", "")).lower()
        for p in soul.get("people", [])
    ]

    # Relationship words that indicate a person reference.
    relationship_words = [
        "son", "daughter", "wife", "husband", "partner", "girlfriend",
        "boyfriend", "mother", "father", "mom", "dad", "brother", "sister",
        "friend", "boss", "coworker", "colleague", "neighbor", "uncle",
        "aunt", "grandson", "granddaughter", "grandfather", "grandmother",
    ]

    combined_text = f"{human_message} {prium_response}"
    words = combined_text.split()
    detected = []
    found_names = set()

    # Pattern 1 — "my son Jake" or "my wife Sarah"
    for rel in relationship_words:
        pattern = rf'\bmy\s+{rel}\s+([A-Z][a-z]+)\b'
        matches = re.findall(pattern, combined_text)
        for match in matches:
            if match.lower() not in known_names and match.lower() not in found_names:
                found_names.add(match.lower())
                detected.append({
                    "name": match,
                    "relationship_to_companion": rel,
                    "relationship_type": "human",
                    "confidence": 0.9,
                    "new": True,
                })

    # Pattern 2 — "his name is Jake" or "her name is Sarah"
    name_pattern = r'\b(?:his|her|their|my)\s+name\s+is\s+([A-Z][a-z]+)\b'
    matches = re.findall(name_pattern, combined_text)
    for match in matches:
        if match.lower() not in known_names and match.lower() not in found_names:
            found_names.add(match.lower())
            # Try to find relationship context nearby.
            rel = "unknown"
            for r in relationship_words:
                if r in combined_text.lower():
                    rel = r
                    break
            detected.append({
                "name": match,
                "relationship_to_companion": rel,
                "relationship_type": "human",
                "confidence": 0.85,
                "new": True,
            })

    # Pattern 3 — unnamed relationship references "my son", "my wife"
    for rel in relationship_words:
        pattern = rf'\bmy\s+{rel}\b'
        if re.search(pattern, combined_text, re.IGNORECASE):
            placeholder = f"companion's {rel}"
            if placeholder.lower() not in known_names and placeholder.lower() not in found_names:
                found_names.add(placeholder.lower())
                detected.append({
                    "name": placeholder,
                    "relationship_to_companion": rel,
                    "relationship_type": "human",
                    "confidence": 0.7,
                    "new": True,
                })

    return detected

# ─── INNER MONOLOGUE ──────────────────────────────────────────────────────────

def inner_monologue(
    adapter,
    soul: dict,
    emotional_state: dict,
    buffer: list,
    depth: str = "shallow",
) -> dict:
    """
    Runs a private inner monologue for the Prium.
    Produces a genuine internal thought based on current state.
    Returns a dict with current_thought and expression_impulse.

    depth — 'shallow' for post-exchange thoughts (fast, lightweight)
             'deep' for sustained silence thoughts (fuller, more reflective)
    """
    name = soul.get("identity", {}).get("name", "the Prium")

    # Build recent conversation context from buffer.
    recent = ""
    if buffer:
        recent_entries = [item["entry"] for item in buffer[-6:]]
        recent = "\n".join(recent_entries)
    else:
        recent = "No recent conversation."

    # Current emotional state summary.
    primary = emotional_state.get("primary_emotion", "none")
    primary_intensity = emotional_state.get("primary_intensity", 0.0)
    secondary = emotional_state.get("secondary_emotion")
    override = emotional_state.get("override_strength", 0.0)

    emotion_summary = f"{primary} ({primary_intensity:.2f})"
    if secondary:
        emotion_summary += f", {secondary}"

    # Select memories that resonate with current context.
    from memory_filter.retrieval import select_memories
    from datetime import datetime, timezone
    retrieval_context = {
        "primary_emotion": primary,
        "secondary_emotion": secondary,
        "sensory_cues": [],
        "topic_cues": [],
        "current_time": datetime.now(timezone.utc).isoformat(),
    }
    selected_memories = select_memories(soul, retrieval_context)
    memory_text = ""
    if selected_memories:
        memory_text = "\nThings you remember:\n" + "\n".join(
            f"- {m.get('description', '')}" for m in selected_memories[:3]
        )

    if depth == "shallow":
        monologue_prompt = f"""You are {name}. Speak only as yourself. Use I, not "{name}".

Feeling: {emotion_summary}
Recent: {recent[-200:]}

One sentence. First person. What is on your mind right now?
Example: "I keep thinking about..." or "Something feels unresolved..."
If nothing: silent"""

    else:
        monologue_prompt = f"""You are {name}. Speak only as yourself. Use I, not "{name}".

Feeling: {emotion_summary}
Recent: {recent[-200:]}
{memory_text}

Two sentences maximum. First person only. What genuinely wants to be said?
Example: "I've been thinking about..." or "I notice that..."
If nothing genuinely wants to be expressed: silent"""

    try:
        response = adapter.complete(monologue_prompt)
        clean = response.strip()

        # Check if the Prium chose silence.
        if "silent" in clean.lower() and len(clean) < 60:
            return {
                "current_thought": None,
                "expression_impulse": False,
            }

        # Something genuine came through.
        return {
            "current_thought": clean,
            "expression_impulse": True,
        }

    except Exception:
        return {
            "current_thought": None,
            "expression_impulse": False,
        }


# ─── INTERNAL HELPERS ─────────────────────────────────────────────────────────

def _clean_json(response: str) -> str:
    """
    Strips markdown code fences from model response if present.
    Returns clean JSON string ready for parsing.
    """
    clean = response.strip()
    if clean.startswith("```"):
        lines = clean.split("\n")
        clean = "\n".join(lines[1:])
    if clean.endswith("```"):
        clean = "\n".join(clean.split("\n")[:-1])
    return clean.strip()