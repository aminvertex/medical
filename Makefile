.PHONY: setup migrate seed run test check

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
	.venv/bin/python manage.py runserver

test:
	.venv/bin/python manage.py test

check:
	.venv/bin/python manage.py check
	.venv/bin/python manage.py makemigrations --check --dry-run
