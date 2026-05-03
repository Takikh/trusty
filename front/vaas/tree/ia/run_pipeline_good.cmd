@echo off
cd /d "%~dp0"
echo Running GOOD doctor pipeline (with built-in camera expression monitor)...
python main.py --doctor demo\good_doctor
pause
