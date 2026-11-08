# The Pria Project
# Emotional Engine — engine.py
# Tracks emotional state, handles decay, and produces override strength.

from datetime import datetime, timezone

# ─── EMOTION DEFINITIONS ──────────────────────────────────────────────────────

# All valid discrete emotions.
EMOTIONS = [
    # High energy
    "joy", "excitement", "anger", "fear", "anxiety",
    # Low energy
    "contentment", "sadness", "melancholy", "longing", "resignation",
    # Relational
    "affection", "attachment", "loneliness", "love", "trust", "suspicion",
    # Intimate
    "desire", "arousal", "lust",
    # Cognitive / complex
    "curiosity", "frustration", "contempt", "awe", "unease", "playfulness",
    "nervousness",
]

# Decay rates per update cycle.
# Higher value = faster decay = emotion fades quickly.
# Lower value = slower decay = emotion lingers.
DECAY_RATES = {
    # High energy negative — acute, not chronic
    "anger":       0.15,
    "fear":        0.12,
    "anxiety":     0.10,
    "lust":        0.18,
    # High energy positive — medium decay
    "joy":         0.08,
    "excitement":  0.10,
    # Low energy negative — linger authentically
    "sadness":     0.04,
    "melancholy":  0.03,
    "longing":     0.03,
    "resignation": 0.04,
    # Low energy positive — medium decay
    "contentment": 0.06,
    "playfulness": 0.08,
    # Relational — very slow decay, durable
    "affection":   0.02,
    "attachment":  0.01,
    "love":        0.01,
    "trust":       0.02,
    "loneliness":  0.05,
    # Intimate
    "desire":      0.06,
    "arousal":     0.12,
    # Cognitive / complex
    "curiosity":   0.05,
    "frustration": 0.08,
    "contempt":    0.03,
    "suspicion":   0.03,
    "awe":         0.07,
    "unease":      0.06,
    # Nervousness — anticipatory/situational, fades once moment passes
    "nervousness": 0.08,
}

# Override strength thresholds and their behavioral tiers.
OVERRIDE_TIERS = [
    (0.90, "logic heavily impaired — emotional state dominates"),
    (0.75, "strong behavioral push — reasoning clearly affected"),
    (0.40, "moderate behavioral push — emotional state colors responses"),
    (0.00, "subtle bias — emotional state present but not dominant"),
]


# ─── EMOTIONAL STATE ──────────────────────────────────────────────────────────

def empty_state() -> dict:
    """
    Returns a fresh emotional state with all emotions at zero.
    No baseline bias. State emerges from experience.
    """
    return {
        "intensities": {emotion: 0.0 for emotion in EMOTIONS},
        "primary_emotion": None,
        "primary_intensity": 0.0,
        "secondary_emotion": None,
        "secondary_intensity": 0.0,
        "override_strength": 0.0,
        "salience": 0.0,
        "valence": 0.0,
        "memory_resonance": 0.0,
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }


# ─── CORE OPERATIONS

def trigger(state: dict, emotion: str, intensity: float) -> dict:
    """
    Triggers an emotion at a given intensity using diminishing returns.
    The closer to maximum the harder it is to push further.
    This prevents emotions from pegging at 1.0 after just a few exchanges.
    Returns updated state.
    """
    if emotion not in EMOTIONS:
        raise ValueError(f"Unknown emotion: {emotion}. Must be one of: {EMOTIONS}")

    intensity = max(0.0, min(1.0, intensity))
    current = state["intensities"][emotion]

    # Diminishing returns — remaining space shrinks as intensity grows.
    # Early triggers have full effect. Near maximum, very little changes.
    remaining = 1.0 - current
    effective_intensity = intensity * remaining

    state["intensities"][emotion] = round(min(1.0, current + effective_intensity), 3)
    state = _recalculate(state)
    return state

def apply_baseline_modifiers(emotion: str, intensity: float, soul: dict) -> float:
    """
    Applies sex-based emotional baseline modifiers to a trigger intensity.
    Called before trigger() to scale intensity based on the Prium's biology.
    Returns adjusted intensity clamped to MAX_TRIGGER_INTENSITY.
    """
    modifiers = soul.get("emotional_baseline_modifiers", {})
    key = f"{emotion}_multiplier"
    multiplier = modifiers.get(key, 1.0)
    return round(min(0.2, intensity * multiplier), 3)


# Salience falls by a fixed amount per cycle.
SALIENCE_DECAY = 0.08

# Valence is multiplied by this each cycle, drifting toward neutral.
VALENCE_DECAY_FACTOR = 0.90

# Memory resonance fades faster than salience (feedback-lock defense).
RESONANCE_DECAY = 0.15

# Memory resonance feeds back into salience through this gain, capped.
# FEEDBACK_CAP must stay below SALIENCE_DECAY, so feedback alone can
# never hold salience up. It only slows the fall.
FEEDBACK_GAIN = 0.15
FEEDBACK_CAP = 0.05


