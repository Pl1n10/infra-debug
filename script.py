python3 << 'PYSCRIPT'
makefile_content = '''# Makefile – infra-test (con abilities dinamiche)
SHELL := /bin/bash

# ====== Config ======
# Ollama / LLM locali
OLLAMA_HOST ?= http://100.100.140.30:11434
EMBED_MODEL ?= nomic-embed-text
LOCAL_MODEL ?= qwen2.5-coder:7b

# Indexer
MAX_CHUNKS   ?= 2000
MAX_BYTES    ?= 262144  # 256KB
ALLOWED_EXTS ?= .tf,.tfvars,.yaml,.yml,.ini,.sh,.md,.py,.txt
EXCLUDE_DIRS ?= .git,node_modules,.venv,.idea,dist,build,artifacts,.terraform,.cache,.local,vendor,target,__pycache__

# Terraform
TF_DIR     ?= terraform
TF_PROJECT ?= llm-demo

# Ansible
ANS_INV ?= ansible/inventory.ini
ANS_PB  ?= ansible/playbook.yml

# Generic
LLM_K ?= 16

# ====== Meta ======
.DEFAULT_GOAL := help
.PHONY: help \\
        index index-terraform index-ansible clean-rag vacuum-rag \\
        tf-init tf-validate tf-plan tf-apply \\
        ans-lint ans-check ans-run \\
        analyst fixer apply-llm-patch \\
        pre-commit-install check ci \\
        abilities-gen ability-list ability-enable ability-disable

# ====== Help ======
help:
\t@echo "Targets utili:"
\t@echo "  index-terraform       Indicizza solo ./terraform (RAG locale)"
\t@echo "  index-ansible         Indicizza solo ./ansible"
\t@echo "  clean-rag             Rimuove .rag.sqlite"
\t@echo "  vacuum-rag            VACUUM sul DB RAG per ridurre spazio"
\t@echo "  tf-init               terraform init (no backend)"
\t@echo "  tf-validate           terraform validate"
\t@echo "  tf-plan               terraform plan (project=$(TF_PROJECT))"
\t@echo "  tf-apply              terraform apply (richiede APPROVE=1)"
\t@echo "  ans-lint              ansible-lint sul playbook"
\t@echo "  ans-check             ansible-playbook --check"
\t@echo "  ans-run               ansible-playbook reale"
\t@echo "  analyst               LLM analyst (usa Q/TRACE/DIFF env)"
\t@echo "  fixer                 LLM fixer (usa Q/TRACE/DIFF env)"
\t@echo "  apply-llm-patch       Applica diff da LLM_OUT=/percorso/output.txt"
\t@echo "  pre-commit-install    Installa i pre-commit hook"
\t@echo "  check                 Esegue pre-commit su tutti i file"
\t@echo "  ci                    Lancia lint/validate/check"
\t@echo "  abilities-gen         Genera target dinamici da abilities abilitate"
\t@echo "  ability-list          Elenca abilities abilitate"
\t@echo "  ability-enable AB=x   Abilita ability (es. AB=python) e rigenera target"
\t@echo "  ability-disable AB=x  Disabilita ability e rigenera target"

# ====== Index (RAG) ======
index: index-terraform index-ansible

index-terraform:
\t@python3 .tools/index.py \\
\t  --repo ./terraform \\
\t  --ollama $(OLLAMA_HOST) \\
\t  --embed $(EMBED_MODEL) \\
\t  --max_chunks $(MAX_CHUNKS) \\
\t  --max_bytes $(MAX_BYTES) \\
\t  --allowed_exts "$(ALLOWED_EXTS)" \\
\t  --exclude_dirs "$(EXCLUDE_DIRS)"

index-ansible:
\t@python3 .tools/index.py \\
\t  --repo ./ansible \\
\t  --ollama $(OLLAMA_HOST) \\
\t  --embed $(EMBED_MODEL) \\
\t  --max_chunks $(MAX_CHUNKS) \\
\t  --max_bytes $(MAX_BYTES) \\
\t  --allowed_exts "$(ALLOWED_EXTS)" \\
\t  --exclude_dirs "$(EXCLUDE_DIRS)"

clean-rag:
\t@rm -f .rag.sqlite && echo "OK: .rag.sqlite rimosso"

vacuum-rag:
\t@sqlite3 .rag.sqlite 'PRAGMA optimize; VACUUM;' || true
\t@ls -lh .rag.sqlite || true

# ====== Terraform ======
tf-init:
\tcd $(TF_DIR) && terraform init -backend=false

tf-validate:
\tcd $(TF_DIR) && terraform validate -no-color

tf-plan:
\tcd $(TF_DIR) && terraform plan -no-color -input=false -var="project=$(TF_PROJECT)" || true

# Esegui solo con: make tf-apply APPROVE=1
tf-apply:
\t@if [[ "$(APPROVE)" != "1" ]]; then \\
\t  echo "Guardrail: set APPROVE=1 per procedere (es. make tf-apply APPROVE=1)"; exit 2; \\
\tfi
\tcd $(TF_DIR) && terraform apply -auto-approve -input=false -var="project=$(TF_PROJECT)"

# ====== Ansible ======
ans-lint:
\tansible-lint $(ANS_PB) -v || true

ans-check:
\tansible-playbook -i $(ANS_INV) $(ANS_PB) --check -vvv || true

ans-run:
\tansible-playbook -i $(ANS_INV) $(ANS_PB) -vv

# ====== LLM loop ======
# Usa variabili d'ambiente:
#   Q="prompt per l'analyst/fixer"
#   TRACE="$(comandi che producono log 2>&1 || true)"
#   DIFF="" (opzionale, patch corrente)
analyst:
\t@python3 .tools/ask_analyst.py \\
\t  --ollama $(OLLAMA_HOST) \\
\t  --local-model $(LOCAL_MODEL) \\
\t  --k $(LLM_K) \\
\t  --query "$${Q}" \\
\t  --trace "$${TRACE}" \\
\t  --diff "$${DIFF}"

fixer:
\t@python3 .tools/ask_fixer.py \\
\t  --ollama $(OLLAMA_HOST) \\
\t  --model $(LOCAL_MODEL) \\
\t  --k $(LLM_K) \\
\t  --query "$${Q}" \\
\t  --trace "$${TRACE}" \\
\t  --diff "$${DIFF}"

# Applica una patch restituita dall'LLM (in /tmp/out.txt o simile)
# Uso: make apply-llm-patch LLM_OUT=/tmp/out.txt
apply-llm-patch:
\t@if [[ -z "$${LLM_OUT}" ]]; then echo "Errore: passa LLM_OUT=/percorso/output.txt"; exit 2; fi
\t@awk '/---BEGIN DIFF---/{f=1;next}/---END DIFF---/{f=0}f' "$${LLM_OUT}" | sed '1d;$$d' > /tmp/llm.patch || true
\t@if [[ ! -s /tmp/llm.patch ]]; then echo "Nessun diff trovato tra i marker nel file $$LLM_OUT"; exit 3; fi
\t@patch -p0 -l --fuzz=3 < /tmp/llm.patch || patch -p1 -l --fuzz=3 < /tmp/llm.patch
\t@echo "Patch applicata."

# ====== Pre-commit / CI ======
pre-commit-install:
\tpre-commit install

check:
\tpre-commit run --all-files

ci: tf-validate tf-plan ans-lint ans-check check
\t@echo "CI locale OK"

# ====== Abilities (auto-estendibili) ======
# Genera targets dinamici in .tools/abilities.mk
abilities-gen:
\t@python3 .tools/abilities_gen.py

# includi i target generati (non fallire se mancante)
-include .tools/abilities.mk

ability-list:
\t@echo "Enabled abilities:"
\t@python3 - <<'PY'
import yaml, sys
p=".tools/abilities_enabled.yml"
try:
    data=yaml.safe_load(open(p))
    for n in data.get("enabled", []):
        print("-", n)
except FileNotFoundError:
    print("(nessuna: file non trovato)")
PY

# abilita: make ability-enable AB=python
ability-enable:
\t@[[ -n "$$AB" ]] || { echo "Usage: make ability-enable AB=<name>"; exit 2; }
\t@python3 - <<'PY'
import sys,yaml
ab = sys.argv[1]
p=".tools/abilities_enabled.yml"
try:
    data=yaml.safe_load(open(p))
except FileNotFoundError:
    data={"enabled":[]}
en=set(data.get("enabled",[]))
en.add(ab)
data["enabled"]=sorted(en)
open(p,"w").write(yaml.safe_dump(data, sort_keys=False))
print(f"[abilities] enabled:", ab)
PY "$$AB"
\t@$(MAKE) abilities-gen

# disabilita: make ability-disable AB=python
ability-disable:
\t@[[ -n "$$AB" ]] || { echo "Usage: make ability-disable AB=<name>"; exit 2; }
\t@python3 - <<'PY'
import sys,yaml
ab = sys.argv[1]
p=".tools/abilities_enabled.yml"
try:
    data=yaml.safe_load(open(p))
except FileNotFoundError:
    data={"enabled":[]}
data["enabled"]=[x for x in data.get("enabled",[]) if x!=ab]
open(p,"w").write(yaml.safe_dump(data, sort_keys=False))
print(f"[abilities] disabled:", ab)
PY "$$AB"
\t@$(MAKE) abilities-gen
'''

with open('Makefile', 'w') as f:
    f.write(makefile_content)

print("Makefile creato con successo!")
PYSCRIPT
