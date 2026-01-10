#!/bin/bash

# EmpathicGateway - Google Cloud Run Deployment Script
# Usage: ./deploy-cloudrun.sh

set -e

echo "🚀 EmpathicGateway Cloud Run Deployment"
echo "========================================"

# Configuration
PROJECT_ID=${GCP_PROJECT_ID:-"your-project-id"}
REGION="europe-west1"
BACKEND_SERVICE="empathic-backend"
FRONTEND_SERVICE="empathic-frontend"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI not found. Please install: https://cloud.google.com/sdk/docs/install${NC}"
    exit 1
fi

# Check if logged in
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
    echo -e "${BLUE}🔐 Please login to Google Cloud...${NC}"
    gcloud auth login
fi

# Set project
echo -e "${BLUE}📋 Setting project: $PROJECT_ID${NC}"
gcloud config set project $PROJECT_ID

# Enable required APIs
echo -e "${BLUE}🔧 Enabling required APIs...${NC}"
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable cloudbuild.googleapis.com

# Deploy Backend
echo -e "${GREEN}🔨 Deploying Backend...${NC}"
gcloud run deploy $BACKEND_SERVICE \
  --source . \
  --dockerfile Dockerfile.backend \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --min-instances 0 \
  --max-instances 10 \
  --timeout 300 \
  --set-env-vars PYTHONUNBUFFERED=1

# Get Backend URL
BACKEND_URL=$(gcloud run services describe $BACKEND_SERVICE \
  --region $REGION \
  --format 'value(status.url)')

echo -e "${GREEN}✅ Backend deployed: $BACKEND_URL${NC}"

# Deploy Frontend
echo -e "${GREEN}🔨 Deploying Frontend...${NC}"
gcloud run deploy $FRONTEND_SERVICE \
  --source . \
  --dockerfile Dockerfile.frontend \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars API_URL=$BACKEND_URL \
  --memory 1Gi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 5 \
  --timeout 60

# Get Frontend URL
FRONTEND_URL=$(gcloud run services describe $FRONTEND_SERVICE \
  --region $REGION \
  --format 'value(status.url)')

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}Backend URL:${NC}  $BACKEND_URL"
echo -e "${BLUE}Frontend URL:${NC} $FRONTEND_URL"
echo ""
echo -e "${BLUE}Health Check:${NC} $BACKEND_URL/health"
echo ""
echo "🎉 Your EmpathicGateway is now live!"
