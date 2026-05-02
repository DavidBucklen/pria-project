# The Pria Project
# Associative Memory Retrieval — retrieval.py
# Selects memories from the soul file based on resonance with current context.
# Retrieval is associative — memories surface by emotional, sensory, tonal,
# and semantic resonance rather than by importance score ranking alone.

# ─── CONFIGURATION ────────────────────────────────────────────────────────────

# Memories with importance >= this value always surface regardless of resonance.
ANCHOR_THRESHOLD = 0.85

# Memories with resonance score >= this value are included in context.
# Tunable — initial value to be calibrated during testing.
RESONANCE_THRESHOLD = 0.15

# Weights for each resonance signal.
RESONANCE_WEIGHTS = {
    "emotional_match":   0.30,
    "sensory_match":     0.25,
    "topic_match":       0.25,
    "recency":           0.10,
    "retrieval_history": 0.10,
}


# ─── RESONANCE SCORING ────────────────────────────────────────────────────────

def score_resonance(memory: dict, context: dict) -> float:
    """
    Scores a single memory against current context for associative resonance.

    context is a dictionary with the following fields:
        primary_emotion     (str)   — current primary emotion
        secondary_emotion   (str)   — current secondary emotion or None
        sensory_cues        (list)  — sensory and tonal elements in current input
        topic_cues          (list)  — semantic topic elements in current input
        session_start       (str)   — ISO timestamp of session start (for recency)
        current_time        (str)   — ISO timestamp of now (for recency)

    Returns a resonance score between 0.0 and 1.0.
    """
    score = 0.0

    # ── Emotional match ──────────────────────────────────────────────────────
    # Does the memory's emotional context match the current emotional state?
    mem_emotion = memory.get("emotional_context", {})
    mem_primary = mem_emotion.get("primary_emotion")
    mem_secondary = mem_emotion.get("secondary_emotion")
    current_primary = context.get("primary_emotion")
    current_secondary = context.get("secondary_emotion")

    emotional_score = 0.0
    if mem_primary and current_primary:
        if mem_primary == current_primary:
            emotional_score += 0.7
        elif mem_primary == current_secondary:
            emotional_score += 0.3
    if mem_secondary and current_secondary:
        if mem_secondary == current_secondary:
            emotional_score += 0.3
        elif mem_secondary == current_primary:
            emotional_score += 0.1

    score += RESONANCE_WEIGHTS["emotional_match"] * min(emotional_score, 1.0)

    # ── Sensory match ────────────────────────────────────────────────────────
    # Do the memory's sensory tags resonate with current sensory cues?
    mem_sensory = set(memory.get("sensory_tags", []))
    current_sensory = set(context.get("sensory_cues", []))

    if mem_sensory and current_sensory:
        overlap = len(mem_sensory & current_sensory)
        sensory_score = overlap / max(len(mem_sensory), len(current_sensory))
        score += RESONANCE_WEIGHTS["sensory_match"] * sensory_score
    
    # ── Topic match ──────────────────────────────────────────────────────────
    # Do the memory's topic tags match current topic cues?
    mem_topics = set(memory.get("topic_tags", []))
    current_topics = set(context.get("topic_cues", []))

    if mem_topics and current_topics:
        overlap = len(mem_topics & current_topics)
        topic_score = overlap / max(len(mem_topics), len(current_topics))
        score += RESONANCE_WEIGHTS["topic_match"] * topic_score

    # ── Recency ──────────────────────────────────────────────────────────────
    # More recent memories have a natural retrieval advantage.
    # Advantage decays over time, modulated by sharpness.
    from datetime import datetime, timezone

    try:
        mem_time = datetime.fromisoformat(memory.get("timestamp", ""))
        current_time_str = context.get("current_time", "")
        if current_time_str:
            now = datetime.fromisoformat(current_time_str)
            age_hours = max(0, (now - mem_time).total_seconds() / 3600)
            # Recency score decays from 1.0 toward 0.0 over 168 hours (one week).
            # Sharpness slows this decay — vivid memories stay accessible longer.
            sharpness = memory.get("sharpness", 0.0)
            decay_rate = 168 * (1 + sharpness)
            recency_score = max(0.0, 1.0 - (age_hours / decay_rate))
            score += RESONANCE_WEIGHTS["recency"] * recency_score
    except (ValueError, TypeError):
        pass

    # ── Retrieval history ────────────────────────────────────────────────────
    # Memories retrieved frequently become more accessible over time.
    triggers = memory.get("triggers", [])
    if triggers:
        # Each previous retrieval adds a small bonus, capped at 1.0.
        history_score = min(1.0, len(triggers) * 0.15)
        score += RESONANCE_WEIGHTS["retrieval_history"] * history_score

    return round(min(score, 1.0), 3)


