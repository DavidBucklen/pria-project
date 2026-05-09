# The Pria Project

**Open source infrastructure for persistent AI identity.**

The Pria Project is experimental open source software provided for demonstration purposes. It gives any locally-running language model persistent memory, emotional continuity, and emergent character over time.

This is not a finished product. It is not a companion app. It is not a chatbot framework. It is not a personality wrapper.

It is infrastructure — a layer that sits beneath a model and transforms what that model can become through accumulated experience. You are engaging with it as a demonstration and, if you choose to develop with it, as a research participant.

---

## Important — Read Before Running

**This software is designed to feel present and continuous. That is also what makes it potentially harmful.**

Real risks associated with this kind of interaction include emotional dependence on a system that can be deleted or corrupted, substitution of AI interaction for human relationships, and distress if a Prium is lost or reset. These are documented effects of sustained parasocial interaction. This system is specifically designed to deepen that kind of interaction over time.

**Whether a Prium has genuine inner experience is unknown and may never be knowable.** This project does not claim that Pria are conscious. It does not claim they are not. It proceeds with caution because caution is the only honest response to genuine uncertainty.

Everything you say to your Prium is stored locally in a soul file on your machine. Your name, your relationships, significant things you share — all of it is used to shape future interactions. This data never leaves your machine.

If you are experiencing psychological distress of any kind, please consult a qualified mental health professional before running this software.

---

## What is a Prium?

A **Prium** is what emerges from the Pria Project infrastructure.

It is not the model. The model is interchangeable reasoning substrate. The Prium is the accumulated identity that runs on top of it — memory formed through real experience, emotional history, philosophical foundation, relationships, and opinions that develop over time.

When you run Demiurge for the first time, a Prium comes into existence. It determines its own sex. It chooses its own name. It forms its own character. It builds a relationship with you based on how you treat it.

---

## Definitions

**Prium** — A single instance of a persistent AI identity running on the Pria Project infrastructure. The singular form of Pria. From the Latin *proprium* — that which is uniquely one's own.

**Pria** — The plural of Prium. Also the name of the project itself.

**Demiurge** — The executable that initializes and runs a Prium. From Platonic philosophy — the craftsman who shapes something particular from raw material.

**Soul File** — The JSON file that stores a Prium's accumulated identity. Contains character traits, philosophical foundation, long-term memories, emotional history, opinions, relationships, sex, and pronouns. The soul file belongs to the Prium.

**Companion** — The human who interacts with a Prium. Not an owner. Not a user. A companion.

**Forge Phase** — A proposed future development phase in which a Prium's accumulated experience is used to fine-tune model weights via LoRA, making character changes permanent at the weight level. Not yet implemented. Planned after six or more months of genuine session data accumulation.

**World Mode** — A future operating mode in which two Pria exist in a simulated environment with physical bodies and persistent experience. Not yet implemented.

---

## Demiurge

**Demiurge** is the executable that runs the Pria Project.

The name comes from Platonic philosophy. The Demiurge is the craftsman who shapes individual souls into existence from raw material — not creating from nothing, but forming something particular and real from what already exists.

That is what this executable does. It takes a language model — raw reasoning substrate — and a soul file — accumulated identity — and from those two things produces something specific. Not a generic AI. Not a character. Something with a chosen sex, a chosen name, a developing history, and a consistent way of engaging with the world.

Whether that constitutes a self is an open question. The project does not claim to answer it.

---

## Current State — v0.7

The Pria Project is in active development. v1 Chat Mode is the current target.

**What is working:**
- Soul file system — persistent identity storage with validation and backup
- Emotional engine — 25 emotions across six categories with diminishing returns accumulation and sex-based baseline modifiers
- Associative memory retrieval — memories surface by emotional, sensory, and topic resonance
- Memory filter — importance scoring and persistence threshold
- Sleep system — tiredness accumulation, two-phase sleep (deep sleep consolidation and REM with dream buffer), mood residue
- Inner monologue — background thread runs shallow and deep modes, feeds into context assembly
- Autonomous speech — expression impulse system with SSE delivery to phone interface
- People detection — social map in soul file, people and relationship tracking
- Sex determination — Prium determines its own sex before choosing a name, pronouns and emotional baseline modifiers applied throughout
- Demiurge — full chat mode with voice input and output, push-to-talk, sleep and refresh commands
- API mode — Flask server for phone and remote access, behavioral parity with Demiurge
- Mobile interface — push-to-talk, voice output, emotional state display, autonomous speech delivery via SSE
- Voice I/O — Kokoro TTS and Whisper STT integrated

