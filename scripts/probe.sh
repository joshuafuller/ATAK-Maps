#!/usr/bin/env bash
# Probe all tile servers for liveness (dual user-agent: TAK + browser).
# Usage:
#   ./scripts/probe.sh                 # validate + probe all maps
#   ./scripts/probe.sh --issues        # also create/close GitHub issues
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
exec python -m mapvalidator --probe "$@" "$REPO_ROOT"
