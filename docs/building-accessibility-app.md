# Building an Accessibility App for Blind/Visually Impaired Users with LiveKit Agents

## Overview

This guide provides a comprehensive approach to building a voice-based accessibility application for blind and visually impaired users using LiveKit Agents, Gemini Live realtime models, and self-hosted MCP servers. The application will help users identify obstacles, find places using Google Maps, and book Airbnb properties through natural voice interaction.

## Architecture Overview

```
┌─────────────────┐
│  User (Voice)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  LiveKit Client │ ◄─── JavaScript/TypeScript
│   (Browser/App) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  LiveKit Server │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  LiveKit Agent  │ ◄─── Python
│  (Gemini Live)  │
└────────┬────────┘
         │
         ├──► Google Maps MCP Server
         ├──► Airbnb MCP Server
         └──► Obstacle Detection Service
```

## Prerequisites

1. **Python 3.9+** for the agent backend
2. **Node.js** for the JavaScript client
3. **LiveKit Server** (Cloud or self-hosted)
4. **API Keys:**
   - Google API Key (for Gemini Live API)
   - Google Maps API Key
   - Airbnb API credentials (if using official API)
   - LiveKit API Key and Secret

## Step 1: Set Up the Agent Backend

### Install Dependencies

```shell
uv add "livekit-agents[google,mcp]~=1.2"
```

### Create the Agent Entrypoint

```python
# agent.py
from livekit import agents
from livekit.agents import AgentSession, mcp
from livekit.plugins import google
import os

async def entrypoint(ctx: agents.JobContext):
    await ctx.connect()
    
    # Initialize the agent session with Gemini Live
    session = AgentSession(
        llm=google.realtime.RealtimeModel(
            model="gemini-2.0-flash-exp",
            voice="Puck",
            instructions="""You are a helpful assistant for visually impaired users. 
            Your role is to:
            1. Help users identify obstacles and navigate safely
            2. Find nearby places using Google Maps
            3. Get directions to locations
            4. Search and book Airbnb properties
            
            Always:
            - Speak clearly and provide detailed descriptions
            - Describe distances and directions in a way that's easy to understand
            - Confirm important actions before executing them
            - Provide step-by-step guidance for navigation"""
        ),
        mcp_servers=[
            mcp.MCPServerHTTP(
                os.getenv("GOOGLE_MAPS_MCP_SERVER_URL", "http://localhost:8080/mcp"),
                headers={
                    "Authorization": f"Bearer {os.getenv('GOOGLE_MAPS_API_KEY')}"
                }
            ),
            mcp.MCPServerHTTP(
                os.getenv("AIRBNB_MCP_SERVER_URL", "http://localhost:8081/mcp"),
                headers={
                    "Authorization": f"Bearer {os.getenv('AIRBNB_API_KEY')}"
                }
            ),
        ]
    )
    
    await session.start(ctx.room)

if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
```

## Step 2: Create MCP Servers

### Google Maps MCP Server

Your Google Maps MCP server should expose tools like:

