#!/bin/bash
# Deploy Google Maps MCP Server to Google Cloud Run
#
# Prerequisites:
# 1. Install gcloud CLI: https://cloud.google.com/sdk/docs/install
# 2. Authenticate: gcloud auth login
# 3. Set your project: gcloud config set project YOUR_PROJECT_ID
# 4. Enable APIs: gcloud services enable run.googleapis.com cloudbuild.googleapis.com
# 5. Set GOOGLE_MAPS_API_KEY environment variable

set -e

# Configuration
PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-$(gcloud config get-value project)}
SERVICE_NAME="google-maps-mcp-server"
REGION=${GOOGLE_CLOUD_REGION:-us-central1}
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Deploying Google Maps MCP Server to Cloud Run...${NC}"
echo "Project: ${PROJECT_ID}"
echo "Service: ${SERVICE_NAME}"
echo "Region: ${REGION}"
echo ""

# Check if GOOGLE_MAPS_API_KEY is set
if [ -z "$GOOGLE_MAPS_API_KEY" ]; then
    echo -e "${RED}Error: GOOGLE_MAPS_API_KEY environment variable is not set${NC}"
    echo "Please set it with: export GOOGLE_MAPS_API_KEY=your_api_key"
    exit 1
fi

# Build the Docker image
echo -e "${YELLOW}Building Docker image...${NC}"
docker build -f docker/Dockerfile.google-maps-mcp -t ${IMAGE_NAME} .

# Push to Google Container Registry
echo -e "${YELLOW}Pushing image to Google Container Registry...${NC}"
docker push ${IMAGE_NAME}

# Deploy to Cloud Run
echo -e "${YELLOW}Deploying to Cloud Run...${NC}"
gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME} \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --set-env-vars GOOGLE_MAPS_API_KEY=${GOOGLE_MAPS_API_KEY} \
    --memory 512Mi \
    --cpu 1 \
    --timeout 300 \
    --max-instances 10 \
    --min-instances 0 \
    --port 8080

# Get the service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format 'value(status.url)')

echo ""
echo -e "${GREEN}Deployment successful!${NC}"
echo -e "${GREEN}Service URL: ${SERVICE_URL}${NC}"
echo ""
echo "Test the deployment:"
echo "  curl ${SERVICE_URL}/health"
echo "  curl ${SERVICE_URL}/tools"
echo ""
echo "Update your .env file with:"
echo "  MCP_SERVER_URLS=${SERVICE_URL}"

