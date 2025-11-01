#!/usr/bin/env python3
import sys
import yaml

if len(sys.argv) < 2 or not sys.argv[1]:
    print("Usage: make ability-enable AB=<name>")
    sys.exit(2)

ab = sys.argv[1]
p = ".tools/abilities_enabled.yml"

try:
    data = yaml.safe_load(open(p))
except FileNotFoundError:
    data = {"enabled": []}

en = set(data.get("enabled", []))
en.add(ab)
data["enabled"] = sorted(en)

with open(p, "w") as f:
    f.write(yaml.safe_dump(data, sort_keys=False))

print(f"[abilities] enabled: {ab}")
