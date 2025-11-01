import os, argparse, sqlite3, json, numpy as np, requests
def cosine(a,b):
    a=np.array(a); b=np.array(b)
    return float(a.dot(b)/(np.linalg.norm(a)*np.linalg.norm(b)+1e-9))
ap=argparse.ArgumentParser()
ap.add_argument("--query", required=True)
ap.add_argument("--k", type=int, default=int(os.getenv("K","16")))
ap.add_argument("--ollama", default=os.getenv("OLLAMA_HOST","http://localhost:11434"))
ap.add_argument("--embed", default=os.getenv("EMBED_MODEL","nomic-embed-text"))
args=ap.parse_args()
qemb = requests.post(f"{args.ollama}/api/embeddings",
                     json={"model": args.embed, "prompt": args.query}).json()["embedding"]
db=sqlite3.connect(".rag.sqlite")
rows=db.execute("SELECT path, chunk, text, emb FROM docs").fetchall()
scored=[]
for path, ch, txt, emb in rows:
    emb=json.loads(emb)
    scored.append((cosine(qemb, emb), path, ch, txt))
scored.sort(key=lambda x:-x[0])
for s, path, ch, txt in scored[:args.k]:
    print(f"\n--- {path}#{ch}  score={s:.3f}\n{txt}\n")
