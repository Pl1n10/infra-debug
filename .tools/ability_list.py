#!/usr/bin/env python3
import yaml
import sys

p = ".tools/abilities_enabled.yml"
try:
    data = yaml.safe_load(open(p))
    print("Enabled abilities:")
    for n in data.get("enabled", []):
        print("-", n)
except FileNotFoundError:
    print("(nessuna: file non trovato)")
