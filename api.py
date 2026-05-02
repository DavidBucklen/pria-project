# The Pria Project
# API Mode — api.py
# Wraps Demiurge as a local Flask server.
# Allows phone and other devices to communicate with the Prium
# over the local network or via Tailscale.
# Run this instead of demiurge.py when you want remote access.

from flask import Flask, request, jsonify
from datetime import datetime, timezone
import threading
import sys
import os

# Import all Demiurge components.
from soul_file.soul import load, save, log_session_start, log_session_end, write_memory
from emotional_engine.engine import empty_state, trigger, decay, state_to_snapshot, load_from_snapshot
from emotional_engine.evaluator import evaluate_exchange
from memory_filter.filter import filter_buffer
from context import assemble, build_system_prompt, create_buffer, add_to_buffer
from adapters.ollama import OllamaAdapter
from demiurge import startup, shutdown, SOUL_FILE_PATH, MODEL_NAME, OLLAMA_HOST

app = Flask(__name__)

# ─── GLOBAL STATE ─────────────────────────────────────────────────────────────
# Single session state shared across all requests.

state = {
    "soul": None,
    "emotional_state": None,
    "adapter": None,
    "buffer": None,
    "session_events": [],
    "system_prompt": None,
    "name": None,
    "ready": False,
}

state_lock = threading.Lock()


# ─── INITIALIZATION ───────────────────────────────────────────────────────────

def initialize():
    """
    Runs the Demiurge startup sequence and populates global state.
    Called once when the server starts.
    """
    print("\n─── DEMIURGE API MODE ────────────────────────────────────────\n")

    soul, emotional_state, adapter, buffer = startup()
    system_prompt = build_system_prompt(soul)
    name = soul["identity"]["name"]

    with state_lock:
        state["soul"] = soul
        state["emotional_state"] = emotional_state
        state["adapter"] = adapter
        state["buffer"] = buffer
        state["session_events"] = []
        state["system_prompt"] = system_prompt
        state["name"] = name
        state["ready"] = True

    print(f"API ready. {name} is listening.")
    print(f"Connect from your phone at http://<your-local-ip>:5000\n")


# ─── ROUTES ───────────────────────────────────────────────────────────────────

@app.route("/", methods=["GET"])
def index():
    """Serves the mobile chat interface."""
    with open("phone.html", "r", encoding="utf-8") as f:
        return f.read(), 200, {"Content-Type": "text/html"}
    
@app.route("/status", methods=["GET"])
def status():
    """
    Health check. Returns Prium name and emotional state.
    """
    with state_lock:
        if not state["ready"]:
            return jsonify({"ready": False}), 503

        emotional = state["emotional_state"]
        return jsonify({
            "ready": True,
            "name": state["name"],
            "primary_emotion": emotional.get("primary_emotion"),
            "primary_intensity": emotional.get("primary_intensity", 0.0),
            "secondary_emotion": emotional.get("secondary_emotion"),
            "override_strength": emotional.get("override_strength", 0.0),
        })


@app.route("/chat", methods=["POST"])
def chat():
    """
    Main chat endpoint.
    Accepts: { "message": "your message here" }
    Returns: { "name": "...", "response": "...", "emotional_state": {...} }
    """
    data = request.get_json()
    if not data or "message" not in data:
        return jsonify({"error": "No message provided"}), 400

    user_input = data["message"].strip()
    if not user_input:
        return jsonify({"error": "Empty message"}), 400

    with state_lock:
        if not state["ready"]:
            return jsonify({"error": "Prium not ready"}), 503

        soul = state["soul"]
        adapter = state["adapter"]
        buffer = state["buffer"]
        name = state["name"]
        system_prompt = state["system_prompt"]

        # Decay emotional state.
        state["emotional_state"] = decay(state["emotional_state"])

        # Assemble context.
        context_block = assemble(
            soul=soul,
            emotional_state=state["emotional_state"],
            buffer=buffer,
            current_input=user_input,
            mode="chat",
        )

        # Build full prompt.
        full_prompt = f"{system_prompt}\n\n{context_block}"

        # Get response.
        response = adapter.complete(full_prompt)

        # Update buffer.
        add_to_buffer(buffer, f"You: {user_input}")
        add_to_buffer(buffer, f"{name}: {response}")

        # Evaluate emotional impact.
        emotion_triggers = evaluate_exchange(
            adapter=adapter,
            soul=soul,
            human_message=user_input,
            prium_response=response,
            current_emotional_state=state["emotional_state"],
        )

        # Apply triggers.
        for emotion, intensity in emotion_triggers:
            state["emotional_state"] = trigger(
                state["emotional_state"], emotion, intensity
            )

        # Record session event.
        override = state["emotional_state"].get("override_strength", 0.0)
        state["session_events"].append({
            "description": f"Companion said: {user_input[:100]}",
            "identity_shaping": False,
            "first_occurrence": len(state["session_events"]) == 0,
            "relationship_change": False,
            "emotional_intensity": override,
            "threshold_crossing": override >= 0.75,
        })

        emotional_snapshot = {
            "primary_emotion": state["emotional_state"].get("primary_emotion"),
            "primary_intensity": state["emotional_state"].get("primary_intensity", 0.0),
            "secondary_emotion": state["emotional_state"].get("secondary_emotion"),
            "override_strength": state["emotional_state"].get("override_strength", 0.0),
        }

        return jsonify({
            "name": name,
            "response": response,
            "emotional_state": emotional_snapshot,
        })


@app.route("/refresh", methods=["POST"])
def refresh():
    """
    Refreshes the context window while preserving soul file and emotional state.
    Equivalent to typing /refresh in chat mode.
    """
    with state_lock:
        if not state["ready"]:
            return jsonify({"error": "Prium not ready"}), 503

        soul = state["soul"]
        emotional_state = state["emotional_state"]
        session_events = state["session_events"]

        # Filter and write memories.
        if session_events:
            results = filter_buffer(session_events)
            for event, result in zip(session_events, results):
                if result["persist"]:
                    write_memory(
                        soul=soul,
                        description=event["description"],
                        score=result["score"],
                        sharpness=emotional_state.get("override_strength", 0.0),
                        emotional_context={
                            "primary_emotion": emotional_state.get("primary_emotion"),
                            "secondary_emotion": emotional_state.get("secondary_emotion"),
                            "override_strength": emotional_state.get("override_strength", 0.0),
                        },
                        immediate=result["immediate_write"],
                    )

        # Save emotional state.
        if "emotional_history" not in soul:
            soul["emotional_history"] = {}
        soul["emotional_history"]["current_state"] = state_to_snapshot(emotional_state)
        save(soul, SOUL_FILE_PATH)

        # Reset buffer and events.
        state["buffer"] = create_buffer()
        state["session_events"] = []

        return jsonify({"status": "refreshed", "name": state["name"]})


@app.route("/end", methods=["POST"])
def end_session():
    """
    Ends the session cleanly — filters memories, saves soul file.
    Call this before closing the app on your phone.
    """
    with state_lock:
        if not state["ready"]:
            return jsonify({"error": "Prium not ready"}), 503

        shutdown(
            soul=state["soul"],
            emotional_state=state["emotional_state"],
            buffer=state["buffer"],
            session_events=state["session_events"],
        )
        state["ready"] = False

        return jsonify({"status": "session ended"})


# ─── MAIN ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    initialize()
    app.run(host="0.0.0.0", port=5000, debug=False)