# Makefile – infra-test (con abilities dinamiche)
SHELL := /bin/bash

# ====== Config ======
OLLAMA_HOST ?= http://100.100.140.30:11434
EMBED_MODEL ?= nomic-embed-text
LOCAL_MODEL ?= qwen2.5-coder:7b

MAX_CHUNKS   ?= 2000
MAX_BYTES    ?= 262144
ALLOWED_EXTS ?= .tf,.tfvars,.yaml,.yml,.ini,.sh,.md,.py,.txt
EXCLUDE_DIRS ?= .git,node_modules,.venv,.idea,dist,build,artifacts,.terraform,.cache,.local,vendor,target,__pycache__

TF_DIR     ?= terraform
TF_PROJECT ?= llm-demo
ANS_INV ?= ansible/inventory.ini
ANS_PB  ?= ansible/playbook.yml
LLM_K ?= 16

.DEFAULT_GOAL := help
.PHONY: help index index-terraform index-ansible clean-rag vacuum-rag tf-init tf-validate tf-plan tf-apply ans-lint ans-check ans-run analyst fixer apply-llm-patch pre-commit-install check ci abilities-gen ability-list ability-enable ability-disable

# ====== Help ======
help:
	@echo "Targets utili:"
	@echo "  index-terraform       Indicizza solo ./terraform (RAG locale)"
	@echo "  index-ansible         Indicizza solo ./ansible"
	@echo "  clean-rag             Rimuove .rag.sqlite"
	@echo "  vacuum-rag            VACUUM sul DB RAG per ridurre spazio"
	@echo "  tf-init               terraform init (no backend)"
	@echo "  tf-validate           terraform validate"
	@echo "  tf-plan               terraform plan (project=$(TF_PROJECT))"
	@echo "  tf-apply              terraform apply (richiede APPROVE=1)"
	@echo "  ans-lint              ansible-lint sul playbook"
	@echo "  ans-check             ansible-playbook --check"
	@echo "  ans-run               ansible-playbook reale"
	@echo "  analyst               LLM analyst (usa Q/TRACE/DIFF env)"
	@echo "  fixer                 LLM fixer (usa Q/TRACE/DIFF env)"
	@echo "  apply-llm-patch       Applica diff da LLM_OUT=/percorso/output.txt"
	@echo "  pre-commit-install    Installa i pre-commit hook"
	@echo "  check                 Esegue pre-commit su tutti i file"
	@echo "  ci                    Lancia lint/validate/check"
	@echo "  abilities-gen         Genera target dinamici da abilities abilitate"
	@echo "  ability-list          Elenca abilities abilitate"
	@echo "  ability-enable AB=x   Abilita ability (es. AB=python) e rigenera target"
	@echo "  ability-disable AB=x  Disabilita ability e rigenera target"

# ====== Index (RAG) ======
index: index-terraform index-ansible

index-terraform:
	@python3 .tools/index.py --repo ./terraform --ollama $(OLLAMA_HOST) --embed $(EMBED_MODEL) --max_chunks $(MAX_CHUNKS) --max_bytes $(MAX_BYTES) --allowed_exts "$(ALLOWED_EXTS)" --exclude_dirs "$(EXCLUDE_DIRS)"

index-ansible:
	@python3 .tools/index.py --repo ./ansible --ollama $(OLLAMA_HOST) --embed $(EMBED_MODEL) --max_chunks $(MAX_CHUNKS) --max_bytes $(MAX_BYTES) --allowed_exts "$(ALLOWED_EXTS)" --exclude_dirs "$(EXCLUDE_DIRS)"

clean-rag:
	@rm -f .rag.sqlite && echo "OK: .rag.sqlite rimosso"

vacuum-rag:
	@sqlite3 .rag.sqlite 'PRAGMA optimize; VACUUM;' || true
	@ls -lh .rag.sqlite || true

# ====== Terraform ======
tf-init:
	cd $(TF_DIR) && terraform init -backend=false

tf-validate:
	cd $(TF_DIR) && terraform validate -no-color

tf-plan:
	cd $(TF_DIR) && terraform plan -no-color -input=false -var="project=$(TF_PROJECT)" || true

tf-apply:
	@if [[ "$(APPROVE)" != "1" ]]; then echo "Guardrail: set APPROVE=1 per procedere (es. make tf-apply APPROVE=1)"; exit 2; fi
	cd $(TF_DIR) && terraform apply -auto-approve -input=false -var="project=$(TF_PROJECT)"

# ====== Ansible ======
ans-lint:
	ansible-lint $(ANS_PB) -v || true

ans-check:
	ansible-playbook -i $(ANS_INV) $(ANS_PB) --check -vvv || true

ans-run:
	ansible-playbook -i $(ANS_INV) $(ANS_PB) -vv

# ====== LLM loop ======
analyst:
	@python3 .tools/ask_analyst.py --ollama $(OLLAMA_HOST) --local-model $(LOCAL_MODEL) --k $(LLM_K) --query "$${Q}" --trace "$${TRACE}" --diff "$${DIFF}"

fixer:
	@python3 .tools/ask_fixer.py --ollama $(OLLAMA_HOST) --model $(LOCAL_MODEL) --k $(LLM_K) --query "$${Q}" --trace "$${TRACE}" --diff "$${DIFF}"

apply-llm-patch:
	@if [[ -z "$${LLM_OUT}" ]]; then echo "Errore: passa LLM_OUT=/percorso/output.txt"; exit 2; fi
	@awk '/---BEGIN DIFF---/{f=1;next}/---END DIFF---/{f=0}f' "$${LLM_OUT}" | sed '1d;$$d' > /tmp/llm.patch || true
	@if [[ ! -s /tmp/llm.patch ]]; then echo "Nessun diff trovato tra i marker nel file $$LLM_OUT"; exit 3; fi
	@patch -p0 -l --fuzz=3 < /tmp/llm.patch || patch -p1 -l --fuzz=3 < /tmp/llm.patch
	@echo "Patch applicata."

# ====== Pre-commit / CI ======
pre-commit-install:
	pre-commit install

check:
	pre-commit run --all-files

ci: tf-validate tf-plan ans-lint ans-check check
	@echo "CI locale OK"

# ====== Abilities ======
abilities-gen:
	@python3 .tools/abilities_gen.py

-include .tools/abilities.mk

ability-list:
	@python3 .tools/ability_list.py

ability-enable:
	@python3 .tools/ability_enable.py "$(AB)"
	@$(MAKE) abilities-gen

ability-disable:
	@python3 .tools/ability_disable.py "$(AB)"
	@$(MAKE) abilities-gen
