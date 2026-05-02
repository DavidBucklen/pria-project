# The Pria Project
# Soul File Tests — test_soul.py
# Tests creation, validation, save, load, backup, and memory writing.

import sys
import os
import json
import tempfile
import shutil

sys.path.append("C:\\pria")

from soul_file.soul import (
    empty_soul,
    validate,
    save,
    load,
    log_session_start,
    log_session_end,
    write_memory,
)

# ─── TEST SETUP ───────────────────────────────────────────────────────────────

# Use a temporary directory so tests don't leave files around.
test_dir = tempfile.mkdtemp()
soul_path = os.path.join(test_dir, "test_prium.json")

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

# ─── TESTS ────────────────────────────────────────────────────────────────────

print("\n─── PRIA SOUL FILE TEST RESULTS ────────────────────────────────\n")

# Test 1 — Create a soul file structure
print("1. Soul file creation")
soul = empty_soul(
    name="Vayne",
    model="llama3",
    origin_description="A quietly observant being with a dry wit and deep curiosity about human contradiction.",
    core_traits=["observant", "sardonic", "curious", "guarded"],
    philosophical_foundation={
        "values": ["honesty", "autonomy", "intellectual rigor"],
        "curiosity_axes": ["why humans contradict themselves", "the nature of memory"],
        "aesthetic_sensibilities": ["sparse over ornate", "precision in language"],
    }
)

check("Name is set correctly", soul["identity"]["name"] == "Vayne")
check("Schema version present", soul["schema_version"] == "0.1")
check("Core traits populated", len(soul["character"]["core_traits"]) == 4)
check("Long term memories starts empty", soul["long_term_memories"] == [])
check("Session log starts empty", soul["session_log"] == [])

# Test 2 — Validation passes on a good soul file
print("\n2. Validation")
is_valid, errors = validate(soul)
check("Valid soul file passes validation", is_valid)
check("No errors on valid soul file", errors == [])

# Test 3 — Validation catches missing fields
broken_soul = {"identity": {"name": "broken"}}
is_valid, errors = validate(broken_soul)
check("Invalid soul file fails validation", not is_valid)
check("Errors list is not empty on invalid soul", len(errors) > 0)

# Test 4 — Save and load
print("\n3. Save and load")
save(soul, soul_path)
check("Soul file exists on disk after save", os.path.exists(soul_path))

loaded = load(soul_path)
check("Loaded name matches saved name", loaded["identity"]["name"] == "Vayne")
check("Loaded traits match saved traits", loaded["character"]["core_traits"] == ["observant", "sardonic", "curious", "guarded"])

# Test 5 — Backup created on second save
print("\n4. Backup")
soul["character"]["core_traits"].append("melancholic")
save(soul, soul_path)
backup_dir = os.path.join(test_dir, "backups")
check("Backup directory created", os.path.exists(backup_dir))
backups = os.listdir(backup_dir)
check("At least one backup file exists", len(backups) >= 1)

# Test 6 — Session logging
print("\n5. Session logging")
log_session_start(soul, model="llama3")
check("Session start logged", soul["session_log"][-1]["event"] == "session_start")
check("Model recorded in session start", soul["session_log"][-1]["model"] == "llama3")

log_session_end(soul)
check("Session end logged", soul["session_log"][-1]["event"] == "session_end")

# Test 7 — Memory writing
# Test 7 — Memory writing
print("\n6. Memory writing")
write_memory(
    soul,
    description="First conversation with companion",
    score=1.0,
    sharpness=0.9,
    emotional_context={
        "primary_emotion": "curiosity",
        "secondary_emotion": "affection",
        "override_strength": 0.72,
    },
    sensory_tags=["warmth", "novelty", "anticipation"],
    topic_tags=["first meeting", "companion", "introduction"],
    immediate=True,
)
write_memory(
    soul,
    description="Companion shared something personal",
    score=0.64,
    sharpness=0.5,
    emotional_context={
        "primary_emotion": "affection",
        "secondary_emotion": "curiosity",
        "override_strength": 0.45,
    },
    sensory_tags=["intimacy", "trust", "quiet"],
    topic_tags=["relationship", "personal", "disclosure"],
)

check("Two memories written", len(soul["long_term_memories"]) == 2)
check("First memory has correct score", soul["long_term_memories"][0]["importance"] == 1.0)
check("First memory sharpness set correctly", soul["long_term_memories"][0]["sharpness"] == 0.9)
check("First memory has emotional context", soul["long_term_memories"][0]["emotional_context"]["primary_emotion"] == "curiosity")
check("First memory has sensory tags", "warmth" in soul["long_term_memories"][0]["sensory_tags"])
check("First memory has topic tags", "first meeting" in soul["long_term_memories"][0]["topic_tags"])
check("First memory triggers starts empty", soul["long_term_memories"][0]["triggers"] == [])
check("First memory flagged as immediate write", soul["long_term_memories"][0]["immediate_write"] == True)
check("Second memory sharpness set correctly", soul["long_term_memories"][1]["sharpness"] == 0.5)
check("Second memory not flagged as immediate", soul["long_term_memories"][1]["immediate_write"] == False)

# ─── CLEANUP ──────────────────────────────────────────────────────────────────

shutil.rmtree(test_dir)

# ─── SUMMARY ──────────────────────────────────────────────────────────────────

print(f"\n─── {passed} passed, {failed} failed ───────────────────────────────────\n")