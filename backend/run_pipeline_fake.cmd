@echo off
cd /d "%~dp0"
echo Running FAKE doctor pipeline with external expression monitor mode...
echo Start run_expression_monitor.cmd in another CMD window before continuing.
python main.py --doctor demo\fake_doctor --external-expression
pause
