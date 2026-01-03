# 🚀 Google Cloud Run Deployment Guide

## Quick Start (3 Adım)

### 1️⃣ Google Cloud Setup
```bash
# gcloud CLI kur (eğer yoksa)
# macOS:
brew install google-cloud-sdk

# Veya: https://cloud.google.com/sdk/docs/install

# Login
gcloud auth login

# Proje oluştur (veya mevcut projeyi kullan)
gcloud projects create empathic-gateway --name="EmpathicGateway"
gcloud config set project empathic-gateway

# Billing aktif et (Google Cloud Console'dan)
# https://console.cloud.google.com/billing
```

### 2️⃣ Deploy Et
```bash
# Otomatik deployment
./deploy-cloudrun.sh

# VEYA Manuel:
export GCP_PROJECT_ID="your-project-id"
./deploy-cloudrun.sh
```

### 3️⃣ Test Et
```bash
# Backend health check
curl https://empathic-backend-xxx.run.app/health

# Frontend'i tarayıcıda aç
# https://empathic-frontend-xxx.run.app
```

---

## 📋 Detaylı Adımlar

### Ön Gereksinimler
- [ ] Google Cloud hesabı (ücretsiz $300 kredi)
- [ ] gcloud CLI kurulu
- [ ] Billing aktif
- [ ] Docker kurulu (opsiyonel, Cloud Build kullanır)

### Manuel Deployment

**Backend:**
```bash
gcloud run deploy empathic-backend \
  --source . \
  --dockerfile Dockerfile.backend \
  --region europe-west1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300
```

**Frontend:**
```bash
# Backend URL'i al
BACKEND_URL=$(gcloud run services describe empathic-backend \
  --region europe-west1 \
  --format 'value(status.url)')

# Frontend deploy
gcloud run deploy empathic-frontend \
  --source . \
  --dockerfile Dockerfile.frontend \
  --region europe-west1 \
  --allow-unauthenticated \
  --set-env-vars API_URL=$BACKEND_URL \
  --memory 1Gi
```

---

## 🔧 Konfigürasyon

### Environment Variables

**Backend:**
```bash
PYTHONUNBUFFERED=1
```

**Frontend:**
```bash
API_URL=https://empathic-backend-xxx.run.app
```

### Resource Limits

| Servis | Memory | CPU | Timeout | Min Instances |
|--------|--------|-----|---------|---------------|
| Backend | 2 GB | 2 | 300s | 0 |
| Frontend | 1 GB | 1 | 60s | 0 |

---

## 💰 Maliyet Optimizasyonu

### 1. Min Instances = 0 (Cold Start)
- İlk istek 10-15 saniye sürer
- Trafik yokken $0
- **Önerilen**: Demo/Test için

### 2. Min Instances = 1 (Always On)
- Her zaman hazır
- Aylık ~$15-20 ek maliyet
- **Önerilen**: Production için

```bash
# Always-on için:
gcloud run services update empathic-backend \
  --min-instances 1 \
  --region europe-west1
```

---

## 🔍 Monitoring & Logs

### Logs Görüntüleme
```bash
# Backend logs
gcloud run services logs read empathic-backend \
  --region europe-west1 \
  --limit 50

# Frontend logs
gcloud run services logs read empathic-frontend \
  --region europe-west1 \
  --limit 50

# Real-time logs
gcloud run services logs tail empathic-backend \
  --region europe-west1
```

### Metrics
```bash
# Cloud Console'da görüntüle
https://console.cloud.google.com/run
```

---

## 🌐 Custom Domain

### 1. Domain Mapping
```bash
# Domain ekle
gcloud run domain-mappings create \
  --service empathic-frontend \
  --domain app.empathicgateway.com \
  --region europe-west1

# DNS kayıtlarını ekle (Cloud Console'dan)
```

### 2. SSL Certificate
- Otomatik olarak Google tarafından sağlanır
- Let's Encrypt kullanır
- Yenileme otomatik

---

## 🔄 Update & Rollback

### Update
```bash
# Yeni versiyon deploy et
./deploy-cloudrun.sh

# Veya sadece backend:
gcloud run deploy empathic-backend \
  --source . \
  --dockerfile Dockerfile.backend \
  --region europe-west1
```

### Rollback
```bash
# Önceki versiyona dön
gcloud run services update-traffic empathic-backend \
  --to-revisions PREVIOUS=100 \
  --region europe-west1
```

---

## 🐛 Troubleshooting

### Cold Start Çok Uzun
```bash
# Min instances artır
gcloud run services update empathic-backend \
  --min-instances 1 \
  --region europe-west1
```

### Out of Memory
```bash
# Memory artır
gcloud run services update empathic-backend \
  --memory 4Gi \
  --region europe-west1
```

### CORS Errors
Backend'e CORS middleware ekle:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 📊 Cost Breakdown

**Örnek Kullanım (Aylık):**
- 100,000 istek
- Ortalama 2 saniye işlem süresi
- Backend: 2GB RAM, 2 CPU
- Frontend: 1GB RAM, 1 CPU

**Maliyet:**
- Backend: ~$5-8
- Frontend: ~$2-3
- **Toplam: ~$7-11/ay**

**Free Tier:**
- İlk 2 milyon istek ücretsiz
- 360,000 GB-seconds ücretsiz
- 180,000 vCPU-seconds ücretsiz

---

## ✅ Deployment Checklist

- [ ] gcloud CLI kurulu
- [ ] Google Cloud projesi oluşturuldu
- [ ] Billing aktif
- [ ] `deploy-cloudrun.sh` çalıştırıldı
- [ ] Backend health check başarılı
- [ ] Frontend açılıyor
- [ ] Test senaryoları çalışıyor
- [ ] Logs kontrol edildi
- [ ] Custom domain ayarlandı (opsiyonel)
- [ ] Monitoring kuruldu

---

## 🎯 Production Checklist

- [ ] Min instances = 1 (always-on)
- [ ] Custom domain
- [ ] SSL certificate
- [ ] Monitoring & alerting
- [ ] Budget alerts
- [ ] Backup strategy
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Load testing

---

## 📞 Support

**Google Cloud Support:**
- Docs: https://cloud.google.com/run/docs
- Pricing: https://cloud.google.com/run/pricing
- Community: https://stackoverflow.com/questions/tagged/google-cloud-run

**EmpathicGateway:**
- GitHub: [Your Repo]
- Issues: [Your Issues Page]
