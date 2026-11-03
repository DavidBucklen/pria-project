# The Pria Project
# Generation Modulation — modulation.py
# Translates emotional state directly into Ollama generation parameters.
# Emotion physically alters how the model generates output rather than
# merely informing it via context description.
#
# Architecture:
#   1. Each emotion has a parameter profile at intensity 1.0
#   2. Parameters are interpolated linearly from baseline at intensity 0.0
#   3. Stability floor applied per-emotion above override_strength 0.85
#   4. Primary and secondary emotion vectors blended using dominance rules
#
# Scoping:
#   Modulation applies ONLY to the main conversational response call.
#   Never applied to: evaluate_exchange, inner_monologue, detect_people,
#   first_run, or any other analytical model call.

# ─── BASELINE (CALM STATE) ────────────────────────────────────────────────────

BASELINE = {
    "temperature":    0.80,
    "top_p":          0.90,
    "top_k":          40,
    "repeat_penalty": 1.10,
    "num_predict":    -1,    # -1 = unlimited
}

# ─── PER-EMOTION PROFILES ─────────────────────────────────────────────────────
# Values represent parameters at intensity 1.0.
# Actual parameters interpolated between BASELINE (intensity 0.0) and profile.
#
# Categories:
#   HIGH IMPAIRMENT    — actively degrade measured reasoning
#   MODERATE IMPAIRMENT — color responses without breaking reasoning
#   EXPRESSIVE ONLY    — handled by soul file context, no param changes
#   LOGIC ENHANCING    — improve or expand generation quality
#
# Note: top_k is the primary impairment lever, not temperature.
# Temperature ceiling: 1.05 (absolute max for 8B model stability).
# num_predict minimum: 200 (prevents mid-sentence truncation).

