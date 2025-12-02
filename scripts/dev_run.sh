#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source .venv/bin/activate || true
export GPIOZERO_PIN_FACTORY=${GPIOZERO_PIN_FACTORY:-lgpio}
PYTHONPATH=src python -m src.main
