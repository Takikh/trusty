@echo off
cd /d "%~dp0"
echo Running GOOD doctor pipeline with external expression monitor mode...
echo Start run_expression_monitor.cmd in another CMD window before continuing.
python main.py --doctor demo\good_doctor --external-expression
pause
