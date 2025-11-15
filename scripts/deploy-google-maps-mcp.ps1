# PowerShell script to deploy Google Maps MCP Server to Google Cloud Run
#
# Prerequisites:
# 1. Install gcloud CLI: https://cloud.google.com/sdk/docs/install
# 2. Authenticate: gcloud auth login
# 3. Set your project: gcloud config set project YOUR_PROJECT_ID
# 4. Enable APIs: gcloud services enable run.googleapis.com cloudbuild.googleapis.com
# 5. Set GOOGLE_MAPS_API_KEY environment variable

$ErrorActionPreference = "Stop"

# Configuration
$PROJECT_ID = if ($env:GOOGLE_CLOUD_PROJECT) { $env:GOOGLE_CLOUD_PROJECT } else { (gcloud config get-value project) }
$SERVICE_NAME = "google-maps-mcp-server"
$REGION = if ($env:GOOGLE_CLOUD_REGION) { $env:GOOGLE_CLOUD_REGION } else { "us-central1" }
$IMAGE_NAME = "gcr.io/$PROJECT_ID/$SERVICE_NAME"

Write-Host "Deploying Google Maps MCP Server to Cloud Run..." -ForegroundColor Green
Write-Host "Project: $PROJECT_ID"
Write-Host "Service: $SERVICE_NAME"
Write-Host "Region: $REGION"
Write-Host ""

# Check if GOOGLE_MAPS_API_KEY is set
if (-not $env:GOOGLE_MAPS_API_KEY) {
    Write-Host "Error: GOOGLE_MAPS_API_KEY environment variable is not set" -ForegroundColor Red
    Write-Host "Please set it with: `$env:GOOGLE_MAPS_API_KEY='your_api_key'"
    exit 1
}

# Build the Docker image
Write-Host "Building Docker image..." -ForegroundColor Yellow
docker build -f docker/Dockerfile.google-maps-mcp -t $IMAGE_NAME .

# Push to Google Container Registry
Write-Host "Pushing image to Google Container Registry..." -ForegroundColor Yellow
docker push $IMAGE_NAME

# Deploy to Cloud Run
Write-Host "Deploying to Cloud Run..." -ForegroundColor Yellow
gcloud run deploy $SERVICE_NAME `
    --image $IMAGE_NAME `
    --platform managed `
    --region $REGION `
    --allow-unauthenticated `
    --set-env-vars "GOOGLE_MAPS_API_KEY=$env:GOOGLE_MAPS_API_KEY" `
    --memory 512Mi `
    --cpu 1 `
    --timeout 300 `
    --max-instances 10 `
    --min-instances 0 `
    --port 8080

# Get the service URL
$SERVICE_URL = gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)'

Write-Host ""
Write-Host "Deployment successful!" -ForegroundColor Green
Write-Host "Service URL: $SERVICE_URL" -ForegroundColor Green
Write-Host ""
Write-Host "Test the deployment:"
Write-Host "  curl $SERVICE_URL/health"
Write-Host "  curl $SERVICE_URL/tools"
Write-Host ""
Write-Host "Update your .env file with:"
Write-Host "  MCP_SERVER_URLS=$SERVICE_URL"

