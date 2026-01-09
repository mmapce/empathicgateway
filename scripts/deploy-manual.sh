#!/bin/bash

# EmpathicGateway - Manual Cloud Run Deployment Script
# This script manually deploys the backend service to Google Cloud Run

set -e

echo "🚀 EmpathicGateway Manual Deployment"
echo "===================================="

# Configuration
PROJECT_ID="rapid-hangar-476217-j6"
REGION="europe-west1"
SERVICE_NAME="empathic-backend"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest"

echo ""
echo "📦 Step 1: Building Docker image locally..."
docker build -t ${IMAGE_NAME} -f Dockerfile.backend .

echo ""
echo "📤 Step 2: Pushing image to Google Container Registry..."
docker push ${IMAGE_NAME}

echo ""
echo "🚀 Step 3: Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_NAME} \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --memory 4Gi \
  --cpu 4 \
  --timeout 600 \
  --max-instances 10 \
  --min-instances 0 \
  --cpu-boost \
  --set-env-vars "PYTHONUNBUFFERED=1" \
  --project ${PROJECT_ID}

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🌐 Service URL:"
gcloud run services describe ${SERVICE_NAME} \
  --platform managed \
  --region ${REGION} \
  --format 'value(status.url)' \
  --project ${PROJECT_ID}
