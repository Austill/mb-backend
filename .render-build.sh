#!/usr/bin/env bash
set -e

echo "=== Render build start ==="
python -m pip install --upgrade pip setuptools wheel
if [ -f requirements.txt ]; then
  echo "=== Installing requirements ==="
  pip install --no-cache-dir -r requirements.txt
fi

echo "=== Build finished ==="
