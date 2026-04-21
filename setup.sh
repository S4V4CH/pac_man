#!/usr/bin/env bash
# Entorno del proyecto Pac-Man Roguelike (Linux / macOS / Git Bash en Windows)
set -euo pipefail
cd "$(dirname "$0")"
python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
echo "Listo. Activa el entorno con: source .venv/bin/activate"
echo "Ejecuta el juego con: python src/main.py"
