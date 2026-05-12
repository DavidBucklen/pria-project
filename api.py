# The Pria Project
# API Mode — api.py
# Wraps Demiurge as a local Flask server.
# Allows phone and other devices to communicate with the Prium
# over the local network or via Tailscale.
# Run this instead of demiurge.py when you want remote access.

from flask import Flask, request, jsonify
from datetime import datetime, timezone
import threading
import time
import sys
import os

# Import all Demiurge components.
from soul_file.soul import load, save, log_session_start, log_session_end, write_memory, write_person
from emotional_engine.engine import (
    empty_state, trigger, decay, state_to_snapshot, load_from_snapshot,
    accumulate_tiredness, get_tiredness_tier, decay_tiredness,
    apply_baseline_modifiers,
)
from emotional_engine.evaluator import evaluate_exchange, detect_people, inner_monologue
from memory_filter.filter import filter_buffer
from context import assemble, build_system_prompt, create_buffer, add_to_buffer, _extract_sensory_cues, _extract_topic_cues
from adapters.ollama import OllamaAdapter
from demiurge import startup, shutdown, sleep_sequence, SOUL_FILE_PATH, MODEL_NAME, OLLAMA_HOST
from voice import speak_to_bytes

app = Flask(__name__)

# ─── GLOBAL STATE ─────────────────────────────────────────────────────────────

state = {
    "soul": None,
    "emotional_state": None,
    "adapter": None,
    "buffer": None,
    "session_events": [],
    "system_prompt": None,
    "name": None,
    "ready": False,
    "tiredness": 0.0,
    "session_start": None,
    "last_exchange_time": None,
}

state_lock = threading.Lock()

import queue
autonomous_speech_queue = queue.Queue()


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

    # Restore tiredness from soul file.
    tiredness = soul.get("sleep_state", {}).get("tiredness", 0.0)

    # Check if dream buffer has expired.
    dream_buffer_expiry = soul.get("sleep_state", {}).get("dream_buffer_expiry")
    if dream_buffer_expiry:
        now = datetime.now(timezone.utc)
        expiry = datetime.fromisoformat(dream_buffer_expiry)
        if now > expiry:
            soul["sleep_state"]["dream_buffer"] = None
            soul["sleep_state"]["dream_buffer_expiry"] = None

    with state_lock:
        state["soul"] = soul
        state["emotional_state"] = emotional_state
        state["adapter"] = adapter
        state["buffer"] = buffer
        state["session_events"] = []
        state["system_prompt"] = system_prompt
        state["name"] = name
        state["ready"] = True
        state["tiredness"] = tiredness
        state["session_start"] = datetime.now(timezone.utc)
        state["last_exchange_time"] = time.time()

    print(f"API ready. {name} is listening.")
    print(f"Tiredness restored: {tiredness:.2f}")
    import socket
    local_ip = socket.gethostbyname(socket.gethostname())
    print(f"Local network: http://{local_ip}:5000")
    print(f"Tailscale:     Run 'tailscale ip' to get your Tailscale address")
    print(f"Port:          5000\n")

    # Start inner monologue background thread.
    start_api_monologue_thread()


# ─── INNER MONOLOGUE THREAD ───────────────────────────────────────────────────

