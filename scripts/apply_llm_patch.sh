#!/usr/bin/env bash
set -euo pipefail
IN="${1:-/dev/stdin}"

# Estrai solo il blocco diff tra i marker, poi prova p0 → p1 con fuzz.
awk '/---BEGIN DIFF---/{flag=1;next}/---END DIFF---/{flag=0}flag' "$IN" \
 | sed '1d;$d' > /tmp/llm.patch || true

if [[ ! -s /tmp/llm.patch ]]; then
  echo "No diff found between markers."
  exit 2
fi

patch -p0 -l --fuzz=3 < /tmp/llm.patch || patch -p1 -l --fuzz=3 < /tmp/llm.patch
echo "Patch applied."
