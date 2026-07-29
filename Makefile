.PHONY: setup migrate seed run test check preflight qa

PORT ?= 8000

setup:
	python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt
	.venv/bin/python manage.py migrate
	.venv/bin/python manage.py seed_demo_data

migrate:
	.venv/bin/python manage.py migrate

seed:
	.venv/bin/python manage.py seed_demo_data

run:
	.venv/bin/python manage.py runserver 127.0.0.1:$(PORT)

test:
	.venv/bin/python manage.py test accounts catalog orders core dashboard --verbosity 2

check:
	.venv/bin/python manage.py check
	.venv/bin/python manage.py makemigrations --check --dry-run

preflight:
	.venv/bin/python scripts/preflight.py

qa:
	PYTHON_BIN=.venv/bin/python ./scripts/qa_all.sh