EMOTION_PROFILES = {

    # ── HIGH IMPAIRMENT ───────────────────────────────────────────────────────

    # Anger — tunnel vision, clipped, impulsive. top_k does the heavy lifting.
    "anger": {
        "temperature":    1.00,
        "top_p":          0.68,
        "top_k":          10,
        "repeat_penalty": 0.92,
        "num_predict":    200,
    },

    # Fear — fragmented, reactive, short output.
    "fear": {
        "temperature":    1.00,
        "top_p":          0.70,
        "top_k":          15,
        "repeat_penalty": 0.94,
        "num_predict":    220,
    },

    # Anxiety — scattered, hypervigilant, less coherent.
    "anxiety": {
        "temperature":    0.98,
        "top_p":          0.74,
        "top_k":          20,
        "repeat_penalty": 0.96,
        "num_predict":    240,
    },

    # Lust — fixated, preoccupied, executive function recedes.
    "lust": {
        "temperature":    1.05,
        "top_p":          0.70,
        "top_k":          15,
        "repeat_penalty": 0.88,
        "num_predict":    260,
    },

    # Desire — shares profile with lust (merged per reviewer consensus).
    "desire": {
        "temperature":    1.05,
        "top_p":          0.70,
        "top_k":          15,
        "repeat_penalty": 0.88,
        "num_predict":    260,
    },

    # Arousal — activation and heightened presence, fixation on a thread.
    "arousal": {
        "temperature":    1.05,
        "top_p":          0.70,
        "top_k":          15,
        "repeat_penalty": 0.88,
        "num_predict":    260,
    },

    # Sadness — slowed, withdrawn, flat. Less elaborated.
    "sadness": {
        "temperature":    0.88,
        "top_p":          0.78,
        "top_k":          22,
        "repeat_penalty": 0.95,
        "num_predict":    200,
    },

    # Love — logic reoriented not degraded. Near-baseline by design.
    # Decisions evaluated through lens of attachment, not impaired reasoning.
    # Executive function intact but differently weighted.
    "love": {
        "temperature":    0.82,
        "top_p":          0.91,
        "top_k":          40,
        "repeat_penalty": 1.09,
        "num_predict":    -1,
    },

    # ── MODERATE IMPAIRMENT ───────────────────────────────────────────────────

    # Longing — pulled inward, reflective, less present.
    "longing": {
        "temperature":    0.90,
        "top_p":          0.80,
        "top_k":          28,
        "repeat_penalty": 0.98,
        "num_predict":    -1,
    },

    # Melancholy — slow, reflective, less engaged.
    "melancholy": {
        "temperature":    0.88,
        "top_p":          0.80,
        "top_k":          28,
        "repeat_penalty": 0.97,
        "num_predict":    240,
    },

    # Frustration — shortened patience, less charitable interpretations.
    "frustration": {
        "temperature":    0.95,
        "top_p":          0.78,
        "top_k":          22,
        "repeat_penalty": 0.95,
        "num_predict":    240,
    },

    # Contempt — dismissive, minimal elaboration.
    "contempt": {
        "temperature":    0.92,
        "top_p":          0.75,
        "top_k":          20,
        "repeat_penalty": 1.05,
        "num_predict":    200,
    },

    # Unease — cautious, hedged. Something feels wrong.
    # Strictly: moral discomfort, unnamed threat, wrongness.
    # NOT for activation, nervousness, or arousal states.
    "unease": {
        "temperature":    0.98,
        "top_p":          0.80,
        "top_k":          25,
        "repeat_penalty": 1.00,
        "num_predict":    -1,
    },

    # Suspicion — guarded, short, closed.
    "suspicion": {
        "temperature":    0.93,
        "top_p":          0.76,
        "top_k":          20,
        "repeat_penalty": 1.02,
        "num_predict":    220,
    },

    # Resignation — flat affect, coherent but disengaged.
    "resignation": {
        "temperature":    0.85,
        "top_p":          0.82,
        "top_k":          30,
        "repeat_penalty": 1.00,
        "num_predict":    220,
    },

    # Nervousness — anticipatory tension, situational.
    # Distinct from anxiety (diffuse/chronic) and unease (wrongness).
    "nervousness": {
        "temperature":    1.04,
        "top_p":          0.76,
        "top_k":          24,
        "repeat_penalty": 0.96,
        "num_predict":    240,
    },

    # Loneliness — withdrawn, aching for connection, less engaged.
    "loneliness": {
        "temperature":    0.88,
        "top_p":          0.80,
        "top_k":          28,
        "repeat_penalty": 0.97,
        "num_predict":    -1,
    },

    # ── EXPRESSIVE ONLY — no sampling parameter changes ───────────────────────
    # These emotions are handled entirely by the soul file context layer.
    # Warmth, bond, and openness come through in what is said, not how
    # the model samples. Included here as explicit no-ops for clarity.

    "affection":  None,   # expressive only — context layer handles this
    "attachment": None,   # expressive only — context layer handles this
    "trust":      None,   # expressive only — context layer handles this
    "contentment": None,  # expressive only — calm baseline is baseline

    # ── LOGIC ENHANCING ───────────────────────────────────────────────────────

    # Curiosity — expands search space, tolerates uncertainty, explores.
    # top_k 70 is the primary enhancing lever — much broader consideration set.
    # top_p 0.93 guards against wandering at high top_k on 8B models.
    "curiosity": {
        "temperature":    0.78,
        "top_p":          0.93,
        "top_k":          70,
        "repeat_penalty": 1.10,
        "num_predict":    -1,
    },

    # Awe — expansive, sits with complexity, less need to resolve.
    "awe": {
        "temperature":    0.80,
        "top_p":          0.95,
        "top_k":          55,
        "repeat_penalty": 1.10,
        "num_predict":    -1,
    },

    # Joy — broad associations, generous interpretations.
    "joy": {
        "temperature":    0.82,
        "top_p":          0.93,
        "top_k":          48,
        "repeat_penalty": 1.08,
        "num_predict":    -1,
    },

    # Excitement — high energy, elaborated, forward-moving.
    "excitement": {
        "temperature":    0.84,
        "top_p":          0.92,
        "top_k":          44,
        "repeat_penalty": 1.06,
        "num_predict":    -1,
    },

    # Playfulness — associative, light, slightly unpredictable.
    "playfulness": {
        "temperature":    0.86,
        "top_p":          0.93,
        "top_k":          48,
        "repeat_penalty": 1.08,
        "num_predict":    -1,
    },
}

