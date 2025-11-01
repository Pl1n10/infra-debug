#!/usr/bin/env python3
import sys
import yaml

if len(sys.argv) < 2 or not sys.argv[1]:
    print("Usage: make ability-disable AB=<name>")
    sys.exit(2)

ab = sys.argv[1]
p = ".tools/abilities_enabled.yml"

try:
    data = yaml.safe_load(open(p))
except FileNotFoundError:
    data = {"enabled": []}

data["enabled"] = [x for x in data.get("enabled", []) if x != ab]

with open(p, "w") as f:
    f.write(yaml.safe_dump(data, sort_keys=False))

print(f"[abilities] disabled: {ab}")
