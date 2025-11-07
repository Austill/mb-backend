#!/usr/bin/env bash
set -o errexit

# Install Python 3.11 manually
echo "Installing Python 3.11.8 manually..."
curl -fsSL https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -o miniconda.sh
bash miniconda.sh -b -p $HOME/miniconda
export PATH="$HOME/miniconda/bin:$PATH"
conda install -y python=3.11

python --version
pip install --upgrade pip
pip install -r requirements.txt

# Start the app
exec gunicorn backend.app:app --bind 0.0.0.0:"${PORT:-5000}" --workers 3 --timeout 120