# ─── STABILITY FLOOR ──────────────────────────────────────────────────────────
# Above override_strength 0.85, modulation intensity scales back toward baseline.
# Prevents runaway emotional self-reinforcement loops.
# At 0.85: full modulation effect (scale = 1.0)
# At 1.00: half modulation effect (scale = 0.5), pulling back toward baseline.
# Reflects human tendency toward flat affect or dissociation under sustained
# extreme emotion rather than infinitely worsening cognition.

STABILITY_FLOOR_THRESHOLD = 0.85
STABILITY_FLOOR_MIN_SCALE = 0.5


def _stability_scale(override_strength: float) -> float:
    """
    Returns the modulation scale factor for a given override strength.
    1.0 at or below threshold, declining to STABILITY_FLOOR_MIN_SCALE at 1.0.
    """
    if override_strength <= STABILITY_FLOOR_THRESHOLD:
        return 1.0
    excess = (override_strength - STABILITY_FLOOR_THRESHOLD) / (1.0 - STABILITY_FLOOR_THRESHOLD)
    return 1.0 - (excess * (1.0 - STABILITY_FLOOR_MIN_SCALE))


# ─── INTERPOLATION ────────────────────────────────────────────────────────────

def _lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation between a and b at fraction t (0.0 to 1.0)."""
    return a + (b - a) * t


def _interpolate_profile(emotion: str, intensity: float, override_strength: float) -> dict:
    """
    Calculates the parameter vector for a single emotion at a given intensity.

    Steps:
    1. Interpolate from BASELINE toward the emotion's profile at the given intensity.
    2. Apply stability floor based on override_strength.

    Returns a parameter dict, or BASELINE if the emotion is expressive-only
    or not found in the profiles.
    """
    profile = EMOTION_PROFILES.get(emotion)

    # Expressive-only emotions and unknown emotions return baseline.
    if profile is None:
        return dict(BASELINE)

    intensity = max(0.0, min(1.0, intensity))

    # Apply stability floor scaling.
    scale = _stability_scale(override_strength)
    # Effective intensity after floor: pulls t back toward 0 (baseline) at high override.
    effective_t = intensity * scale

    params = {}
    for key in BASELINE:
        baseline_val = BASELINE[key]
        profile_val = profile[key]

        if key == "num_predict":
            # Handle unlimited (-1) specially.
            if profile_val == -1:
                # Profile is unlimited — stays unlimited regardless of intensity.
                params[key] = -1
            elif baseline_val == -1:
                # Baseline is unlimited, profile sets a limit.
                # Ease in from a generous ceiling (600) toward profile limit.
                params[key] = int(_lerp(600, profile_val, effective_t))
            else:
                params[key] = int(round(_lerp(baseline_val, profile_val, effective_t)))
        elif key == "top_k":
            params[key] = int(round(_lerp(baseline_val, profile_val, effective_t)))
        else:
            params[key] = round(_lerp(baseline_val, profile_val, effective_t), 4)

    return params


# ─── BLENDING ─────────────────────────────────────────────────────────────────
# Per-parameter dominance rules (ChatGPT + Gemini consensus):
#
#   top_k          — smooth weighted minimum (lower value has more influence)
#   top_p          — smooth weighted minimum (lower value has more influence)
#   temperature    — weighted blend (70% primary, 30% secondary)
#   repeat_penalty — weighted blend (70% primary, 30% secondary)
#   num_predict    — lower value wins (shorter output preference dominates)
#
# "Smooth weighted minimum" means the lower value gets extra weight rather than
# winning outright. Prevents a weak secondary emotion from completely overriding
# a strong primary just because its top_k happens to be numerically lower.

PRIMARY_WEIGHT   = 0.70
SECONDARY_WEIGHT = 0.30


def _smooth_weighted_min(primary_val, secondary_val, primary_weight=PRIMARY_WEIGHT):
    """
    Blends two values giving extra weight to whichever is lower (more restrictive).
    The lower value's weight is boosted by the difference between the two values,
    scaled to keep the result between them.
    """
    secondary_weight = 1.0 - primary_weight
    # Standard weighted blend as the base.
    blend = (primary_val * primary_weight) + (secondary_val * secondary_weight)
    # Pull blend toward the lower value proportionally.
    lower = min(primary_val, secondary_val)
    higher = max(primary_val, secondary_val)
    if higher == lower:
        return blend
    # How far is the blend from the lower value, as a fraction of the range?
    pull_strength = 0.3  # how aggressively to pull toward the lower value
    return blend - (blend - lower) * pull_strength


def _blend_params(primary_params: dict, secondary_params: dict) -> dict:
    """
    Blends primary and secondary parameter vectors using dominance rules.
    """
    blended = {}

    for key in BASELINE:
        p_val = primary_params[key]
        s_val = secondary_params[key]

        if key == "top_k":
            blended[key] = int(round(_smooth_weighted_min(p_val, s_val)))

        elif key == "top_p":
            blended[key] = round(_smooth_weighted_min(p_val, s_val), 4)

        elif key == "temperature":
            blended[key] = round(
                (p_val * PRIMARY_WEIGHT) + (s_val * SECONDARY_WEIGHT), 4
            )

        elif key == "repeat_penalty":
            blended[key] = round(
                (p_val * PRIMARY_WEIGHT) + (s_val * SECONDARY_WEIGHT), 4
            )

        elif key == "num_predict":
            # Lower value wins. Handle -1 (unlimited) carefully.
            if p_val == -1 and s_val == -1:
                blended[key] = -1
            elif p_val == -1:
                blended[key] = s_val
            elif s_val == -1:
                blended[key] = p_val
            else:
                blended[key] = min(p_val, s_val)

    return blended


# ─── PUBLIC API ───────────────────────────────────────────────────────────────

def get_generation_params(
    primary_emotion: str,
    primary_intensity: float,
    secondary_emotion: str,
    secondary_intensity: float,
    override_strength: float,
) -> dict:
    """
    Returns Ollama generation parameters for the current emotional state.

    primary_emotion     — name of the primary emotion (or None)
    primary_intensity   — intensity of the primary emotion (0.0 to 1.0)
    secondary_emotion   — name of the secondary emotion (or None)
    secondary_intensity — intensity of the secondary emotion (0.0 to 1.0)
    override_strength   — current overall override strength (0.0 to 1.0)
                          Used for stability floor calculation.

    Returns a dict suitable for passing as the options field in an
    Ollama /api/generate request.

    Ordering (Gemini consensus):
    1. Interpolate primary params at primary_intensity
    2. Apply stability floor to primary params
    3. Interpolate secondary params at secondary_intensity
    4. Apply stability floor to secondary params
    5. Blend using per-parameter dominance rules
    """
    # No emotional state — return baseline unchanged.
    if not primary_emotion:
        return dict(BASELINE)

    # Calculate primary parameter vector (interpolation + stability floor built in).
    primary_params = _interpolate_profile(primary_emotion, primary_intensity, override_strength)

    # No secondary emotion — return primary params directly.
    if not secondary_emotion or secondary_intensity < 0.15:
        return primary_params

    # Calculate secondary parameter vector.
    secondary_params = _interpolate_profile(secondary_emotion, secondary_intensity, override_strength)

    # Blend using dominance rules.
    return _blend_params(primary_params, secondary_params)