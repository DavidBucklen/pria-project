# The Pria Project
# Observation Log — observe_log.py
# Appends one JSON line per exchange to observe_log.jsonl.
# Read by observe.py (dashboard) and later by the training data logger.
# A logging failure must never interrupt a conversation.

import json
from datetime import datetime, timezone

from emotional_engine.engine import get_tiredness_tier

LOG_PATH = "observe_log.jsonl"
TEXT_LIMIT = 300  # characters kept of each message


def log_turn(
    soul: dict,
    emotional_state: dict,
    tiredness: float,
    triggers: list,
    gen_params: dict,
    human_message: str = "",
    response: str = "",
):
    """
    Writes one record describing the state after an exchange.
    Call after triggers, appraisal and tiredness have been applied.
    """
    try:
        intensities = {
            emotion: value
            for emotion, value in emotional_state.get("intensities", {}).items()
            if value > 0.0
        }

        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "name": soul.get("identity", {}).get("name"),
            "primary_emotion": emotional_state.get("primary_emotion"),
            "primary_intensity": emotional_state.get("primary_intensity", 0.0),
            "secondary_emotion": emotional_state.get("secondary_emotion"),
            "secondary_intensity": emotional_state.get("secondary_intensity", 0.0),
            "override_strength": emotional_state.get("override_strength", 0.0),
            "salience": emotional_state.get("salience", 0.0),
            "valence": emotional_state.get("valence", 0.0),
            "memory_resonance": emotional_state.get("memory_resonance", 0.0),
            "active_intensities": intensities,
            "tiredness": tiredness,
            "tiredness_tier": get_tiredness_tier(tiredness),
            "triggers": [list(t) for t in triggers],
            "gen_params": gen_params,
            "refractory_until": soul.get("cognitive_state", {}).get("refractory_until"),
            "human_message": human_message[:TEXT_LIMIT],
            "response": response[:TEXT_LIMIT],
        }

        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    except Exception as e:
        print(f"[OBSERVE] Log write failed: {e}")