# 🛡️ EmpathicGateway

**AI-Powered Priority Routing & PII Detection System**

> **Course:** ARI5501 Natural Language Processing  
> **Track:** Track 1: AI Engineer  
> **Author:** Murat Korkmaz

EmpathicGateway is an intelligent API Gateway designed to solve the "Latency vs. Security" trade-off in modern customer support systems. Instead of a standard FIFO queue, it uses **Edge AI** to analyze request urgency, mask sensitive data, and route traffic dynamically to prevent system overload during spikes.

![System Architecture](docs/architecture_diagram.png)

---

## 🚀 Key Features

### 🧠 1. Hybrid AI Engine
*   **Architecture:** We use a "Transfer Learning" approach, combining:
    *   **Embedder:** `sentence-transformers/all-MiniLM-L6-v2` (BERT) for rich semantic understanding.
    *   **Classifier:** `LogisticRegression` for ultra-low latency inference.
*   **Result:** The system understands context (e.g., *"I lost my wallet"* vs *"I lost the game"*) without the heavy compute cost of LLMs.
*   **Synthetic Injection:** To fix class imbalance, we synthesized 130+ variations of critical scenarios (Fraud/Theft) to ensure **100% Recall** on security threats.

### 🛡️ 2. Zero-Trust Security Guardrails
Privacy is handled *before* any data touches the database or downstream agents.
*   **Hybrid PII Masking:**
    *   **Regex Layer:** Instantly redacts structured data (Credit Cards, Emails, Phones).
    *   **NER Layer (BERT):** Detects context-dependent entities like Names (`[PERSON]`) and Locations (`[LOC]`).
*   **Injection Defense:** Heuristic filters block "Prompt Injection" attacks (e.g., *"Ignore previous instructions"*).

### ⚡ 3. Resilience & Chaos Engineering
*   **Dynamic Lane Management:** Traffic is split into two prioritized lanes:
    *   **FAST LANE (Capacity: 10):** Reserved for Critical/High priority (Fraud, Payment).
    *   **NORMAL LANE (Capacity: 2):** For Chit-Chat and General Queries.
*   **Circuit Breaker:** If the Normal Lane fills up during a generic traffic spike (e.g. DDOS), the system sheds load (`HTTP 429`) while keeping the Fast Lane open for real emergencies.

### 📊 4. Live Ops Dashboard
*   **Real-time Visualization:** See requests moving through lanes in real-time.
*   **Stress Tester:** Built-in tool to simulate 100+ concurrent requests and visualize how the system handles saturation.
*   **Explainable AI:** Click on any request to see *why* the model classified it as Critical (Confidence Scores + Logits).

---

## 🌍 Deployment & Live Demo

The production version of this system is deployed on a private **Synology NAS (DS923+)** home server.

*   **Infrastructure:** Docker containers running on Synology Container Manager.
*   **Remote Access:** Exposed securely via **Cloudflare Tunnel** (Zero Trust).
*   **Live Demo:** A temporary public link can be provided upon request for evaluation.
    *   *Note: To conserve resources, the server is active only during scheduled demo slots. It is turned on/off on demand. Please contact the author to request a live session.*

---

## 📂 Project Structure

```
EmpathicGateway/
├── backend/
│   ├── main.py            # FastAPI Gateway (API, PII Logic, Routing)
│   ├── train_model.py     # Training Pipeline (Synthetic Injection)
│   ├── models.py          # Pydantic Schemas
│   └── urgency_model.joblib # AI Model
├── frontend/
│   └── app.py             # Streamlit Ops Dashboard
├── docs/                  # Documentation & Reports
├── scripts/               # Maintenance Tools
└── docker-compose.yml     # Container Orchestration
```

---

## 🛠️ Installation & Usage

### Option 1: Docker (Recommended)
The system is fully containerized.

```bash
# 1. Clone & Key
git clone https://github.com/mmapce/empathicgateway.git
cd EmpathicGateway

# 2. Launch
docker-compose up --build
```
> **Note:** The first run will download the BERT model (~90MB) from Hugging Face.

**Access Points:**
*   🎨 **Dashboard:** http://localhost:8503
*   ⚙️ **API Docs:** http://localhost:8081/docs

### Option 2: Local Python Development
For debugging or direct code execution.

```bash
# 1. Environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Train Model (Optional - Pre-trained model is auto-downloaded)
python -m backend.train_model

# 3. Start Backend
uvicorn backend.main:app --port 8081 --host 0.0.0.0

# 4. Start Frontend
streamlit run frontend/app.py --server.port 8503
```

---

## 🧪 Simulation Guide (How to Demo)

1.  **Open Dashboard:** Go to http://localhost:8503.
2.  **Start Traffic:** Open the Sidebar and click **"Start Stress Test"**.
3.  **Observe Lanes:**
    *   Notice how "Normal" requests (blocks) pile up and eventually turn **Red** (Rejected/429) when the lane is full.
    *   Notice how "Critical" requests (Fraud) *always* bypass the queue and get processed (Green), demonstrating the Priority Routing.
4.  **Test PII:**
    *   Type a message in the "Live Inspector": *"My name is Murat and my card is 4111-2222-3333-4444"*.
    *   See the backend output: *"My name is [PERSON] and my card is [CREDIT_CARD]"*.

---

## 📊 Technical Specifications

| Component | Technology | Performance |
| :--- | :--- | :--- |
| **Model** | BERT (MiniLM) + LogReg | 99.8% Accuracy |
| **API** | FastAPI (Async) | **~20ms Latency** |
| **Frontend** | Streamlit | Real-time (Active Polling) |
| **Security** | Hybrid (Regex + NER) | 95%+ PII Recall |

---

## 📜 License
MIT License.
