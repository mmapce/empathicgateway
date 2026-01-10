# 🛡️ EmpathicGateway

**AI-Powered Priority Routing & PII Detection System**

EmpathicGateway is an intelligent traffic management system designed for high-load customer support environments. It classifies incoming requests using **BERT** (Critical/High/Normal), detects sensitive data (PII) using **NER**, and routes traffic accordingly to prevent system overload.

![Architecture Diagram](docs/architecture_diagram.png)

---

## 🌟 Key Features

### � Intelligent Core
- **Hybrid AI Engine**: Combines `SentenceTransformers` (BERT) for feature extraction with `LogisticRegression` for ultra-fast intent classification.
- **Priority Routing**: Automatically routes excessive load to "Slow Lanes" while keeping "Fast Lanes" open for critical issues (e.g., "Fraud Detected").
- **Long Text Support**: Handles complex queries up to **2048 characters**.

### 🛡️ Security & Guardrails
- **PII Masking**: Automatically detects and redacts Credit Cards, Emails, and Names using regex + `dslim/bert-base-NER`.
- **Injection Defense**: Heuristic checks to prevent Prompt Injection attacks.
- **API Security**: Token-based authentication (`X-API-Key`).

### 📊 Real-Time Operations
- **Live Dashboard**: Streamlit interface with sub-second update capabilities ("Dynamic Sleep").
- **Stress Testing**: Built-in "Chaos Mode" to simulate traffic spikes.
- **Explainable AI**: Provides confidence scores and reasoning for routing decisions.

---

## 📂 Project Structure

A clean, minimalist repository focused on production readiness:

```
EmpathicGateway/
├── backend/               # FastAPI Application
│   ├── main.py            # API Gateway & Logic
│   ├── models.py          # Data Structures
│   ├── train_model.py     # ML Training Script
│   └── urgency_model.joblib # Trained AI Model
├── frontend/              # Streamlit Dashboard
│   └── app.py             # UI Logic
├── scripts/               # NAS Deployment Tools
│   ├── update_backend.py
│   └── update_frontend.py
├── docs/                  # Documentation
│   └── TECHNICAL_REPORT.md
├── docker-compose.synology.yml # Production Config
└── Dockerfile.*           # Container Definitions
```

---

## � Quick Start

### Option 1: Local Development (Docker)

The easiest way to run the full stack locally.

```bash
docker-compose up --build
```

- **Frontend:** http://localhost:8503
- **Backend API:** http://localhost:8081/docs

### Option 2: Local Development (Python)

If you prefer running without Docker:

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start Backend
uvicorn backend.main:app --port 8081 --host 0.0.0.0

# 3. Start Frontend (New Terminal)
streamlit run frontend/app.py --server.port 8503
```

### Option 3: Synology NAS Deployment

This project is optimized for Edge deployment on Synology Container Manager.

1.  **Preparation:** Ensure SSH access to your NAS.
2.  **Deploy:** Use the `docker-compose.synology.yml` file in Container Manager.
3.  **Updates:** Use the provided scripts to push code changes instantly:
    ```bash
    # Set your NAS Password (or edit script)
    export NAS_PASS="your_password"
    
    # Deploy updates
    python3 scripts/update_backend.py
    ```

---

## � Tech Stack

- **AI/ML:** PyTorch, SentenceTransformers (MiniLM-L6), Scikit-Learn (LogReg), HuggingFace Transformers.
- **Backend:** FastAPI, Uvicorn.
- **Frontend:** Streamlit, Altair Charts.
- **Infrastructure:** Docker, Synology NAS, Cloudflare Tunnel.

---

## 📜 License

MIT License.
