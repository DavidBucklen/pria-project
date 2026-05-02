# The Pria Project
# Emotional Evaluator — evaluator.py
# Makes a second model call after each exchange to evaluate
# the emotional impact of what just happened on the Prium.
# Returns emotion triggers that feed into the emotional engine.
# This is approach 2 — model based emotional evaluation.
# The emotional response emerges from genuine interpretation
# rather than keyword rules.

import json

# ─── CONFIGURATION ────────────────────────────────────────────────────────────

# Maximum intensity any single emotion can be triggered per exchange.
MAX_TRIGGER_INTENSITY = 0.4

# Minimum intensity threshold — below this we ignore the trigger.
MIN_TRIGGER_INTENSITY = 0.05


# ─── EVALUATION ───────────────────────────────────────────────────────────────

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

Valid emotions: joy, excitement, anger, fear, anxiety, contentment, sadness, melancholy, longing, resignation, affection, attachment, loneliness, love, trust, suspicion, desire, arousal, lust, curiosity, frustration, contempt, awe, unease, playfulness

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
        clean = response.strip()

        # Strip markdown if present.
        if clean.startswith("```"):
            lines = clean.split("\n")
            clean = "\n".join(lines[1:])
        if clean.endswith("```"):
            clean = "\n".join(clean.split("\n")[:-1])
        clean = clean.strip()

        triggers = json.loads(clean)

        # Validate and clean the results.
        valid_triggers = []
        valid_emotions = [
            "joy", "excitement", "anger", "fear", "anxiety",
            "contentment", "sadness", "melancholy", "longing", "resignation",
            "affection", "attachment", "loneliness", "love", "trust", "suspicion",
            "desire", "arousal", "lust", "curiosity", "frustration", "contempt",
            "awe", "unease", "playfulness"
        ]

        for item in triggers:
            emotion = item.get("emotion", "").lower().strip()
            intensity = float(item.get("intensity", 0.0))

            if emotion in valid_emotions:
                intensity = max(MIN_TRIGGER_INTENSITY, min(MAX_TRIGGER_INTENSITY, intensity))
                valid_triggers.append((emotion, intensity))

        return valid_triggers[:3]

    except (json.JSONDecodeError, ValueError, TypeError):
        # If evaluation fails for any reason return empty — don't crash.
        return []