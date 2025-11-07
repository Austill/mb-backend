#!/usr/bin/env bash
set -o errexit

# Install Python 3.11 manually
echo "Installing Python 3.11.8 manually..."


python --version
pip install --upgrade pip
pip install -r requirements.txt

# Start the app
exec gunicorn run:app -b 0.0.0.0:5000
