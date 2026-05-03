"""
Quick standalone test for the gapless TTS fix.
Run: python tools/tts_gap_test.py
It speaks a long multi-sentence text. You should hear NO pause between sentences.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import asyncio
from audio.tts_kokoro.tts import speak, preload

TEST_TEXT = (
    "Good morning, Doctor. Thank you for joining us today. "
    "I wanted to start by asking you about your time at the university. "
    "Could you recall a few of the subjects you studied in your fourth year of medicine, "
    "and tell me which one had the most impact on your clinical thinking? "
    "Take your time — there is no rush at all."
)

async def main():
    print("[test] Preloading Kokoro model...")
    preload()
    print("[test] Speaking multi-sentence test. Listen for gaps between sentences.")
    print(f"[test] Text: {TEST_TEXT}\n")
    await speak(TEST_TEXT)
    print("[test] Done. Did you hear any gaps?")

asyncio.run(main())
