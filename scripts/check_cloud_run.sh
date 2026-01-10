#!/bin/bash

# Quick Cloud Run Status Check Script

PROJECT_ID="rapid-hangar-476217-j6"
REGION="europe-west1"
SERVICE_NAME="empathic-backend"

echo "🔍 Checking Cloud Run Service Status..."
echo "=========================================="

# 1. Service Status
echo ""
echo "📊 Service Info:"
gcloud run services describe $SERVICE_NAME \
  --region $REGION \
  --project $PROJECT_ID \
  --format="table(status.url,status.conditions)"

# 2. Latest Revision
echo ""
echo "🚀 Latest Revision:"
gcloud run revisions list \
  --service $SERVICE_NAME \
  --region $REGION \
  --project $PROJECT_ID \
  --limit 1 \
  --format="table(metadata.name,status.conditions[0].status,status.conditions[0].message)"

# 3. Recent Logs (Last 50 lines)
echo ""
echo "📜 Recent Logs (Last 50 lines):"
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME" \
  --project $PROJECT_ID \
  --limit 50 \
  --format="table(timestamp,severity,textPayload)"

# 4. Service URL
echo ""
echo "🌐 Service URL:"
gcloud run services describe $SERVICE_NAME \
  --region $REGION \
  --project $PROJECT_ID \
  --format="value(status.url)"
