# .tools/index.py (safe / infra-focused)
import os, argparse, sqlite3, json, hashlib, requests
from pathlib import Path
from time import time

def parse_csv(val, cast=str):
    if not val: return []
    return [cast(x.strip()) for x in val.split(",") if x.strip()]

ap = argparse.ArgumentParser()
ap.add_argument("--repo", required=True, help="root da indicizzare (es. ./terraform oppure ./ansible)")
ap.add_argument("--ollama", default=os.getenv("OLLAMA_HOST","http://localhost:11434"))
ap.add_argument("--embed",  default=os.getenv("EMBED_MODEL","nomic-embed-text"))
ap.add_argument("--max_chunks", type=int, default=300, help="limite massimo di CHUNK da embeddare (non file)")
ap.add_argument("--max_bytes",  type=int, default=256*1024, help="salta file più grandi di questa soglia")
ap.add_argument("--exclude_dirs", default=".git,node_modules,.venv,.idea,dist,build,artifacts,.terraform,.cache,.local,vendor,target,__pycache__",
                help="CSV di directory da escludere (match su qualsiasi segmento del path)")
ap.add_argument("--allowed_exts", default=".tf,.tfvars,.yaml,.yml,.ini,.sh,.md,.py,.txt",
                help="CSV di estensioni consentite (vuota per nessun filtro). File senza estensione consentiti se nome=='Makefile'")
ap.add_argument("--chunk_len", type=int, default=1000, help="dimensione massima di un chunk in caratteri")
args = ap.parse_args()

EXCLUDE_DIRS = set(parse_csv(args.exclude_dirs))
ALLOWED_EXTS = set(parse_csv(args.allowed_exts))

def should_exclude_dir(path: Path) -> bool:
    parts = set(path.parts)
    return any(ex in parts for ex in EXCLUDE_DIRS)

def allowed_file(p: Path) -> bool:
    if p.name == "Makefile":
        return True
    if not ALLOWED_EXTS:
        return True
    return p.suffix.lower() in ALLOWED_EXTS

def chunks(txt: str, maxlen=1000):
    buf, out = [], []
    for ln in txt.splitlines():
        # +1 per il newline
        if sum(len(x)+1 for x in buf) + len(ln) + 1 > maxlen:
            if buf: out.append("\n".join(buf))
            buf = [ln]
        else:
            buf.append(ln)
    if buf:
        out.append("\n".join(buf))
    return out

db = sqlite3.connect(".rag.sqlite")
db.execute("""CREATE TABLE IF NOT EXISTS docs (
  id TEXT PRIMARY KEY, path TEXT, chunk INT, text TEXT, emb TEXT
)""")
db.commit()

files = []
repo_root = Path(args.repo).resolve()
for p in repo_root.rglob("*"):
    try:
        if not p.is_file():
            continue
        if should_exclude_dir(p):
            continue
        # skip binari comuni e grossi
        if p.suffix.lower() in [".png",".jpg",".jpeg",".pdf",".zip",".lock",".bin",".gif"]:
            continue
        # filtro per estensioni
        if not allowed_file(p):
            continue
        # limite dimensione
        try:
            if p.stat().st_size > args.max_bytes:
                continue
        except Exception:
            continue
        # tenta lettura testo
        try:
            txt = p.read_text(errors="ignore")
        except Exception:
            continue

        for i, ck in enumerate(chunks(txt, maxlen=args.chunk_len)):
            rid = hashlib.sha1(f"{p}:{i}".encode()).hexdigest()
            files.append((rid, str(p.relative_to(Path.cwd())), i, ck))
            if len(files) >= args.max_chunks:
                break
        if len(files) >= args.max_chunks:
            break
    except Exception:
        # non bloccare l’indice per un file problematico
        continue

print(f"[index] chunks to embed: {len(files)} (max_chunks={args.max_chunks})", flush=True)

done = 0
for rid, path, ch, txt in files:
    t0 = time()
    r = requests.post(
        f"{args.ollama}/api/embeddings",
        json={"model": args.embed, "prompt": txt},
        timeout=120
    )
    r.raise_for_status()
    emb = r.json()["embedding"]
    with db:
        db.execute("INSERT OR REPLACE INTO docs VALUES (?,?,?,?,?)",
                   (rid, path, ch, txt, json.dumps(emb)))
    done += 1
    if done % 10 == 0 or done == len(files):
        sz = os.path.getsize(".rag.sqlite")/1024
        print(f"[index] {done}/{len(files)} stored; db={sz:.0f}KB; last={time()-t0:.1f}s", flush=True)

print(f"[index] DONE. Total chunks: {len(files)}; db size: {os.path.getsize('.rag.sqlite')/1024:.0f}KB")