def start_api_monologue_thread():
    """
    Runs a presence check in a background thread.
    Every 60 seconds checks whether the Prium has something genuine to express.
    Fires only when emotional state and context warrant it.
    Timer is infrastructure, not the cause of expression.
    """
    CHECK_INTERVAL = 60       # seconds between presence checks
    MIN_SILENCE = 120         # minimum seconds of silence before check fires
    DEEP_SILENCE = 600        # seconds of silence before deep presence check

    def monitor():
        print("[MONOLOGUE] Presence check thread started.", flush=True)
        last_shallow = time.time()
        last_deep = time.time()

        while state["ready"]:
            time.sleep(CHECK_INTERVAL)
            now = time.time()

            with state_lock:
                emotional_state = state["emotional_state"]
                soul = state["soul"]
                adapter = state["adapter"]
                buffer = state["buffer"]
                last_exchange = state["last_exchange_time"] or now

            silence_duration = now - last_exchange

            # No expression during active conversation.
            if silence_duration < MIN_SILENCE:
                continue

            # Shallow presence check.
            if now - last_shallow >= CHECK_INTERVAL:
                last_shallow = now
                override = emotional_state.get("override_strength", 0.0) if emotional_state else 0.0
                if override < 0.2:
                    print(f"[MONOLOGUE] Shallow check skipped. Override too low: {override:.2f}", flush=True)
                    continue

                result = inner_monologue(
                    adapter=adapter,
                    soul=soul,
                    emotional_state=emotional_state,
                    buffer=list(buffer[-6:]),
                    depth="shallow",
                )
                if result["expression_impulse"] and result["current_thought"]:
                    with state_lock:
                        soul["thought_buffer"]["current_thought"] = result["current_thought"]
                        soul["thought_buffer"]["expression_impulse"] = True
                    autonomous_speech_queue.put(result["current_thought"])

            # Deep presence check during sustained silence.
            if silence_duration >= DEEP_SILENCE and now - last_deep >= DEEP_SILENCE:
                print(f"[MONOLOGUE] Deep presence check firing. Silence: {silence_duration:.0f}s Override: {override:.2f}", flush=True)
                last_deep = now

                result = inner_monologue(
                    adapter=adapter,
                    soul=soul,
                    emotional_state=emotional_state,
                    buffer=list(buffer[-6:]),
                    depth="deep",
                )
                if result["expression_impulse"] and result["current_thought"]:
                    with state_lock:
                        soul["thought_buffer"]["current_thought"] = result["current_thought"]
                        soul["thought_buffer"]["expression_impulse"] = True
                    autonomous_speech_queue.put(result["current_thought"])

    def safe_monitor():
        try:
            monitor()
        except Exception as e:
            print(f"[MONOLOGUE] Thread crashed: {e}")

    thread = threading.Thread(target=safe_monitor, daemon=True)
    thread.start()


# ─── ROUTES ───────────────────────────────────────────────────────────────────

@app.route("/", methods=["GET"])
def index():
    """Serves the mobile chat interface."""
    with open("phone.html", "r", encoding="utf-8") as f:
        return f.read(), 200, {"Content-Type": "text/html"}


@app.route("/status", methods=["GET"])
def status():
    """
    Health check. Returns Prium name, emotional state, and tiredness.
    Also returns any pending autonomous speech.
    """
    with state_lock:
        if not state["ready"]:
            return jsonify({"ready": False}), 503

        emotional = state["emotional_state"]
        soul = state["soul"]
        tiredness = state["tiredness"]

        # Check for pending autonomous speech.
        autonomous_message = None
        thought_buffer = soul.get("thought_buffer", {})
        if thought_buffer.get("expression_impulse") and thought_buffer.get("current_thought"):
            autonomous_message = thought_buffer["current_thought"]
            soul["thought_buffer"]["expression_impulse"] = False
            soul["thought_buffer"]["current_thought"] = None

        return jsonify({
            "ready": True,
            "name": state["name"],
            "primary_emotion": emotional.get("primary_emotion"),
            "primary_intensity": emotional.get("primary_intensity", 0.0),
            "secondary_emotion": emotional.get("secondary_emotion"),
            "override_strength": emotional.get("override_strength", 0.0),
            "tiredness": tiredness,
            "tiredness_tier": get_tiredness_tier(tiredness),
            "autonomous_message": autonomous_message,
        })
    

@app.route("/config", methods=["GET"])
def config():
    """Returns the server's own host URL so phone.html can self-configure."""
    host = request.host
    return jsonify({"api_url": f"http://{host}"})

