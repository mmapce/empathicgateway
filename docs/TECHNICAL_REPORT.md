# EmpathicGateway: Technical Report
**Date:** January 2026  
**Author:** Murat Korkmaz  
**Version:** 1.0 (Final Release)

---

## 1. Executive Summary
**EmpathicGateway** is an intelligent, resilient API Gateway designed to solve the "Triage Bottleneck" in high-volume customer support systems. Unlike traditional "First-In, First-Out" queues, it uses **Edge AI** to instantly classify urgency, mask sensitive data (PII), and shed excess load during traffic spikes. The system achieves **99.8% classification accuracy** with **<50ms latency** on standard CPU hardware, enabling deployment on both Google Cloud Run and local Synology NAS devices.

## 2. System Architecture
The solution follows a containerized microservices pattern, orchestrated via Docker.

| Component | Technology | Responsibility |
| :--- | :--- | :--- |
| **Backend** | Python, FastAPI, PyTorch | AI Inference, PII Masking, Traffic Routing (Async Semaphores). |
| **Frontend** | Streamlit, Plotly | Ops Dashboard, Real-time Traffic Simulation, Load Visualization. |
| **Gateway** | Cloudflare Tunnel | Zero-trust secure external access (NAS Deployment). |
| **Model** | BERT + LogReg | Hybrid NLP for high-speed intent classification. |

**Data Flow:**
`User Request` → `PII Redaction` → `BERT Embedding` → `Intent Classification` → `Priority Queue` → `Downstream Agent`

## 3. AI Methodology & Data Strategy
### 3.1 Hybrid Model Architecture
We prioritized **inference speed** without sacrificing semantic understanding.
*   **Embedder:** `sentence-transformers/all-MiniLM-L6-v2` converts text to 384-dimensional vectors.
*   **Classifier:** `LogisticRegression` maps vectors to intents with varying priorities.
*   **Performance:** This hybrid approach runs significantly faster than generative LLMs, making it viable for edge deployment.

### 3.2 Synthetic Data Injection (The "Just Browsing" Fix)
The initial dataset (Bitext) lacked nuance for low-priority chatter. We implemented a **Synthetic Injection Strategy**:
*   **Critical Injection:** Added 100+ variations of "Lost Wallet", "Fraud", "Stolen Card" to ensure **Recall = 1.00** for security risks.
*   **Normal Injection:** Added conversational samples ("Just browsing", "Thanks", "Hello") labeled as `chit_chat`.
*   **Result:** The model natively distinguishes between *"I lost my card"* (Critical) and *"I lost the game"* (Normal), removing the need for fragile `if/else` keyword filters.

## 4. Privacy & Zero-Trust Security
Privacy is handled *before* any data enters the processing pipeline or database.
1.  **Metric-Based Regex:** Instantly redacts structured PII (Credit Cards, Emails) with 100% certainty.
2.  **Contextual NER (BERT):** Detects unstructured entities like Names (`[PERSON]`), Locations (`[LOC]`), and Organizations (`[ORG]`).
*   **Output:** `My name is Murat` → `My name is [PERSON]`.

## 5. Resilience: Chaos Engineering
The system is built to survive saturation.
*   **Backpressure:** We utilize `asyncio.Semaphore` to cap concurrent requests.
*   **Lane Prioritization:**
    *   **FAST LANE:** Reserved for `fraud_report` and `payment_issue`. High capacity (10 concurrent).
    *   **NORMAL LANE:** For `chit_chat` and `queries`. Low capacity (2-5 concurrent).
*   **Circuit Breaking:** If the Normal Lane is full, the gateway immediately returns `429 Too Many Requests`, protecting the server resources for Critical tasks. The Frontend Demo visualizes this via "Red Blocks" (Rejected) vs "Green Blocks" (Accepted).

## 6. Deployment Strategy
The system supports a hybrid lifecycle:
*   **Cloud:** Google Cloud Run (Serverless, Auto-scaling).
*   **Edge (NAS):** Synology NAS with **Cloudflare Tunnel**. This allows secure public access (`trycloudflare.com`) without exposing local ports or modifying router firewalls. The model was optimized to run on **CPU-only** (fixing MPS/CUDA dependencies) for hardware compatibility.

## 7. Performance Metrics
*   **Accuracy:** **99.84%** (Validation Set)
*   **Critical Intent Recall:** **1.00** (No critical tickets missed)
*   **Browsing/Chit-Chat Precision:** **1.00** (Zero False Positives)
*   **Avg Inference Latency:** **45ms** (Synology NAS CPU)

---
*EmpathicGateway Technical Report - Confidential*
