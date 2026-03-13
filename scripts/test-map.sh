#!/usr/bin/env bash
# Test a single XML map file — validates and probes the tile server.
# Usage:
#   ./scripts/test-map.sh Google/google_hybrid.xml
#   ./scripts/test-map.sh path/to/my_new_map.xml
set -euo pipefail

if [ $# -eq 0 ]; then
    echo "Usage: $0 <map-file.xml> [map-file2.xml ...]"
    echo ""
    echo "Validates XML structure and probes the tile server for each file."
    echo ""
    echo "Examples:"
    echo "  $0 Google/google_hybrid.xml"
    echo "  $0 ESRI/esri_clarity.xml Bing/Bing_Maps.xml"
    exit 1
fi

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OVERALL_EXIT=0

for MAP_FILE in "$@"; do
    # Resolve relative to repo root if not absolute
    if [[ "$MAP_FILE" != /* ]]; then
        MAP_FILE="$REPO_ROOT/$MAP_FILE"
    fi

    if [ ! -f "$MAP_FILE" ]; then
        echo "ERROR: File not found: $MAP_FILE"
        OVERALL_EXIT=1
        continue
    fi

    echo "======================================================================"
    echo "Testing: $(basename "$MAP_FILE")"
    echo "======================================================================"

    python -c "
import sys
from pathlib import Path
from mapvalidator.xml_checks import validate_file
from mapvalidator.probe import probe_source
from mapvalidator.reporter import print_report
import xml.etree.ElementTree as ET

filepath = Path('$MAP_FILE')

# XML validation
result = validate_file(filepath)

# Liveness probe
try:
    tree = ET.parse(filepath)
    probe = probe_source(tree.getroot(), filepath)
except Exception as e:
    probe = None
    print(f'  Probe error: {e}')

probes = [probe] if probe else None
exit_code = print_report([result], probes)
sys.exit(exit_code)
" || OVERALL_EXIT=1

    echo ""
done

exit $OVERALL_EXIT
