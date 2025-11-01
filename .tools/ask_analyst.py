import os, argparse, subprocess, requests
ap=argparse.ArgumentParser()
ap.add_argument("--ollama", default=os.getenv("OLLAMA_HOST","http://localhost:11434"))
ap.add_argument("--local-model", default=os.getenv("LOCAL_MODEL","qwen2.5-coder:7b"))
ap.add_argument("--k", type=int, default=int(os.getenv("K","16")))
ap.add_argument("--query", default="")
ap.add_argument("--trace", default="")
ap.add_argument("--diff", default="")
args=ap.parse_args()
snips = subprocess.run(
 ["python3",".tools/retrieve.py","--query",args.query,"--k",str(args.k),"--ollama",args.ollama],
 capture_output=True, text=True).stdout
prompt = f"""You are a senior engineer (Analyst).
Given:
- ERROR/stack:\\n{args.trace}\\n
- DIFF or failing command:\\n{args.diff}\\n
- Retrieved snippets:\\n{snips}\\n
1) Top 3 likely root causes with file:line hints.
2) Minimal extra logs/metrics to add (if useful).
3) Concrete next steps (numbered).
Keep it concise.
"""
r = requests.post(f"{args.ollama}/api/chat",
                  json={"model": args.local_model,"messages":[{"role":"user","content":prompt}],
                        "stream": False})
r.raise_for_status()
print(r.json()["message"]["content"])
