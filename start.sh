#!/usr/bin/env bash

# uv pip install -r requirements.txt && \
python manage.py makemigrations --verbosity 2 && \
python manage.py collectstatic && \
python manage.py migrate && \
# python manage.py migrate profiles && \
# python manage.py migrate management && \
python manage.py seed_all