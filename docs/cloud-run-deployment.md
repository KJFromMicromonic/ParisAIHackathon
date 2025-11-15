# Deploying Google Maps MCP Server to Cloud Run

This guide explains how to deploy your Google Maps MCP server to Google Cloud Run for production use.

## Prerequisites

1. **Google Cloud Account** with billing enabled
2. **gcloud CLI** installed and configured
   - Install: https://cloud.google.com/sdk/docs/install
   - Authenticate: `gcloud auth login`
   - Set project: `gcloud config set project YOUR_PROJECT_ID`
3. **Docker** installed locally
4. **Google Maps API Key** (already configured)

## Quick Start

### Option 1: Using the Deployment Script (Recommended)

#### Linux/macOS:

```bash
export GOOGLE_MAPS_API_KEY=your_api_key_here
export GOOGLE_CLOUD_PROJECT=your-project-id  # Optional, uses gcloud default
export GOOGLE_CLOUD_REGION=us-central1      # Optional, defaults to us-central1

chmod +x scripts/deploy-google-maps-mcp.sh
./scripts/deploy-google-maps-mcp.sh
```

#### Windows PowerShell:

```powershell
$env:GOOGLE_MAPS_API_KEY = "your_api_key_here"
$env:GOOGLE_CLOUD_PROJECT = "your-project-id"  # Optional
$env:GOOGLE_CLOUD_REGION = "us-central1"       # Optional

.\scripts\deploy-google-maps-mcp.ps1
```

### Option 2: Manual Deployment

1. **Enable Required APIs:**

```bash
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

2. **Build and Push Docker Image:**

```bash
PROJECT_ID=$(gcloud config get-value project)
IMAGE_NAME="gcr.io/${PROJECT_ID}/google-maps-mcp-server"

docker build -f docker/Dockerfile.google-maps-mcp -t ${IMAGE_NAME} .
docker push ${IMAGE_NAME}
```

3. **Deploy to Cloud Run:**

```bash
gcloud run deploy google-maps-mcp-server \
    --image gcr.io/${PROJECT_ID}/google-maps-mcp-server \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars GOOGLE_MAPS_API_KEY=${GOOGLE_MAPS_API_KEY} \
    --memory 512Mi \
    --cpu 1 \
    --timeout 300 \
    --max-instances 10 \
    --min-instances 0 \
    --port 8080
```

## Configuration Options

### Environment Variables

- `GOOGLE_MAPS_API_KEY` (required): Your Google Maps API key
- `PORT` (optional): Server port (default: 8080, Cloud Run sets this automatically)

### Cloud Run Settings

- **Memory**: 512Mi (adjust based on usage)
- **CPU**: 1 vCPU (sufficient for most use cases)
- **Timeout**: 300 seconds (5 minutes)
- **Max Instances**: 10 (scale up as needed)
- **Min Instances**: 0 (scale to zero when not in use)

### Customization

To customize deployment settings, edit the deployment command:

```bash
gcloud run deploy google-maps-mcp-server \
    --image gcr.io/${PROJECT_ID}/google-maps-mcp-server \
    --memory 1Gi \              # Increase memory
    --cpu 2 \                   # Increase CPU
    --max-instances 20 \        # Scale up
    --min-instances 1 \         # Keep warm (reduces cold starts)
    --timeout 600 \            # Longer timeout
    --region europe-west1      # Different region
```

## Verifying Deployment

After deployment, test your service:

```bash
# Get the service URL
SERVICE_URL=$(gcloud run services describe google-maps-mcp-server \
    --region us-central1 \
    --format 'value(status.url)')

# Test health endpoint
curl ${SERVICE_URL}/health

# List available tools
curl ${SERVICE_URL}/tools

# Test a tool call
curl -X POST ${SERVICE_URL}/tools/search_nearby_places \
  -H "Content-Type: application/json" \
  -d '{"location": "48.8566,2.3522", "type": "restaurant", "radius": 1000}'