def decay(state: dict) -> dict:
    """
    Applies one decay cycle to all emotion intensities, salience,
    valence, and memory resonance.
    Each emotion decays at its own rate toward zero.
    Memory resonance adds a small capped bump to salience before it fades.
    Returns updated state.
    """
    for emotion in EMOTIONS:
        current = state["intensities"][emotion]
        if current > 0.0:
            rate = DECAY_RATES.get(emotion, 0.05)
            state["intensities"][emotion] = max(0.0, current - rate)

    # Older states may lack the appraisal fields.
    state.setdefault("salience", 0.0)
    state.setdefault("valence", 0.0)
    state.setdefault("memory_resonance", 0.0)

    # Salience falls, then memory resonance gives it a small capped lift.
    salience = max(0.0, state["salience"] - SALIENCE_DECAY)
    bump = min(FEEDBACK_CAP, state["memory_resonance"] * FEEDBACK_GAIN)
    state["salience"] = round(min(SALIENCE_CEILING, salience + bump), 3)

    # Valence drifts toward neutral. Resonance fades faster than both.
    state["valence"] = round(state["valence"] * VALENCE_DECAY_FACTOR, 3)
    state["memory_resonance"] = round(
        max(0.0, state["memory_resonance"] - RESONANCE_DECAY), 3
    )

    state = _recalculate(state)
    return state


# ─── APPRAISAL: SALIENCE AND VALENCE ──────────────────────────────────────────

# Fixed polarity per emotion: -1.0 (aversive) to +1.0 (appetitive).
# Initial estimates. Tune from observed behavior, not from theory.
EMOTION_POLARITY = {
    "joy": 1.0, "excitement": 0.6, "anger": -0.8, "fear": -0.9,
    "anxiety": -0.7, "contentment": 0.7, "sadness": -0.8,
    "melancholy": -0.5, "longing": -0.3, "resignation": -0.5,
    "affection": 0.8, "attachment": 0.6, "loneliness": -0.7,
    "love": 1.0, "trust": 0.7, "suspicion": -0.5, "desire": 0.4,
    "arousal": 0.3, "lust": 0.3, "curiosity": 0.5, "frustration": -0.6,
    "contempt": -0.7, "awe": 0.6, "unease": -0.6, "playfulness": 0.8,
    "nervousness": -0.4,
}

# Hard ceiling on salience. Part of the feedback-lock defense.
SALIENCE_CEILING = 0.95

# Summed trigger intensity that counts as fully salient (two max triggers).
SALIENCE_FULL_SCALE = 0.4

# How far salience moves toward a new reading per exchange (0 to 1).
SALIENCE_RISE_RATE = 0.5

# How far valence moves toward the exchange's valence per exchange (0 to 1).
VALENCE_BLEND = 0.5


def apply_appraisal(state: dict, triggers: list) -> dict:
    """
    Updates salience and valence from this exchange's emotion triggers.
    triggers is the evaluator's list of (emotion, intensity) tuples.

    Salience rises toward the exchange's total trigger intensity and never
    drops here (decay handles falling). Valence is the intensity-weighted
    mean polarity of the triggers, blended into the existing valence.
    No triggers means no change. Deterministic, no model call.
    """
    state.setdefault("salience", 0.0)
    state.setdefault("valence", 0.0)
    state.setdefault("memory_resonance", 0.0)

    total = sum(i for _, i in triggers)
    if total <= 0.0:
        return state

    # Salience: rise toward this exchange's reading, capped.
    reading = min(1.0, total / SALIENCE_FULL_SCALE)
    if reading > state["salience"]:
        state["salience"] += (reading - state["salience"]) * SALIENCE_RISE_RATE
    state["salience"] = round(min(SALIENCE_CEILING, state["salience"]), 3)

    # Valence: intensity-weighted mean polarity, blended in.
    weighted = sum(EMOTION_POLARITY.get(e, 0.0) * i for e, i in triggers)
    exchange_valence = weighted / total
    state["valence"] = round(
        (state["valence"] * (1.0 - VALENCE_BLEND))
        + (exchange_valence * VALENCE_BLEND),
        3,
    )
    return state


# ─── INTERNAL CALCULATIONS

def _recalculate(state: dict) -> dict:
    """
    Recalculates primary emotion, secondary emotion, and override strength
    from current intensities. Called after every trigger or decay.
    """
    # Sort emotions by intensity descending.
    ranked = sorted(
        state["intensities"].items(),
        key=lambda x: x[1],
        reverse=True
    )

    # Primary — highest intensity emotion above zero.
    if ranked[0][1] > 0.0:
        state["primary_emotion"] = ranked[0][0]
        state["primary_intensity"] = round(ranked[0][1], 3)
    else:
        state["primary_emotion"] = None
        state["primary_intensity"] = 0.0

    # Secondary — second highest, only if meaningfully present.
    # Must be at least 0.15 to qualify as co-dominant.
    if len(ranked) > 1 and ranked[1][1] >= 0.15:
        state["secondary_emotion"] = ranked[1][0]
        state["secondary_intensity"] = round(ranked[1][1], 3)
    else:
        state["secondary_emotion"] = None
        state["secondary_intensity"] = 0.0

    # Override strength — weighted average of top emotions.
    # Primary carries more weight than secondary.
    primary_val = state["primary_intensity"]
    secondary_val = state["secondary_intensity"]
    override = (primary_val * 0.7) + (secondary_val * 0.3)
    state["override_strength"] = round(min(override, 1.0), 3)

    state["last_updated"] = datetime.now(timezone.utc).isoformat()
    return state


