@echo off
cd /d "%~dp0"
echo Starting local STT/TTS smoke test...
python tools\audio_smoke_test.py
pause
