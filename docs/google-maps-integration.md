# Google Maps Integration Guide

## Overview

This guide explains how to integrate Google Maps into your LiveKit agent for navigation assistance. The integration uses the Model Context Protocol (MCP) to provide tools for finding places, getting directions, and geocoding addresses.

## Features

The Google Maps MCP server provides the following capabilities:

1. **Search Nearby Places** - Find restaurants, hospitals, pharmacies, stores, and other points of interest near a location
2. **Get Directions** - Get step-by-step walking, driving, or transit directions between two locations
3. **Geocode Addresses** - Convert addresses to coordinates
4. **Reverse Geocode** - Convert coordinates to human-readable addresses

## Prerequisites

1. **Google Cloud Project** with billing enabled
2. **Google Maps API Key** with the following APIs enabled:
   - Places API
   - Directions API
   - Geocoding API
3. **Python dependencies** installed (see Installation section)

## Installation

### 1. Install Dependencies

The Google Maps integration requires the `googlemaps` library:

```bash
pip install googlemaps>=4.10.0
```

Or install all dependencies:

```bash
pip install -r requirements.txt
```

### 2. Get Google Maps API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable billing (Google provides $200/month free credit)
4. Navigate to [APIs & Services > Library](https://console.cloud.google.com/apis/library)
5. Enable the following APIs:
   - **Places API** - For searching nearby places
   - **Directions API** - For getting directions
   - **Geocoding API** - For address/coordinate conversion
6. Go to [APIs & Services > Credentials](https://console.cloud.google.com/apis/credentials)
7. Click "Create Credentials" > "API Key"
8. Copy your API key
9. (Recommended) Restrict the API key to only the enabled APIs

### 3. Configure Environment Variables

Add your Google Maps API key to your `.env` file:

```bash
GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here
```

## Running the Google Maps MCP Server

### Option 1: Run as Standalone Server

Run the MCP server as a separate process:

```bash
python scripts/run_google_maps_mcp.py
```

The server will start on `http://localhost:8080` by default. You can customize the port:

```bash
GOOGLE_MAPS_MCP_PORT=8081 python scripts/run_google_maps_mcp.py
```

### Option 2: Run with Uvicorn Directly

```bash
uvicorn app.mcp.google_maps_server:app --port 8080 --host 0.0.0.0
```

### Option 3: Deploy to Google Cloud Run (Recommended for Production)

Deploy the MCP server to Google Cloud Run for a fully managed, scalable service:

```bash
# Using the deployment script
export GOOGLE_MAPS_API_KEY=your_api_key_here
./scripts/deploy-google-maps-mcp.sh
```

For detailed Cloud Run deployment instructions, see the [Cloud Run Deployment Guide](./cloud-run-deployment.md).

### Option 4: Deploy to Other Platforms

For production, you can also deploy the MCP server as a separate service on other platforms (e.g., Heroku, Railway, AWS ECS, Azure Container Instances) and configure the agent to use the deployed URL.

## Configuring the Agent

### 1. Update Environment Variables

In your `.env` file, configure the MCP server URL:

```bash
# For local development
MCP_SERVER_URLS=http://localhost:8080

# For production (if deployed separately)
MCP_SERVER_URLS=https://your-google-maps-mcp-server.com
```

If your MCP server requires authentication:

```bash
MCP_SERVER_HEADERS={"https://your-server.com": {"Authorization": "Bearer your_token"}}
```

### 2. Verify Agent Configuration

The agent automatically loads MCP servers from the `MCP_SERVER_URLS` environment variable. The Google Maps tools will be available to the agent once the MCP server is running and configured.

## Available Tools

### 1. search_nearby_places

Search for places near a location.

**Parameters:**
- `location` (required): Location as `"latitude,longitude"` or address (e.g., `"48.8566,2.3522"` or `"Paris, France"`)
- `radius` (optional): Search radius in meters (default: 1000, max: 50000)
- `type` (optional): Type of place (e.g., `"restaurant"`, `"hospital"`, `"pharmacy"`, `"store"`, `"bank"`, `"gas_station"`)
- `keyword` (optional): Keyword to search for (e.g., `"coffee"`, `"pharmacy"`, `"ATM"`)

**Example Usage:**
- "Find nearby restaurants"
- "Where is the nearest pharmacy?"
- "Show me coffee shops near me"
- "Find hospitals within 2 kilometers"

### 2. get_directions

Get step-by-step directions between two locations.

**Parameters:**
- `origin` (required): Starting location (address or `"latitude,longitude"`)
- `destination` (required): Destination location (address or `"latitude,longitude"`)
- `mode` (optional): Transportation mode - `"walking"`, `"driving"`, or `"transit"` (default: `"walking"`)
- `alternatives` (optional): Return alternative routes (default: `false`)

**Example Usage:**
- "How do I get to the Eiffel Tower?"
- "Give me walking directions to 123 Main Street"
- "What's the best route to the airport?"

### 3. geocode_address

Convert an address to coordinates.

**Parameters:**
- `address` (required): Address to geocode (e.g., `"1600 Amphitheatre Parkway, Mountain View, CA"`)

**Example Usage:**
- "What are the coordinates for the Louvre Museum?"
- "Where is 123 Main Street located?"

### 4. reverse_geocode

Convert coordinates to a human-readable address.

**Parameters:**
- `lat` (required): Latitude coordinate
- `lng` (required): Longitude coordinate

**Example Usage:**
- "What address is at coordinates 48.8566, 2.3522?"

## Example Conversations

### Finding Nearby Places

**User:** "Find nearby restaurants"

**Agent:** "I'll search for restaurants near your location... I found 5 restaurants nearby:
1. Le Comptoir du Relais - 132 meters away, rated 4.5 stars
2. L'As du Fallafel - 250 meters away, rated 4.3 stars
3. Breizh Café - 180 meters away, rated 4.4 stars
..."

### Getting Directions

**User:** "How do I get to the Eiffel Tower?"

**Agent:** "I'll get walking directions to the Eiffel Tower... Here are the step-by-step directions:
1. Head northeast on Rue de Rivoli toward Rue du Louvre (50 meters)
2. Turn right onto Rue du Louvre (200 meters)
3. Continue straight onto Boulevard de Sébastopol (500 meters)
...
Total distance: 2.3 kilometers, estimated walking time: 28 minutes"

## Testing the Integration

### 1. Test the MCP Server Directly

Check if the server is running:

```bash
curl http://localhost:8080/health
```

List available tools:

```bash
curl http://localhost:8080/tools
```

Test a tool call:

```bash
curl -X POST http://localhost:8080/tools/search_nearby_places \
  -H "Content-Type: application/json" \
  -d '{"location": "48.8566,2.3522", "type": "restaurant", "radius": 1000}'
```

### 2. Test Through the Agent

Start your agent and try these voice commands:

- "Find nearby coffee shops"
- "Where is the nearest pharmacy?"
- "How do I get to the train station?"
- "Give me directions to 123 Main Street"

## Troubleshooting

### Issue: "Google Maps API key not configured"

**Solution:** Make sure `GOOGLE_MAPS_API_KEY` is set in your environment variables or `.env` file.

### Issue: "API key not valid"

**Solution:** 
1. Verify your API key is correct
2. Ensure the required APIs are enabled in Google Cloud Console
3. Check if your API key has restrictions that might be blocking requests

### Issue: "MCP server not found"

**Solution:**
1. Verify the MCP server is running: `curl http://localhost:8080/health`
2. Check that `MCP_SERVER_URLS` in your `.env` matches the server URL
3. Ensure the server is accessible from where your agent is running

### Issue: "No places found" or "No directions found"

**Solution:**
1. Verify the location/address is valid
2. Try a larger search radius
3. Check if the location exists in Google Maps

## Best Practices

1. **API Key Security**: Never commit your API key to version control. Use environment variables and `.env` files (which should be in `.gitignore`).

2. **Rate Limiting**: Google Maps APIs have rate limits. Monitor your usage in the Google Cloud Console to avoid unexpected charges.

3. **Error Handling**: The agent handles errors gracefully, but you should monitor logs for API errors.

4. **Caching**: Consider implementing caching for frequently requested locations to reduce API calls.

5. **User Privacy**: Be mindful of user location data. Only request location when necessary and handle it securely.

## Cost Considerations

Google Maps Platform offers:
- **$200/month free credit** for eligible accounts
- Pay-as-you-go pricing after free credit
- Most common operations (geocoding, directions, places) are very affordable

Monitor your usage in the [Google Cloud Console](https://console.cloud.google.com/billing).

## Additional Resources

- [Google Maps Platform Documentation](https://developers.google.com/maps/documentation)
- [Places API Documentation](https://developers.google.com/maps/documentation/places/web-service)
- [Directions API Documentation](https://developers.google.com/maps/documentation/directions)
- [Geocoding API Documentation](https://developers.google.com/maps/documentation/geocoding)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [LiveKit Agents MCP Documentation](docs/mcp-servers-with-livekit-agents.md)

## Next Steps

1. Set up your Google Maps API key
2. Run the MCP server
3. Configure your agent to use the MCP server
4. Test the integration with voice commands
5. Customize the agent instructions to better utilize Google Maps features

For more advanced use cases, consider:
- Adding custom place types
- Implementing route optimization
- Adding real-time traffic information
- Integrating with other location-based services