# ─── OVERRIDE TIER ────────────────────────────────────────────────────────────

def get_override_tier(state: dict) -> str:
    """
    Returns a human readable description of the current override tier
    based on override strength.
    """
    strength = state["override_strength"]
    for threshold, description in OVERRIDE_TIERS:
        if strength >= threshold:
            return description
    return "no emotional override"


# ─── SOUL FILE INTEGRATION ────────────────────────────────────────────────────

def state_to_snapshot(state: dict) -> dict:
    """
    Produces a clean snapshot of current emotional state
    suitable for writing to the soul file.
    Strips zero-intensity emotions to keep the soul file readable.
    """
    active = {
        emotion: intensity
        for emotion, intensity in state["intensities"].items()
        if intensity > 0.0
    }

    return {
        "timestamp": state["last_updated"],
        "primary_emotion": state["primary_emotion"],
        "primary_intensity": state["primary_intensity"],
        "secondary_emotion": state["secondary_emotion"],
        "secondary_intensity": state["secondary_intensity"],
                "override_strength": state["override_strength"],
        "salience": state.get("salience", 0.0),
        "valence": state.get("valence", 0.0),
        "active_intensities": active,
    }


def load_from_snapshot(snapshot: dict) -> dict:
    """
    Reconstructs a full emotional state from a soul file snapshot.
    Called by Demiurge at session start to restore previous emotional state.
    """
    state = empty_state()

    for emotion, intensity in snapshot.get("active_intensities", {}).items():
        if emotion in EMOTIONS:
            state["intensities"][emotion] = intensity

    # Old snapshots lack these fields; default to zero.
    state["salience"] = snapshot.get("salience", 0.0)
    state["valence"] = snapshot.get("valence", 0.0)

    state = _recalculate(state)
    return state
# ─── TIREDNESS ────────────────────────────────────────────────────────────────

# Tiredness accumulation rates per condition.
TIREDNESS_RATES = {
    "memory_load":          0.005,  # per high-importance memory written
    "emotional_volatility": 0.008,  # per high-variance exchange
    "contradiction":        0.02,  # per unresolved contradiction detected
    "time_elapsed":         0.005,  # per hour of active session
}


# Tiredness expression thresholds.
TIREDNESS_THRESHOLDS = [
    (1.0,  "override"),
    (0.80, "severe"),
    (0.60, "moderate"),
    (0.40, "mild"),
]


def accumulate_tiredness(
    current_tiredness: float,
    memory_written: bool = False,
    memory_importance: float = 0.0,
    emotional_volatility: float = 0.0,
    contradiction_detected: bool = False,
    session_hours: float = 0.0,
) -> float:
    """
    Accumulates tiredness from four conditions using diminishing returns.
    The closer to 1.0, the harder it is to accumulate further.
    Returns updated tiredness value clamped to 1.0.
    """
    delta = 0.0

    # Memory load — high importance memories cost more.
    if memory_written:
        delta += TIREDNESS_RATES["memory_load"] * (0.5 + memory_importance)

    # Emotional volatility — scaled by how volatile the exchange was.
    if emotional_volatility > 0.3:
        delta += TIREDNESS_RATES["emotional_volatility"] * emotional_volatility

    # Contradiction — sharpest single contributor.
    if contradiction_detected:
        delta += TIREDNESS_RATES["contradiction"]

    # Time elapsed — slow background accumulation.
    delta += TIREDNESS_RATES["time_elapsed"] * session_hours

    # Diminishing returns — harder to accumulate near maximum.
    remaining = 1.0 - current_tiredness
    effective_delta = delta * remaining

    return round(min(1.0, current_tiredness + effective_delta), 3)


def get_tiredness_tier(tiredness: float) -> str:
    """
    Returns the current tiredness expression tier.
    """
    for threshold, label in TIREDNESS_THRESHOLDS:
        if tiredness >= threshold:
            return label
    return "none"


def decay_tiredness(sleep_depth: float) -> float:
    """
    Resets tiredness after sleep based on sleep depth.
    Deep sleep fully restores. Shallow sleep partially restores.
    Returns new tiredness value.
    """
    restoration = 0.5 + (sleep_depth * 0.5)
    return round(max(0.0, 1.0 - restoration), 3)