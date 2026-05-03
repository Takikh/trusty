@echo off
cd /d "%~dp0"
echo Running local project preflight check...
python tools\preflight_check.py --doctor demo\good_doctor
pause
