#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt
# Placeholder for future migrations
# python -m alembic upgrade head
