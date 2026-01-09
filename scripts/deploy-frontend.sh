#!/bin/bash

# Deploy Frontend to Google Cloud Run
# This script deploys the Streamlit frontend with the correct backend API URL

set -e

PROJECT_ID="rapid-hangar-476217-j6"
REGION="europe-west1"
BACKEND_URL="https://empathic-backend-1078757655479.europe-west1.run.app"

echo "🚀 Deploying Frontend to Cloud Run..."
echo "======================================="

# Build and deploy using Cloud Build
gcloud builds submit \
  --config=cloudbuild-frontend.yaml \
  --project=${PROJECT_ID} \
  --region=${REGION}

echo ""
echo "✅ Frontend deployment initiated!"
echo ""
echo "📊 Monitor deployment:"
echo "https://console.cloud.google.com/cloud-build/builds?project=${PROJECT_ID}"
echo ""
echo "🌐 Once deployed, frontend will be available at:"
echo "https://empathic-frontend-[hash].${REGION}.run.app"
