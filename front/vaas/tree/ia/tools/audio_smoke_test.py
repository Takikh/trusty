"""
Local STT/TTS smoke test.

This intentionally prints each step so a CMD window shows whether Kokoro and
Whisper load correctly before running the full pipeline.
"""
import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.audio_io import audio_status, listen, preload_audio, speak


def main() -> None:
    parser = argparse.ArgumentParser(description="Test local STT/TTS.")
    parser.add_argument("--skip-speak", action="store_true", help="Do not play TTS.")
    parser.add_argument("--skip-listen", action="store_true", help="Do not record STT.")
    parser.add_argument("--timeout", type=int, default=8, help="STT listen timeout.")
    parser.add_argument("--tts-voice", default=None, help="Kokoro voice name.")
    parser.add_argument(
        "--text",
        default="Audio test ready. Kokoro text to speech is working.",
        help="Text to speak for the TTS test.",
    )
    args = parser.parse_args()

    print("=" * 70)
    print(" AUDIO SMOKE TEST")
    print("=" * 70)
    print(audio_status())
    print()

    print("[audio] Preloading models...")
    preload_audio()
    print("[audio] Preload complete.")

    if not args.skip_speak:
        print(f"[tts] Speaking test phrase with voice={args.tts_voice or 'default'}...")
        try:
            speak(args.text, voice=args.tts_voice)
            print("[tts] Done.")
        except Exception as exc:
            print(f"[tts] Failed: {exc}")
            print("[tts] Continuing so STT can still be tested.")

    if not args.skip_listen:
        print(f"[stt] Speak after the prompt. English mode. Timeout: {args.timeout} seconds.")
        text = listen(timeout=args.timeout)
        print(f"[stt] Transcript: {text}")

    print("[audio] Smoke test finished.")


if __name__ == "__main__":
    main()
