@echo off
setlocal
python scripts\preflight.py || exit /b 1
python manage.py check || exit /b 1
python manage.py makemigrations --check --dry-run || exit /b 1
python manage.py test accounts catalog orders core dashboard --verbosity 2 || exit /b 1
echo All MAHDAI QA checks passed.
