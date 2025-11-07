#!/usr/bin/env bash
set -o errexit

# Install Python 3.11 manually


python --version
pip install --upgrade pip
pip install -r requirements.txt

# Start the app
exec python -m gunicorn backend.app:app

