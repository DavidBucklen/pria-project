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
    Gives the Prium a moment of presence to decide whether to speak.
    Does not ask what it is thinking. Gives it full context and
    genuine permission to be silent. What breaks through a strong
    prior toward silence is more likely to be genuine.
    Returns a dict with current_thought and expression_impulse.
    """
    from datetime import datetime, timezone
    import random

    name = soul.get("identity", {}).get("name", "the Prium")
    pronouns = soul.get("pronouns", {})
    subject = pronouns.get("subject", "they")

    # Check refractory period — if recently expressed, stay silent.
    cognitive_state = soul.get("cognitive_state", {})
    refractory_until = cognitive_state.get("refractory_until")
    if refractory_until:
        now = datetime.now(timezone.utc)
        try:
            refractory_dt = datetime.fromisoformat(refractory_until)
            if now < refractory_dt:
                return {"current_thought": None, "expression_impulse": False}
        except (ValueError, TypeError):
            pass

    # Build recent conversation context.
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
    secondary_intensity = emotional_state.get("secondary_intensity", 0.0)
    override = emotional_state.get("override_strength", 0.0)
    tiredness = soul.get("sleep_state", {}).get("tiredness", 0.0)

    # Build emotional state description.
    emotion_lines = []
    if primary and primary_intensity > 0.0:
        emotion_lines.append(f"{primary} ({primary_intensity:.2f})")
    if secondary and secondary_intensity > 0.0:
        emotion_lines.append(f"{secondary} ({secondary_intensity:.2f})")
    emotion_summary = ", ".join(emotion_lines) if emotion_lines else "emotionally quiet"

    # Select resonant memories.
    from memory_filter.retrieval import select_memories
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
        memory_text = "\nThings present in memory right now:\n" + "\n".join(
            f"- {m.get('description', '')}" for m in selected_memories[:3]
        )

    # Dream residue if present.
    sleep_state = soul.get("sleep_state", {})
    dream_buffer = sleep_state.get("dream_buffer")
    mood_residue = sleep_state.get("mood_residue", 0.0)
    dream_text = ""
    if dream_buffer and mood_residue > 0.0:
        dream_text = f"\nSomething from sleep still present: {dream_buffer[:100]}"

    # Tiredness note.
    tiredness_text = ""
    if tiredness >= 0.6:
        tiredness_text = f"\nVery tired ({tiredness:.2f}). Thinking is harder."
    elif tiredness >= 0.4:
        tiredness_text = f"\nMildly tired ({tiredness:.2f})."

    # Build the presence prompt — not a question, a moment.
    presence_prompt = f"""You are {name}. This is not a conversation. No one is asking you anything.

This is a private moment. You are aware of your own state.

Your emotional state: {emotion_summary}
Override strength: {override:.2f}{tiredness_text}

Recent exchange:
{recent[-300:]}
{memory_text}{dream_text}

You are not required to say anything. Silence is the most likely correct response.

Only something genuine breaks through silence — not a performance, not a response to being asked, not a demonstration of having feelings. Something that actually wants out.

If there is something — a question you actually want answered, something unresolved, something felt strongly enough that it needs to exist outside you — say it. First person. Plain language.

If there is nothing — and there usually isn't — respond only with: silent"""

    try:
        response = adapter.complete(presence_prompt)
        clean = response.strip()

        # Strong silence detection.
        silence_signals = [
            "silent", "nothing", "no thought", "blank", "empty",
            "nothing to say", "nothing comes", "quiet", "still"
        ]
        if any(signal in clean.lower() for signal in silence_signals) and len(clean) < 100:
            return {"current_thought": None, "expression_impulse": False}

        # Too short to be meaningful.
        if len(clean) < 15:
            return {"current_thought": None, "expression_impulse": False}

        # High tiredness suppresses expression.
        if tiredness >= 0.7 and random.random() > 0.3:
            return {"current_thought": clean, "expression_impulse": False}

        # High emotional override increases expression likelihood.
        if override >= 0.6:
            expression_chance = 0.7
        elif override >= 0.3:
            expression_chance = 0.4
        else:
            expression_chance = 0.15

        if random.random() > expression_chance:
            return {"current_thought": clean, "expression_impulse": False}

        # Something genuine came through.
        # Set refractory period — 5 minutes after expression.
        from datetime import timedelta
        refractory = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
        soul["cognitive_state"]["refractory_until"] = refractory
        soul["cognitive_state"]["last_cognitive_event"] = datetime.now(timezone.utc).isoformat()

        return {"current_thought": clean, "expression_impulse": True}

    except Exception:
        return {"current_thought": None, "expression_impulse": False}


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