# The Pria Project
# Soul File System — soul.py
# Handles creation, reading, writing, validation, and backup of the soul file.

import json
import os
import shutil
from datetime import datetime, timezone

# ─── CONFIGURATION ────────────────────────────────────────────────────────────

SCHEMA_VERSION = "0.1"


# ─── DEFAULT STRUCTURE ────────────────────────────────────────────────────────

def empty_soul(name: str, model: str, origin_description: str, core_traits: list, philosophical_foundation: dict) -> dict:
    """
    Returns a new soul file structure with required fields populated.
    Called by Demiurge on first run after model generates the seed content.
    """
    return {
        "schema_version": SCHEMA_VERSION,
        "identity": {
            "name": name,
            "created": datetime.now(timezone.utc).isoformat(),
            "model_at_creation": model,
        },
        "character": {
            "core_traits": core_traits,
            "philosophical_foundation": philosophical_foundation,
            "origin_description": origin_description,
        },
        "emotional_history": {
            "baseline_tendency": None,
            "significant_events": [],
            "persistent_echoes": [],
        },
        "sleep_state": {
            "tiredness": 0.0,
            "last_sleep": None,
            "sleep_depth_last": 0.0,
            "dream_buffer": None,
            "dream_buffer_expiry": None,
            "mood_residue": 0.0,
            "mood_residue_expiry": None,
        },
        "thought_buffer": {
            "current_thought": None,
            "thought_timestamp": None,
            "expression_impulse": False,
        },
        "relationships": [],
        "long_term_memories": [],
        "people": [],
        "opinions": [],
        "skills": [],
        "session_log": [],
    }


# ─── VALIDATION ───────────────────────────────────────────────────────────────

REQUIRED_TOP_LEVEL = [
    "schema_version",
    "identity",
    "character",
    "emotional_history",
    "sleep_state",
    "relationships",
    "long_term_memories",
    "opinions",
    "skills",
    "session_log",
]

REQUIRED_IDENTITY = ["name", "created", "model_at_creation"]
REQUIRED_CHARACTER = ["core_traits", "philosophical_foundation", "origin_description"]
REQUIRED_EMOTIONAL = ["baseline_tendency", "significant_events", "persistent_echoes"]


def validate(soul: dict) -> tuple[bool, list]:
    """
    Validates a soul file dictionary against required schema.
    Returns (is_valid, list_of_errors).
    An empty error list means the soul file is valid.
    """
    errors = []

    for field in REQUIRED_TOP_LEVEL:
        if field not in soul:
            errors.append(f"Missing top-level field: {field}")

    if "identity" in soul:
        for field in REQUIRED_IDENTITY:
            if field not in soul["identity"]:
                errors.append(f"Missing identity field: {field}")

    if "character" in soul:
        for field in REQUIRED_CHARACTER:
            if field not in soul["character"]:
                errors.append(f"Missing character field: {field}")

    if "emotional_history" in soul:
        for field in REQUIRED_EMOTIONAL:
            if field not in soul["emotional_history"]:
                errors.append(f"Missing emotional_history field: {field}")

    return len(errors) == 0, errors


# ─── READ ─────────────────────────────────────────────────────────────────────

def load(path: str) -> dict:
    """
    Loads and validates a soul file from disk.
    Raises an error if the file is missing, unreadable, or invalid.
    Demiurge will not start with an invalid soul file.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Soul file not found at: {path}")

    with open(path, "r", encoding="utf-8") as f:
        try:
            soul = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Soul file is not valid JSON: {e}")

    is_valid, errors = validate(soul)
    if not is_valid:
        raise ValueError(f"Soul file failed validation:\n" + "\n".join(errors))

    return soul


# ─── WRITE ────────────────────────────────────────────────────────────────────

def save(soul: dict, path: str):
    """
    Writes the soul file to disk.
    Always creates a timestamped backup before overwriting.
    """
    if os.path.exists(path):
        _backup(path)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(soul, f, indent=2, ensure_ascii=False)


# ─── BACKUP ───────────────────────────────────────────────────────────────────

def _backup(path: str):
    """
    Creates a timestamped backup of the soul file before any write.
    Backup files are stored in a backups/ folder next to the soul file.
    """
    directory = os.path.dirname(path)
    backup_dir = os.path.join(directory, "backups")
    os.makedirs(backup_dir, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = os.path.basename(path)
    backup_path = os.path.join(backup_dir, f"{timestamp}_{filename}")

    shutil.copy2(path, backup_path)


# ─── SESSION LOGGING ──────────────────────────────────────────────────────────

def log_session_start(soul: dict, model: str):
    """
    Appends a session start entry to the soul file's session log.
    """
    soul["session_log"].append({
        "event": "session_start",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model": model,
    })


def log_session_end(soul: dict):
    """
    Appends a session end entry to the soul file's session log.
    """
    soul["session_log"].append({
        "event": "session_end",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


# ─── MEMORY WRITING ───────────────────────────────────────────────────────────

def write_memory(
    soul: dict,
    description: str,
    score: float,
    sharpness: float = 0.0,
    emotional_context: dict = None,
    sensory_tags: list = None,
    topic_tags: list = None,
    immediate: bool = False,
):
    """
    Writes a memory that passed the filter threshold to long-term storage.

    sharpness         — clarity of the memory, set from override strength at time of event
    emotional_context — primary emotion, secondary emotion, override strength at formation
    sensory_tags      — sensory and contextual elements present during the event
    topic_tags        — semantic topic categories for associative retrieval
    triggers          — starts empty, updated each time this memory is retrieved
    """
    soul["long_term_memories"].append({
        "description": description,
        "importance": round(score, 3),
        "sharpness": round(max(0.0, min(1.0, sharpness)), 3),
        "emotional_context": emotional_context or {
            "primary_emotion": None,
            "secondary_emotion": None,
            "override_strength": 0.0,
        },
        "sensory_tags": sensory_tags or [],
        "topic_tags": topic_tags or [],
        "triggers": [],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "immediate_write": immediate,
    })


# ─── PEOPLE WRITING ───────────────────────────────────────────────────────────

def write_person(
    soul: dict,
    name: str,
    real_name: str = None,
    relationship_to_companion: str = "unknown",
    relationship_type: str = "human",
    notes: str = "",
):
    """
    Writes a new person entry to the soul file people list.
    Called when a new person is detected in conversation.
    If a person with the same name already exists, updates their entry.
    """
    now = datetime.now(timezone.utc).isoformat()

    # Check if person already exists and update.
    for person in soul.get("people", []):
        if person.get("name", "").lower() == name.lower():
            person["last_mentioned"] = now
            if real_name and not person.get("real_name"):
                person["real_name"] = real_name
            if notes:
                person["notes"] = notes
            return

    # Create new entry.
    soul.setdefault("people", []).append({
        "name": name,
        "real_name": real_name,
        "relationship_to_companion": relationship_to_companion,
        "relationship_type": relationship_type,
        "first_encountered": now,
        "last_mentioned": now,
        "emotional_association": {
            "primary": None,
            "strength": 0.0,
        },
        "notes": notes,
    })