```

## Updating Your Agent Configuration

Once deployed, update your `.env` file to use the Cloud Run URL:

```bash
# Replace localhost URL with Cloud Run URL
MCP_SERVER_URLS=https://google-maps-mcp-server-xxxxx-uc.a.run.app
```

Or if you have multiple MCP servers:

```bash
MCP_SERVER_URLS=https://google-maps-mcp-server-xxxxx-uc.a.run.app,https://other-mcp-server.com
```

## Updating the Deployment

To update the deployment with new code:

1. **Rebuild and push the image:**

```bash
PROJECT_ID=$(gcloud config get-value project)
IMAGE_NAME="gcr.io/${PROJECT_ID}/google-maps-mcp-server"

docker build -f docker/Dockerfile.google-maps-mcp -t ${IMAGE_NAME} .
docker push ${IMAGE_NAME}
```

2. **Redeploy (Cloud Run will use the new image):**

```bash
gcloud run deploy google-maps-mcp-server \
    --image ${IMAGE_NAME} \
    --region us-central1
```

Or simply run the deployment script again - it will rebuild and redeploy.

## Monitoring and Logs

### View Logs

```bash
gcloud run services logs read google-maps-mcp-server \
    --region us-central1 \
    --limit 50
```

### Monitor in Cloud Console

1. Go to [Cloud Run Console](https://console.cloud.google.com/run)
2. Click on your service
3. View metrics, logs, and revisions

## Cost Considerations

Cloud Run pricing:
- **Free tier**: 2 million requests/month, 360,000 GB-seconds, 180,000 vCPU-seconds
- **Pay-as-you-go**: After free tier, very affordable for most use cases
- **Scaling**: Only pay for what you use (scales to zero)

Typical costs for moderate usage:
- ~$5-20/month for most applications
- Scales automatically based on traffic

## Security Best Practices

1. **API Key Security**: 
   - Never commit API keys to version control
   - Use Cloud Run secrets or environment variables
   - Consider using Google Secret Manager for sensitive keys

2. **Access Control**:
   - Use `--no-allow-unauthenticated` if you want to restrict access
   - Implement authentication headers if needed
   - Use Cloud IAM for service-to-service authentication

3. **API Key Restrictions**:
   - Restrict your Google Maps API key to specific APIs
   - Add IP restrictions if possible
   - Monitor usage in Google Cloud Console

## Troubleshooting

### Issue: "Permission denied" when pushing image

**Solution**: Ensure you're authenticated and have the right permissions:
```bash
gcloud auth configure-docker
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="user:YOUR_EMAIL" \
    --role="roles/storage.admin"
```

### Issue: "Service not found" when deploying

**Solution**: Ensure Cloud Run API is enabled:
```bash
gcloud services enable run.googleapis.com
```

### Issue: "Image pull failed"

**Solution**: Check that the image was pushed successfully:
```bash
gcloud container images list --repository=gcr.io/YOUR_PROJECT_ID
```

### Issue: Service returns 500 errors

**Solution**: Check logs for errors:
```bash
gcloud run services logs read google-maps-mcp-server --region us-central1
```

Common causes:
- Missing `GOOGLE_MAPS_API_KEY` environment variable
- Invalid API key
- API key doesn't have required APIs enabled

## Using with Your Current Project

Your current project already has MCP router support configured. Once deployed:

1. **Get the Cloud Run URL** from the deployment output
2. **Update `.env`**:
   ```bash
   MCP_SERVER_URLS=https://your-cloud-run-url
   ```
3. **Restart your agent** - it will automatically connect to the Cloud Run MCP server

The agent's `MCPRouter` class will automatically:
- Discover tools from the Cloud Run server
- Route tool calls to the server
- Handle errors gracefully

## Next Steps

- Monitor usage and costs in Google Cloud Console
- Set up alerts for errors or high usage
- Consider adding authentication if needed
- Scale resources based on actual usage patterns

For more information, see:
- [Google Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Cloud Run Pricing](https://cloud.google.com/run/pricing)
- [Google Maps Integration Guide](./google-maps-integration.md)

