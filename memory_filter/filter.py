# The Pria Project
# Memory Filter — filter.py
# Evaluates experience events and assigns importance scores.
# Events above the persistence threshold are written to long-term memory.

# ─── CONFIGURATION ────────────────────────────────────────────────────────────

# Criterion weights — how much each factor contributes to importance score.
# These are initial estimates. Tune based on test results.
WEIGHTS = {
    "identity_shaping":      0.35,
    "first_occurrence":      0.25,
    "relationship_change":   0.25,
    "emotional_intensity":   0.50,
    "threshold_crossing":    0.15,
}

# Events with importance score at or above this value are kept long-term.
PERSISTENCE_THRESHOLD = 0.25

# Events with importance score at or above this value trigger an immediate
# soul file write mid-session.
IMMEDIATE_WRITE_THRESHOLD = 0.85


# ─── SCORING ──────────────────────────────────────────────────────────────────

def score_event(event: dict) -> float:
    """
    Takes an experience event and returns an importance score between 0.0 and 1.0.

    An event is a dictionary with the following fields:
        identity_shaping    (bool)  — does this define or shift who the Prium is?
        first_occurrence    (bool)  — is this the first time this type of thing has happened?
        relationship_change (bool)  — does this alter the state of a relationship?
        emotional_intensity (float) — how emotionally intense is this event? (0.0 to 1.0)
        threshold_crossing  (bool)  — does this push override strength across a tier boundary?
        description         (str)   — human readable description of the event (for logging)
    """

    score = 0.0

    if event.get("identity_shaping"):
        score += WEIGHTS["identity_shaping"]

    if event.get("first_occurrence"):
        score += WEIGHTS["first_occurrence"]

    if event.get("relationship_change"):
        score += WEIGHTS["relationship_change"]

    # Emotional intensity is a float so it scales the weight rather than triggering it fully.
    intensity = event.get("emotional_intensity", 0.0)
    score += WEIGHTS["emotional_intensity"] * intensity

    if event.get("threshold_crossing"):
        score += WEIGHTS["threshold_crossing"]

    # Clamp to 1.0 maximum.
    return min(score, 1.0)


# ─── FILTER DECISION ──────────────────────────────────────────────────────────

def filter_event(event: dict) -> dict:
    """
    Scores an event and returns a result dictionary containing:
        score           (float) — the importance score
        persist         (bool)  — whether this event should go to long-term memory
        immediate_write (bool)  — whether this event should trigger an immediate soul file write
        description     (str)   — passed through from the event for logging
    """

    score = score_event(event)

    return {
        "description":     event.get("description", "no description"),
        "score":           round(score, 3),
        "persist":         score >= PERSISTENCE_THRESHOLD,
        "immediate_write": score >= IMMEDIATE_WRITE_THRESHOLD,
    }


# ─── BATCH FILTER ─────────────────────────────────────────────────────────────

def filter_buffer(events: list) -> list:
    """
    Runs filter_event on a list of events.
    Returns a list of result dictionaries in the same order.
    """
    return [filter_event(event) for event in events]