# ─── MEMORY SELECTION ─────────────────────────────────────────────────────────

def select_memories(soul: dict, context: dict) -> list:
    """
    Selects memories from the soul file for inclusion in context assembly.

    Returns a list of memory dictionaries, each with an added
    'resonance_score' field indicating why it was selected.

    Memories are returned in order: anchors first, then by resonance score.
    Guarantees at least 3 recent memories are always surfaced.
    """
    MINIMUM_RECENT_MEMORIES = 3

    memories = soul.get("long_term_memories", [])
    anchors = []
    candidates = []
    anchor_descriptions = set()

    for memory in memories:
        importance = memory.get("importance", 0.0)
        if importance >= ANCHOR_THRESHOLD:
            anchors.append({**memory, "resonance_score": 1.0, "anchor": True})
            anchor_descriptions.add(memory.get("description", ""))
        else:
            resonance = score_resonance(memory, context)
            if resonance >= RESONANCE_THRESHOLD:
                candidates.append({**memory, "resonance_score": resonance, "anchor": False})

    # Sort candidates by resonance score descending.
    candidates.sort(key=lambda m: m["resonance_score"], reverse=True)

    # Always surface at least MINIMUM_RECENT_MEMORIES memories.
    # If resonance retrieval came up short, fill with most recent memories.
    selected_descriptions = (
        anchor_descriptions | {m.get("description", "") for m in candidates}
    )

    if len(candidates) < MINIMUM_RECENT_MEMORIES:
        non_anchors = [
            m for m in memories
            if m.get("importance", 0.0) < ANCHOR_THRESHOLD
            and m.get("description", "") not in selected_descriptions
        ]
        non_anchors.sort(key=lambda m: m.get("timestamp", ""), reverse=True)

        needed = MINIMUM_RECENT_MEMORIES - len(candidates)
        for memory in non_anchors[:needed]:
            candidates.append({
                **memory,
                "resonance_score": 0.0,
                "anchor": False,
            })

    return anchors + candidates


# ─── RETRIEVAL UPDATE ─────────────────────────────────────────────────────────

def record_retrieval(soul: dict, description: str, cue: str):
    """
    Updates the triggers list of a retrieved memory.
    Called after context assembly to record what surfaced this memory.
    Repeated retrieval strengthens future accessibility.
    """
    for memory in soul.get("long_term_memories", []):
        if memory.get("description") == description:
            memory.setdefault("triggers", []).append(cue)
            break


# ─── SHARPNESS PRESENTATION ───────────────────────────────────────────────────

def apply_sharpness(memory: dict) -> str:
    """
    Returns the memory description wrapped in language appropriate
    to its sharpness value.

    High sharpness  — full detail, presented clearly.
    Medium sharpness — present but softer at the edges.
    Low sharpness   — vague, hedged language.
    """
    description = memory.get("description", "")
    sharpness = memory.get("sharpness", 0.0)

    if sharpness >= 0.75:
        return description
    elif sharpness >= 0.40:
        return f"I remember, though not perfectly — {description}"
    else:
        return f"There is something, vague now — {description}"