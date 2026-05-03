"""
Small file-based state used by local test commands.

It lets a separate expression-monitor process know which interview turn is
currently active without requiring sockets, Redis, or a server.
"""
import json
import os
import time


RUNTIME_DIR = os.getenv("RUNTIME_DIR", "runtime")
STATE_PATH = os.path.join(RUNTIME_DIR, "interview_state.json")


def set_active_turn(doctor_id: str, turn_id: str | None) -> None:
    os.makedirs(RUNTIME_DIR, exist_ok=True)
    state = {
        "doctor_id": doctor_id,
        "active_turn_id": turn_id,
        "updated_at_ms": int(time.time() * 1000),
    }
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def clear_active_turn(doctor_id: str) -> None:
    set_active_turn(doctor_id, None)


def read_active_turn() -> dict:
    try:
        with open(STATE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"doctor_id": None, "active_turn_id": None, "updated_at_ms": None}
    except json.JSONDecodeError:
        return {"doctor_id": None, "active_turn_id": None, "updated_at_ms": None}