```python
# google_maps_mcp_server.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import googlemaps

app = FastAPI()
gmaps = googlemaps.Client(key=os.getenv("GOOGLE_MAPS_API_KEY"))

class SearchNearbyRequest(BaseModel):
    location: str  # "latitude,longitude" or address
    radius: int = 1000  # meters
    type: str = None  # e.g., "restaurant", "hospital", "pharmacy"

class GetDirectionsRequest(BaseModel):
    origin: str
    destination: str
    mode: str = "walking"  # "walking", "driving", "transit"

@app.post("/mcp/tools/search_nearby_places")
async def search_nearby_places(request: SearchNearbyRequest):
    """Search for places near a location"""
    try:
        # Geocode the location if it's an address
        if "," not in request.location:
            geocode_result = gmaps.geocode(request.location)
            location = geocode_result[0]['geometry']['location']
            location_str = f"{location['lat']},{location['lng']}"
        else:
            location_str = request.location
        
        # Search nearby places
        places_result = gmaps.places_nearby(
            location=location_str,
            radius=request.radius,
            type=request.type
        )
        
        # Format results for voice output
        results = []
        for place in places_result.get('results', [])[:5]:
            results.append({
                "name": place.get('name'),
                "address": place.get('vicinity'),
                "rating": place.get('rating'),
                "distance": "N/A"  # Calculate if needed
            })
        
        return {
            "places": results,
            "count": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mcp/tools/get_directions")
async def get_directions(request: GetDirectionsRequest):
    """Get walking directions between two points"""
    try:
        directions_result = gmaps.directions(
            request.origin,
            request.destination,
            mode=request.mode
        )
        
        if not directions_result:
            return {"error": "No directions found"}
        
        route = directions_result[0]
        leg = route['legs'][0]
        
        # Format for voice output
        steps = []
        for step in leg['steps']:
            steps.append({
                "instruction": step['html_instructions'].replace('<b>', '').replace('</b>', ''),
                "distance": step['distance']['text'],
                "duration": step['duration']['text']
            })
        
        return {
            "origin": leg['start_address'],
            "destination": leg['end_address'],
            "total_distance": leg['distance']['text'],
            "total_duration": leg['duration']['text'],
            "steps": steps
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# MCP protocol endpoints
@app.get("/mcp/tools")
async def list_tools():
    """List available MCP tools"""
    return {
        "tools": [
            {
                "name": "search_nearby_places",
                "description": "Search for places near a location. Useful for finding restaurants, hospitals, pharmacies, etc.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "Location as 'latitude,longitude' or address"
                        },
                        "radius": {
                            "type": "integer",
                            "description": "Search radius in meters (default: 1000)"
                        },
                        "type": {
                            "type": "string",
                            "description": "Type of place (e.g., 'restaurant', 'hospital', 'pharmacy')"
                        }
                    },
                    "required": ["location"]
                }
            },
            {
                "name": "get_directions",
                "description": "Get walking directions between two locations",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "origin": {
                            "type": "string",
                            "description": "Starting location"
                        },
                        "destination": {
                            "type": "string",
                            "description": "Destination location"
                        },
                        "mode": {
                            "type": "string",
                            "description": "Transportation mode: 'walking', 'driving', or 'transit'"
                        }
                    },
                    "required": ["origin", "destination"]
                }
            }
        ]
    }
```

### Airbnb MCP Server

```python
# airbnb_mcp_server.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests

app = FastAPI()

class SearchPropertiesRequest(BaseModel):
    location: str
    check_in: str  # YYYY-MM-DD
    check_out: str  # YYYY-MM-DD
    guests: int = 1

@app.post("/mcp/tools/search_properties")
async def search_properties(request: SearchPropertiesRequest):
    """Search for available Airbnb properties"""
    # Implement Airbnb API integration
    # Note: Airbnb doesn't have a public API, so you'll need to:
    # 1. Use a third-party service
    # 2. Web scrape (with proper permissions)
    # 3. Use Airbnb's partner API if available
    
    # Example response structure
    return {
        "properties": [
            {
                "id": "12345",
                "name": "Cozy Studio Apartment",
                "location": "Downtown",
                "price": 89,
                "rating": 4.8,
                "available": True
            }
        ]
    }

@app.get("/mcp/tools")
async def list_tools():
    return {
        "tools": [
            {
                "name": "search_properties",
                "description": "Search for available Airbnb properties in a location",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string"},
                        "check_in": {"type": "string"},
                        "check_out": {"type": "string"},
                        "guests": {"type": "integer"}
                    },
                    "required": ["location", "check_in", "check_out"]
                }
            }
        ]
    }
```

## Step 3: Create the JavaScript Client

### Install Dependencies

```shell
npm install livekit-client
```

### Basic Client Implementation

```typescript
// client.ts
import { Room, RoomEvent, Track } from 'livekit-client';

class AccessibilityApp {
  private room: Room;
  private wsUrl: string;
  
  constructor(wsUrl: string) {
    this.wsUrl = wsUrl;
    this.room = new Room({
      adaptiveStream: true,
      dynacast: true,
    });
    
    this.setupEventHandlers();
  }
  
  async connect(token: string) {
    try {
      await this.room.connect(this.wsUrl, token);
      console.log('Connected to room:', this.room.name);
      
      // Enable microphone for voice interaction
      await this.room.localParticipant.setMicrophoneEnabled(true);
    } catch (error) {
      console.error('Failed to connect:', error);
      throw error;
    }
  }
  
  private setupEventHandlers() {
    // Handle agent audio
    this.room.on(RoomEvent.TrackSubscribed, (track, publication, participant) => {
      if (track.kind === Track.Kind.Audio && participant.identity.startsWith('agent')) {
        const audioElement = track.attach();
        document.body.appendChild(audioElement);
      }
    });
    
    // Handle disconnection
    this.room.on(RoomEvent.Disconnected, () => {
      console.log('Disconnected from room');
    });
    
    // Handle reconnection
    this.room.on(RoomEvent.Reconnecting, () => {
      console.log('Reconnecting...');
    });
    
    this.room.on(RoomEvent.Reconnected, () => {
      console.log('Reconnected successfully');
    });
  }
  
  async disconnect() {
    await this.room.disconnect();
  }
}

// Usage
const app = new AccessibilityApp('wss://your-livekit-server.com');
const token = await fetch('/api/token').then(r => r.text());
await app.connect(token);
```

