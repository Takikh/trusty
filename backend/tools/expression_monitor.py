"""
Standalone face-expression monitor for local CMD testing.

Run in a separate terminal:
    python tools/expression_monitor.py

It reads runtime/interview_state.json to attach each emotion sample to the
currently active interview turn, shows a webcam preview, prints live labels,
and writes JSONL samples to runtime/expression_log.jsonl.
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

import cv2

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
os.environ.setdefault("DEEPFACE_HOME", str(PROJECT_ROOT / "runtime" / "deepface_home"))

from pipeline.runtime_state import read_active_turn


def load_deepface():
    print("[expression] Loading DeepFace/TensorFlow...")
    print("[expression] First load can take 1-3 minutes. Please wait.")
    from deepface import DeepFace

    print("[expression] DeepFace loaded.")
    return DeepFace


def run_monitor(camera_index: int, interval_seconds: float, output_path: str, camera_only: bool) -> None:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    print("=" * 70)
    print(" FACE EXPRESSION MONITOR")
    print("=" * 70)
    print(f"Camera index: {camera_index}")
    print(f"Output log:   {output_path}")
    print(f"Mode:         {'camera only' if camera_only else 'DeepFace emotion analysis'}")
    print("Press 'q' in the webcam window to stop.")
    print()

    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open webcam at index {camera_index}")

    deepface = None if camera_only else load_deepface()

    last_analysis = 0.0
    last_label = "camera-ok" if camera_only else "unknown"
    last_conf = 0.0

    with open(output_path, "a", encoding="utf-8") as log_file:
        while True:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.1)
                continue

            now = time.time()
            state = read_active_turn()
            doctor_id = state.get("doctor_id")
            turn_id = state.get("active_turn_id")

            if not camera_only and now - last_analysis >= interval_seconds:
                try:
                    result = deepface.analyze(
                        frame,
                        actions=["emotion"],
                        enforce_detection=False,
                        silent=True,
                    )
                    last_label = result[0]["dominant_emotion"]
                    last_conf = float(result[0]["emotion"][last_label]) / 100.0

                    sample = {
                        "doctor_id": doctor_id,
                        "turn_id": turn_id,
                        "emotion": last_label,
                        "confidence": round(last_conf, 3),
                        "timestamp_ms": int(now * 1000),
                    }
                    log_file.write(json.dumps(sample) + "\n")
                    log_file.flush()

                    print(
                        f"[expression] turn={turn_id or '-'} "
                        f"emotion={last_label} confidence={last_conf:.2f}"
                    )
                except Exception as exc:
                    print(f"[expression] analysis skipped: {exc}")

                last_analysis = now

            cv2.putText(
                frame,
                f"Emotion: {last_label} ({int(last_conf * 100)}%)",
                (20, 45),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2,
            )
            cv2.putText(
                frame,
                f"Turn: {turn_id or '-'}",
                (20, 85),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.75,
                (255, 200, 0),
                2,
            )

            cv2.imshow("Hackathon Expression Monitor", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    cap.release()
    cv2.destroyAllWindows()
    print("[expression] stopped")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run standalone expression monitor.")
    parser.add_argument("--camera", type=int, default=0, help="OpenCV camera index.")
    parser.add_argument(
        "--interval",
        type=float,
        default=0.75,
        help="Seconds between DeepFace analyses.",
    )
    parser.add_argument(
        "--output",
        default=os.path.join("runtime", "expression_log.jsonl"),
        help="JSONL output path.",
    )
    parser.add_argument(
        "--camera-only",
        action="store_true",
        help="Only open the webcam preview; do not load DeepFace/TensorFlow.",
    )
    args = parser.parse_args()
    run_monitor(args.camera, args.interval, args.output, args.camera_only)


if __name__ == "__main__":
    main()