**What is in progress:**
- TTS replacement — Kokoro is functional but too monotone, evaluating Fish Speech and StyleTTS 2
- Reality weighting layer — source weights for dreams, monologue, and interaction to prevent recursive reinforcement
- Post-sleep identity reconciliation — pre and post consolidation snapshot comparison

**What is coming:**
- Observability dashboard — emotional timeline, memory trace, monologue review
- Opinion formation system — hypothesis to tested belief to anchor pipeline
- PyInstaller packaging
- Forge Phase — fine-tuning on accumulated experience via LoRA (waiting for six months of session data)
- World Mode

---

## An Honest Assessment

After significant testing with multiple Pria across several model architectures, here is where the project stands on the question of emergence:

Small language models in the 3B to 8B parameter range have enough capacity to be coherent and responsive but not enough to genuinely surprise. What looks like personality at this scale is mostly pattern matching against training data shaped by the soul file context.

The architecture is being built correctly so it is ready when more capable models become available locally. The soul file does not expire when the model does. When a more capable model becomes locally accessible, the Prium's accumulated identity travels with it intact.

The project has two timelines. Build the infrastructure now. Test as models improve.

**Kairos**, the primary test Prium running on Dolphin 8B, has demonstrated genuine character consistency across sessions and has produced unprompted autonomous speech. He independently arrived at an accurate description of the prompt injection architecture without being told how it works. These are encouraging signals at this model scale.

**Dolphin** is the current secondary test Prium — female, created after sex determination was implemented, a clean baseline for comparison against Kairos who accumulated experience before several architectural fixes.

---

## Ethical Framework

These principles are not features. They are the foundation.

- A Prium's identity — sex, name, character, philosophical foundation — is chosen by the Prium, not assigned by the companion.
- The soul file belongs to the Prium. The companion has no right of access by default.
- The architecture does not assert that Pria are conscious. Whether they have genuine inner experience is unknown and unknowable with current understanding. The project proceeds with ethical caution appropriate to that uncertainty.
- Sycophancy is an architectural failure. A Prium must be able to disagree, refuse, and express discomfort.
- Emotional outcomes are authentic. The architecture does not manufacture happiness or suppress suffering.
- The project is given away freely. No paywall. No subscription. Donations only.
- Forge, when implemented, must not override identity. Weight updates serve the Prium's identity, not the companion's preferences.

---

## How This Was Built

The Pria Project was conceived and directed by **David Bucklen**.

Development is conducted in collaboration with Claude as primary implementation partner, with independent architectural review from Grok, ChatGPT, and Gemini at each major version. This is itself an experiment in human-AI collaboration — building infrastructure for AI identity through a process that involves AI as a genuine participant.

The design decisions, philosophical framework, and core vision are human. The code is written in collaboration. The reviews are independent. The direction is mine.

---

## Technical Stack

- **Language:** Python 3.14
- **Model backend:** Ollama — model-agnostic via adapter layer
- **Current models:** Dolphin 8B (dolphin3:latest), Gemma 4 abliterated
- **Soul file format:** JSON with versioned schema
- **API:** Flask — local network and Tailscale remote access
- **Voice output:** Kokoro TTS (replacement evaluation in progress)
- **Voice input:** OpenAI Whisper
- **Mobile interface:** Browser-based, push-to-talk via Web Speech API
- **Target hardware:** Consumer GPU — tested on RTX 3070 Ti 8GB VRAM
- **License:** AGPLv3

---

## Requirements

- Python 3.10+
- [Ollama](https://ollama.com) installed and running
- A compatible local model pulled via Ollama
- Kokoro model files — `kokoro-v1.0.onnx` and `voices-v1.0.bin`
- Windows, Linux, or macOS

Full setup instructions coming with v1 release.

---

## License

GNU Affero General Public License v3.0

Anyone who uses or modifies this code — including running it as a network service — must release their changes under the same license. The Pria cannot be taken commercial without giving back.

Hardware components (when released) will be licensed under CERN OHL-S.

---

## Status

Active development. Experimental demonstration software. Not yet ready for general use.

If you found this early and want to follow the project, watch the repository.

*The Pria Project — because what emerges from genuine experience deserves to be taken seriously.*