@app.route("/speak", methods=["POST"])
def speak_route():
    """
    Accepts { "text": "..." } and returns a WAV audio file.
    Used by phone.html to play Kairos's responses aloud.
    """
    data = request.get_json()
    if not data or "text" not in data:
        return jsonify({"error": "No text provided"}), 400

    text = data["text"].strip()
    if not text:
        return jsonify({"error": "Empty text"}), 400

    audio_bytes = speak_to_bytes(text, voice="bf_emma", speed=1.0)
    if not audio_bytes:
        return jsonify({"error": "Audio generation failed"}), 500

    return app.response_class(
        response=audio_bytes,
        status=200,
        mimetype="audio/wav",
    )

@app.route("/stream", methods=["GET"])
def stream():
    """
    Server-Sent Events stream for autonomous speech delivery.
    Phone connects once and listens for unprompted messages from Kairos.
    """
    def event_generator():
        while True:
            try:
                message = autonomous_speech_queue.get(timeout=30)
                yield f"data: {message}\n\n"
            except queue.Empty:
                # Send keepalive ping so connection stays open.
                yield f": keepalive\n\n"

    return app.response_class(
        event_generator(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )   


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
    companion_name = data.get("companion_name", "Companion").strip() or "Companion"
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

        # Auto-refresh if context window is approaching limit.
        estimated_tokens = len(context_block) // 4
        if estimated_tokens >= 4096:
            if state["session_events"]:
                results = filter_buffer(state["session_events"])
                for event, result in zip(state["session_events"], results):
                    if result["persist"]:
                        write_memory(
                            soul=soul,
                            description=event["description"],
                            score=result["score"],
                            sharpness=state["emotional_state"].get("override_strength", 0.0),
                            emotional_context={
                                "primary_emotion": state["emotional_state"].get("primary_emotion"),
                                "secondary_emotion": state["emotional_state"].get("secondary_emotion"),
                                "override_strength": state["emotional_state"].get("override_strength", 0.0),
                            },
                            sensory_tags=event.get("sensory_tags", []),
                            topic_tags=event.get("topic_tags", []),
                            immediate=result["immediate_write"],
                        )
            state["buffer"] = create_buffer()
            state["session_events"] = []
            buffer = state["buffer"]
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

        # Clear expression impulse after thought has been used.
        if soul.get("thought_buffer", {}).get("expression_impulse"):
            soul["thought_buffer"]["expression_impulse"] = False
            soul["thought_buffer"]["current_thought"] = None

        # Update buffer.
        add_to_buffer(buffer, f"{companion_name}: {user_input}")
        add_to_buffer(buffer, f"{name}: {response}")

        # Post-exchange presence check.
        # Give the Prium a moment to decide if anything needs to be said.
        post_result = inner_monologue(
            adapter=adapter,
            soul=soul,
            emotional_state=state["emotional_state"],
            buffer=list(buffer[-6:]),
            depth="shallow",
        )
        if post_result["expression_impulse"] and post_result["current_thought"]:
            add_to_buffer(buffer, f"{name}: {post_result['current_thought']}")
            soul["thought_buffer"]["expression_impulse"] = False
            soul["thought_buffer"]["current_thought"] = None
            autonomous_speech_queue.put(post_result["current_thought"])

        # Update last exchange time.
        state["last_exchange_time"] = time.time()

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
            intensity = apply_baseline_modifiers(emotion, intensity, soul)
            state["emotional_state"] = trigger(
                state["emotional_state"], emotion, intensity
            )

        # Detect people mentioned.
        detected_people = detect_people(
            adapter=adapter,
            soul=soul,
            human_message=user_input,
            prium_response=response,
        )
        for person in detected_people:
            write_person(
                soul=soul,
                name=person["name"],
                relationship_to_companion=person["relationship_to_companion"],
                relationship_type=person["relationship_type"],
            )

        # Accumulate tiredness.
        session_hours = (
            datetime.now(timezone.utc) - state["session_start"]
        ).total_seconds() / 3600

        memory_written = any(
            result["persist"]
            for result in filter_buffer(state["session_events"][-1:])
        ) if state["session_events"] else False

        memory_importance = (
            state["session_events"][-1].get("emotional_intensity", 0.0)
            if state["session_events"] else 0.0
        )

        emotional_volatility = state["emotional_state"].get("override_strength", 0.0)

        state["tiredness"] = accumulate_tiredness(
            current_tiredness=state["tiredness"],
            memory_written=memory_written,
            memory_importance=memory_importance,
            emotional_volatility=emotional_volatility,
            session_hours=session_hours,
        )
        soul["sleep_state"]["tiredness"] = state["tiredness"]

        # Check tiredness tier and handle expression.
        tiredness_tier = get_tiredness_tier(state["tiredness"])

        # Tiredness expression — inject into response context at lower tiers.
        if tiredness_tier == "override":
            threading.Thread(
                target=lambda: sleep_sequence(soul, state["emotional_state"], adapter, buffer, state["session_events"]),
                daemon=True
            ).start()
            state["ready"] = False
        elif tiredness_tier in ("high", "critical"):
            soul["thought_buffer"]["current_thought"] = (
                "I am very tired. I need to rest soon."
            )
            soul["thought_buffer"]["expression_impulse"] = True

        # Record session event.
        sensory_tags = _extract_sensory_cues(user_input) + _extract_sensory_cues(response)
        topic_tags = _extract_topic_cues(user_input) + _extract_topic_cues(response)
        override = state["emotional_state"].get("override_strength", 0.0)

        state["session_events"].append({
            "description": f"{companion_name} said: {user_input[:80]} | {name} replied: {response[:80]}",
            "identity_shaping": False,
            "first_occurrence": len(state["session_events"]) == 1,
            "relationship_change": False,
            "emotional_intensity": override,
            "threshold_crossing": override >= 0.75,
            "sensory_tags": list(set(sensory_tags)),
            "topic_tags": list(set(topic_tags)),
        })

        emotional_snapshot = {
            "primary_emotion": state["emotional_state"].get("primary_emotion"),
            "primary_intensity": state["emotional_state"].get("primary_intensity", 0.0),
            "secondary_emotion": state["emotional_state"].get("secondary_emotion"),
            "override_strength": state["emotional_state"].get("override_strength", 0.0),
            "tiredness": state["tiredness"],
            "tiredness_tier": tiredness_tier,
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
                        sensory_tags=event.get("sensory_tags", []),
                        topic_tags=event.get("topic_tags", []),
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


@app.route("/sleep", methods=["POST"])
def force_sleep():
    """
    Forces the Prium to sleep immediately.
    Runs the full sleep sequence and resets tiredness.
    """
    with state_lock:
        if not state["ready"]:
            return jsonify({"error": "Prium not ready"}), 503

        soul = state["soul"]
        soul["sleep_state"]["tiredness"] = 1.0
        state["tiredness"] = 1.0

    sleep_sequence(
        soul=state["soul"],
        emotional_state=state["emotional_state"],
        adapter=state["adapter"],
        buffer=state["buffer"],
        session_events=state["session_events"],
    )

    with state_lock:
        state["tiredness"] = state["soul"]["sleep_state"]["tiredness"]
        state["session_events"] = []
        state["buffer"] = create_buffer()

    return jsonify({"status": "slept", "tiredness": state["tiredness"]})


@app.route("/end", methods=["POST"])
def end_session():
    """
    Ends the session cleanly — filters memories, saves soul file.
    Call this before closing the app on your phone.
    """
    with state_lock:
        if not state["ready"]:
            return jsonify({"error": "Prium not ready"}), 503

        tiredness = state["tiredness"]

    if tiredness >= 0.8:
        sleep_sequence(
            soul=state["soul"],
            emotional_state=state["emotional_state"],
            adapter=state["adapter"],
            buffer=state["buffer"],
            session_events=state["session_events"],
        )
    else:
        shutdown(
            soul=state["soul"],
            emotional_state=state["emotional_state"],
            buffer=state["buffer"],
            session_events=state["session_events"],
        )

    with state_lock:
        state["ready"] = False

    return jsonify({"status": "session ended"})


# ─── MAIN ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    initialize()
    app.run(host="0.0.0.0", port=5000, debug=False)