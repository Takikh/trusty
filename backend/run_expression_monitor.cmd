@echo off
cd /d "%~dp0"
echo Starting standalone face expression monitor...
echo Press q in the webcam window to stop.
python tools\expression_monitor.py
pause
