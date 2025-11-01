* badge GitHub Actions,
* prima integrazione (CI pipeline) già spuntata,
* miglior formattazione per il portfolio.

---

```markdown
# 🧱 infra-debug — Local DevOps Playground  
[![CI](https://github.com/Pl1n10/infra-debug/actions/workflows/ci.yml/badge.svg)](https://github.com/Pl1n10/infra-debug/actions/workflows/ci.yml)

> 🧰 Un laboratorio **completamente locale** per testare flussi DevOps end-to-end, con automazione IaC e LLM self-hosted.

---

## 🚀 Panoramica

Questo progetto combina **Terraform**, **Ansible**, **Pre-commit** e un **LLM locale (Ollama)** per costruire un ambiente di test e debugging DevOps completamente indipendente dal cloud.

### Include:
- ✅ **Terraform** — provisioning e validazione di risorse AWS (mock locale o reale)
- ✅ **Ansible** — automazione di configurazioni e test in dry-run
- 🤖 **LLM Fixer/Analyst** — correzione automatica del codice Terraform / Ansible
- 🧠 **RAG locale** — contesto semantico indicizzato in SQLite
- 🧹 **Pre-commit hooks** — linting e validazioni automatiche su Git

---

## 📂 Struttura del progetto

```

infra-debug/
├── ansible/
│   ├── playbook.yml        # Playbook demo
│   └── inventory.ini       # Inventario (localhost)
│
├── terraform/
│   ├── main.tf             # S3 bucket demo
│   ├── variables.tf        # Variabili (region, project)
│   └── versions.tf         # Provider + version pinning
│
├── .tools/
│   ├── ask_fixer.py        # Chiama LLM per generare diff
│   ├── ask_analyst.py      # Analizza errori/log
│   └── index.py            # Indicizza sorgenti per RAG
│
├── .github/workflows/ci.yml # Pipeline CI (make ci)
├── .pre-commit-config.yaml  # Hook Terraform / YAML / Ansible
├── Makefile                 # Automazione principale
└── .rag.sqlite              # Database embedding locale

````

---

## 🧠 Flusso di lavoro

### 🔹 1. Terraform

```bash
make tf-init
make tf-validate
make tf-plan
````

💡 Esegue `terraform init`, `validate`, e `plan` con `project=llm-demo`.
Per applicare davvero:

```bash
make tf-apply APPROVE=1
```

---

### 🔹 2. Ansible

```bash
make ans-lint
make ans-check
make ans-run
```

* `ans-lint`: linting YAML / sintassi
* `ans-check`: esecuzione in modalità dry-run (`--check`)
* `ans-run`: provisioning reale

---

### 🔹 3. LLM Fixer Loop (offline con Ollama)

Quando un comando fallisce (es. `terraform plan`), salvi l’output e lo fai analizzare dal modello.

```bash
TRACE_TF="$(make tf-plan 2>&1 || true)"

make fixer Q="LANGUAGE: HCL. TARGET FILE: terraform/main.tf ONLY.
Fix the duplicate tags issue. Return MINIMAL unified diff." \
  TRACE="$TRACE_TF" \
  | tee /tmp/llm_out.txt
```

Applica automaticamente la patch:

```bash
make apply-llm-patch LLM_OUT=/tmp/llm_out.txt
```

---

### 🔹 4. Indicizzazione RAG

Crea o aggiorna il database `.rag.sqlite` con i contenuti del progetto:

```bash
make index-terraform
make index-ansible
```

Per ripulire o ottimizzare:

```bash
make clean-rag
make vacuum-rag
```

---

### 🔹 5. Pre-commit & CI

Installa i pre-commit hook:

```bash
make pre-commit-install
```

Esegui controlli manuali:

```bash
make check
```

Pipeline locale:

```bash
make ci
```

Esegue:

* `terraform fmt`
* `terraform validate`
* `yamllint`
* `ansible-lint`

---

## ⚙️ Setup richiesto

| Strumento        | Funzione          | Installazione                                                            |     |
| ---------------- | ----------------- | ------------------------------------------------------------------------ | --- |
| **Terraform**    | IaC               | `sudo apt install terraform`                                             |     |
| **Ansible**      | Config management | `sudo apt install ansible`                                               |     |
| **Ansible-lint** | Linting playbook  | `sudo apt install ansible-lint`                                          |     |
| **Yamllint**     | Validazione YAML  | `sudo apt install yamllint`                                              |     |
| **Pre-commit**   | Hook Git          | `sudo apt install pre-commit`                                            |     |
| **Ollama**       | LLM locale        | `curl -fsSL [https://ollama.ai/install.sh](https://ollama.ai/install.sh) | sh` |

---

## 🔧 Variabili chiave (Makefile)

| Variabile     | Default                  | Descrizione             |
| ------------- | ------------------------ | ----------------------- |
| `OLLAMA_HOST` | `http://localhost:11434` | Endpoint Ollama         |
| `LOCAL_MODEL` | `qwen2.5-coder:7b`       | Modello LLM per fixer   |
| `EMBED_MODEL` | `nomic-embed-text`       | Modello embedding RAG   |
| `TF_PROJECT`  | `llm-demo`               | Nome progetto Terraform |
| `ANS_INV`     | `ansible/inventory.ini`  | Inventario Ansible      |
| `ANS_PB`      | `ansible/playbook.yml`   | Playbook principale     |

---

## 🧩 Target principali Makefile

| Comando                                  | Descrizione                   |
| ---------------------------------------- | ----------------------------- |
| `make index`                             | Indicizza Ansible + Terraform |
| `make tf-init / validate / plan / apply` | Gestione Terraform            |
| `make ans-lint / check / run`            | Gestione Ansible              |
| `make fixer`                             | Correzione automatica LLM     |
| `make apply-llm-patch`                   | Applica il diff generato      |
| `make check`                             | Esegue pre-commit hook        |
| `make ci`                                | Mini pipeline locale          |

---

## 🧭 Estensioni future

* ✅ **GitHub Actions CI** già integrato
* ⏳ **OpenWebUI Integration** per prompt interattivi LLM
* ⏳ **Profilo AWS terraform-admin** per deploy reale
* ⏳ **Ruoli Ansible modulari**
* ⏳ **Supporto Pulumi / Docker Compose**

---

## 👨‍💻 Autore

**Roberto Novara**
💼 DevOps Engineer & System Administrator
📍 Napoli — Remote
🌐 GitHub: [Pl1n10](https://github.com/Pl1n10)

---

> 💬 *“Local-first DevOps meets AI — perché testare in locale è la prima forma di sicurezza.”*

```