## Step 4: Obstacle Detection Integration

For obstacle detection, you can integrate with:

1. **Camera-based detection** (if user has a smartphone with camera)
2. **LiDAR sensors** (on supported devices)
3. **External sensors** via IoT integration

Example integration:

```python
# obstacle_detection.py
from livekit.agents import function_tool, RunContext

class ObstacleDetectionAgent:
    @function_tool()
    async def detect_obstacles(
        self,
        context: RunContext,
        image_data: str = None,  # Base64 encoded image
    ) -> dict:
        """Detect obstacles in the user's path using computer vision.
        
        Args:
            image_data: Base64 encoded image from user's camera
        """
        # Integrate with your obstacle detection model
        # This could use:
        # - YOLO for object detection
        # - Depth estimation models
        # - Custom trained models
        
        obstacles = await detect_obstacles_in_image(image_data)
        
        return {
            "obstacles": [
                {
                    "type": obstacle.type,
                    "distance": obstacle.distance,
                    "direction": obstacle.direction,
                    "severity": obstacle.severity
                }
                for obstacle in obstacles
            ],
            "recommendation": generate_navigation_recommendation(obstacles)
        }
```

## Step 5: Environment Configuration

Create a `.env` file:

```env
# LiveKit
LIVEKIT_URL=wss://your-livekit-server.com
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret

# Google
GOOGLE_API_KEY=your_google_api_key
GOOGLE_MAPS_API_KEY=your_google_maps_api_key

# MCP Servers
GOOGLE_MAPS_MCP_SERVER_URL=http://localhost:8080/mcp
AIRBNB_MCP_SERVER_URL=http://localhost:8081/mcp

# Airbnb (if using API)
AIRBNB_API_KEY=your_airbnb_api_key
```

## Step 6: Running the Application

1. **Start MCP Servers:**

```shell
# Terminal 1: Google Maps MCP Server
uvicorn google_maps_mcp_server:app --port 8080

# Terminal 2: Airbnb MCP Server
uvicorn airbnb_mcp_server:app --port 8081
```

2. **Start the Agent:**

```shell
uv run agent.py dev
```

3. **Start the Client:**

```shell
npm run dev
```

## Best Practices for Accessibility

1. **Voice-First Design:**
   - All interactions should be voice-based
   - Provide clear audio feedback for all actions
   - Use natural language for responses

2. **Error Handling:**
   - Provide clear, actionable error messages
   - Offer alternative solutions when operations fail
   - Confirm important actions before executing

3. **Navigation Assistance:**
   - Describe distances in relatable terms ("about 50 steps ahead")
   - Use cardinal directions consistently
   - Provide landmarks and context

4. **Privacy and Security:**
   - Handle location data securely
   - Don't store sensitive information unnecessarily
   - Get explicit consent for location sharing

5. **Performance:**
   - Minimize latency for real-time interactions
   - Cache frequently accessed data
   - Optimize MCP server responses

## Additional Resources

- [LiveKit Agents Documentation](https://docs.livekit.io/agents/)
- [Gemini Live API](https://docs.livekit.io/agents/models/realtime/plugins/gemini/)
- [MCP Protocol](https://modelcontextprotocol.io/)
- [Google Maps API](https://developers.google.com/maps)
- [Web Content Accessibility Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)

## Testing

Test your application with:
1. Various voice commands and natural language inputs
2. Different network conditions
3. Multiple concurrent users
4. Error scenarios (API failures, network issues)

## Deployment

Consider deploying:
- MCP servers on cloud platforms (AWS, GCP, Azure)
- Agent workers on scalable infrastructure
- Client application as a Progressive Web App (PWA) for easy access

