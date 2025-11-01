#!/usr/bin/env python3
import os, argparse, subprocess, requests

ap=argparse.ArgumentParser()
ap.add_argument("--ollama", default=os.getenv("OLLAMA_HOST","http://localhost:11434"))
ap.add_argument("--model", default=os.getenv("LOCAL_MODEL","qwen2.5-coder:7b"))
ap.add_argument("--k", type=int, default=int(os.getenv("K","16")))
ap.add_argument("--query", default="")
ap.add_argument("--trace", default="")
ap.add_argument("--diff", default="")
args=ap.parse_args()

snips = subprocess.run(
    ["python3",".tools/retrieve.py","--query",args.query,"--k",str(args.k),"--ollama",args.ollama],
    capture_output=True, text=True
).stdout

prompt = f"""You are a senior engineer (Fixer).
Produce a MINIMAL unified diff and (if needed) a tiny test update that reproduces and verifies the fix.
Keep the patch as small as possible and explain side effects briefly.

ERROR/stack:
{args.trace}

CURRENT DIFF (may be empty):
{args.diff}

RETRIEVED SNIPPETS:
{snips}

Return format:
---BEGIN DIFF---
<unified diff here>
---END DIFF---
---NOTES---
<short notes here>"""

r = requests.post(f"{args.ollama}/api/chat",
                  json={"model": args.model, "messages":[{"role":"user","content":prompt}], "stream": False})
r.raise_for_status()
print(r.json()["message"]["content"])
