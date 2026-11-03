# v0.8 Proto Freeze

Frozen: 2026-11-03
Tag: `v0.8-proto-final`
Branch: `proto`
Default branch at freeze: `master`

Single-model baseline of the Pria Project, before the Triarchic architecture work. Kept for comparison with later versions.

## Baseline model

`dolphin3:latest` (digest `d5ab9ae8e1f2`, 4.9 GB), as set by `MODEL_NAME` in `demiurge.py`.

Other models installed on the development machine at freeze time (not part of the baseline):

| Model | Digest | Size |
|---|---|---|
| deepseek-r1:7b | 755ced02ce7b | 4.7 GB |
| qwen2.5-coder:7b | dae161e27b0e | 4.7 GB |

## Python

Python 3.14.4. Dependencies: see `requirements-frozen.txt`.

## Kokoro files (not in git)

| File | SHA256 |
|---|---|
| kokoro-v1.0.onnx | 7d5df8ecf7d4b1878015a32686053fd0eebe2bc377234608764cc0ef3636a6c5 |
| voices-v1.0.bin | bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d |

Whisper STT model: `base` (set in `voice.py`).

## Configuration at freeze

`demiurge.py`:

```
SOUL_FILE_PATH = "soul.json"
MODEL_NAME = "dolphin3:latest"
OLLAMA_HOST = "http://localhost:11434"
CONTEXT_WINDOW_LIMIT = 4096
VOICE_OUTPUT = True
VOICE_INPUT = False
VOICE_SPEED = 1.0
```

`adapters/ollama.py`:

```
REQUEST_TIMEOUT = 300
```

## Pria archived (not in git)

Soul files for Kairos, Dolphin, and Friction, with their `backups/` folders, are archived outside the repository. Soul files are gitignored and are not part of this tag.

## Changes in this freeze

- Removed the private physiology and primal drive modules and every hook into them.
- Removed the duplicate `evaluate_exchange()` call in `demiurge.py`.
- Fixed the `full_prompt` indentation bug in `demiurge.py`.
- Fixed the `.gitignore` README line.
- Added `emotional_engine/modulation.py` to version control.
- Stopped tracking `__pycache__` files.

## Known issues carried into the baseline

- Dream buffer expiry is not rechecked during a running API session.
- Soul file backups are never rotated or pruned.
- `api.py` has not had a full audit.
