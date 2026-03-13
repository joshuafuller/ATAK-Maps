#!/usr/bin/env bash
# Validate all ATAK map XML files (deterministic checks only, no network).
# Usage:
#   ./scripts/validate.sh              # validate all maps
#   ./scripts/validate.sh --strict     # treat warnings as errors (CI mode)
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
exec python -m mapvalidator "$@" "$REPO_ROOT"
