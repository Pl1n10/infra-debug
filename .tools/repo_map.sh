#!/usr/bin/env bash
set -euo pipefail
mkdir -p artifacts
{ echo "# REPO MAP ($(date))"; echo '```'; find . -maxdepth 4 -type f; echo '```'; } > artifacts/repo_map.md
