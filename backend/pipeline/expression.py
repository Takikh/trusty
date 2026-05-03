"""
Step 7 - expression.py
Background thread using DeepFace to read webcam frames and log emotions.
Synced to the current interview turn via active_turn_id.
"""
import threading
import time
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("DEEPFACE_HOME", str(PROJECT_ROOT / "runtime" / "deepface_home"))
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

try:
    import cv2
    from deepface import DeepFace
    DEEPFACE_AVAILABLE = True
except ImportError:
    import cv2
    DEEPFACE_AVAILABLE = False
    print("  [expression] WARNING: deepface not available. Using simulated emotion stream for demo.")


class ExpressionStream:
    def __init__(self):
        self.active_turn_id = None
        self.log            = []
        self._running       = False
        self._thread        = None

    def start(self):
        self._running = True
        self._thread  = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        print("  [expression] Expression stream started.")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=3)
        print(f"  [expression] Stopped. Total log entries: {len(self.log)}")

    def _loop(self):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("  [expression] WARNING: Cannot open webcam. Expression stream disabled.")
            return

        while self._running:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.2)
                continue

            try:
                if DEEPFACE_AVAILABLE:
                    result  = DeepFace.analyze(
                        frame,
                        actions=["emotion"],
                        enforce_detection=False,
                        silent=True
                    )
                    label = result[0]["dominant_emotion"]
                    conf  = result[0]["emotion"][label] / 100.0
                else:
                    import random
                    label = random.choice(["neutral", "neutral", "neutral", "fear", "happy"])
                    conf = random.uniform(0.75, 0.99)

                if self.active_turn_id:
                    self.log.append({
                        "turn_id":    self.active_turn_id,
                        "emotion":    label,
                        "confidence": round(conf, 3),
                        "timestamp_ms": int(time.time() * 1000)
                    })
                    
                # Draw on frame
                cv2.putText(frame, f"Emotion: {label} ({int(conf*100)}%)", (20, 50), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                cv2.putText(frame, f"Turn ID: {self.active_turn_id}", (20, 90), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 200, 0), 2)
            except Exception:
                pass

            cv2.imshow("Doctor Interview - Emotion Tracking", frame)
            
            # Press 'q' to quit window (though thread stops automatically)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            # Remove time.sleep(0.5) so video is smooth, deepface might make it slow anyway
            
        cap.release()
        cv2.destroyAllWindows()

    def get_summary(self) -> dict:
        """Returns per-turn emotion summary."""
        if not self.log:
            return {}

        from collections import Counter
        turns = {}
        for entry in self.log:
            tid = entry["turn_id"]
            if tid not in turns:
                turns[tid] = []
            turns[tid].append(entry["emotion"])

        summary = {}
        for tid, emotions in turns.items():
            counts  = Counter(emotions)
            dominant = counts.most_common(1)[0][0]
            stress_count = sum(counts.get(e, 0) for e in ["fear", "angry", "disgust"])
            total        = len(emotions)
            summary[tid] = {
                "dominant_emotion": dominant,
                "stress_ratio":     round(stress_count / total, 3) if total else 0.0,
                "sample_count":     total
            }
        return summary
