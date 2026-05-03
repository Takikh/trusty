@echo off
cd /d "%~dp0"
echo Starting camera-only test...
echo Press q in the webcam window to stop.
python tools\expression_monitor.py --camera-only
pause
