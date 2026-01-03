# 🚀 EmpathicGateway Deployment Guide

## Overview
This guide covers deploying EmpathicGateway to production using Docker and cloud platforms.

---

## 📦 Option 1: Docker Deployment (Recommended)

### Prerequisites
- Docker & Docker Compose installed
- 4GB+ RAM (for BERT models)

### Step 1: Create Dockerfiles

**Backend Dockerfile** (`Dockerfile.backend`):
```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/
COPY backend/urgency_model.joblib ./backend/

# Expose port
EXPOSE 8081

# Run with production server
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8081"]
```

**Frontend Dockerfile** (`Dockerfile.frontend`):
```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install dependencies
RUN pip install streamlit requests pandas numpy

# Copy frontend code
COPY frontend/ ./frontend/

# Expose port
EXPOSE 8503

# Run Streamlit
CMD ["streamlit", "run", "frontend/app.py", "--server.port=8503", "--server.address=0.0.0.0"]
```

### Step 2: Create docker-compose.yml

```yaml
version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    ports:
      - "8081:8081"
    environment:
      - PYTHONUNBUFFERED=1
    volumes:
      - ./backend:/app/backend
    restart: unless-stopped

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "8503:8503"
    environment:
      - API_URL=http://backend:8081
    depends_on:
      - backend
    restart: unless-stopped
```

### Step 3: Deploy
```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

---

## ☁️ Option 2: Cloud Platforms

### A. Render.com (Free Tier Available)

**Backend (Web Service):**
1. Connect GitHub repo
2. Build Command: `pip install -r requirements.txt`
3. Start Command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
4. Environment: Python 3.10
5. Instance Type: Free (512MB RAM) or Starter ($7/mo, 512MB)

**Frontend (Web Service):**
1. Build Command: `pip install streamlit requests pandas numpy`
2. Start Command: `streamlit run frontend/app.py --server.port=$PORT --server.address=0.0.0.0`
3. Environment Variable: `API_URL=https://your-backend.onrender.com`

### B. Railway.app

**Backend:**
```bash
railway init
railway up
```

**Frontend:**
- Add `API_URL` environment variable pointing to backend
- Deploy with `railway up`

### C. Fly.io (Global Edge Deployment)

**Backend:**
```bash
fly launch --name empathic-backend
fly deploy
```

**Frontend:**
```bash
fly launch --name empathic-frontend
fly secrets set API_URL=https://empathic-backend.fly.dev
fly deploy
```

---

## ⚙️ Production Considerations

### 1. Model Optimization
```python
# backend/main.py - Add model caching
import os
from functools import lru_cache

@lru_cache(maxsize=1)
def load_ner_pipeline():
    return pipeline("ner", model="dslim/bert-base-NER", aggregation_strategy="simple")
```

### 2. Environment Variables
Create `.env` file:
```bash
# Backend
FAST_LANE_LIMIT=10
NORMAL_LANE_LIMIT=2
API_KEY=your-secure-key-here

# Frontend
API_URL=http://localhost:8081
```

### 3. Security
- Change `X-API-KEY` in production
- Enable HTTPS (handled by cloud platforms)
- Add rate limiting (use `slowapi` package)

### 4. Monitoring
```python
# Add to backend/main.py
from prometheus_fastapi_instrumentator import Instrumentator

Instrumentator().instrument(app).expose(app)
```

### 5. Scaling
- **Horizontal**: Use load balancer + multiple backend instances
- **Vertical**: Increase RAM for model loading (2GB+ recommended)

---

## 📊 Resource Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 1 core | 2+ cores |
| RAM | 2GB | 4GB+ |
| Storage | 1GB | 2GB |
| Network | 100Mbps | 1Gbps |

---

## 🔍 Health Checks

Add to `backend/main.py`:
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "ner_loaded": ner_pipeline is not None
    }
```

---

## 🐛 Troubleshooting

**Issue: Out of Memory**
- Solution: Reduce model size or increase instance RAM

**Issue: Slow NER**
- Solution: Use GPU instances or cache results

**Issue: CORS Errors**
- Solution: Add CORS middleware to backend

---

## 📝 Quick Deploy Checklist

- [ ] Create `requirements.txt`
- [ ] Test locally with Docker
- [ ] Choose cloud platform
- [ ] Set environment variables
- [ ] Deploy backend
- [ ] Deploy frontend
- [ ] Test end-to-end
- [ ] Set up monitoring
- [ ] Configure auto-scaling (optional)

---

## 🎯 Recommended Stack

**For Demo/MVP:**
- Render.com Free Tier (Backend + Frontend)
- Total Cost: $0

**For Production:**
- Railway.app or Fly.io
- Backend: $7-20/mo
- Frontend: $5-10/mo
- Total: ~$15-30/mo
