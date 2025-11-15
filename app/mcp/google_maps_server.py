"""Google Maps MCP Server implementation."""

import os
from typing import Any, Dict, List, Optional

import googlemaps
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.core.config import settings

app = FastAPI(title="Google Maps MCP Server")

# Initialize Google Maps client
_gmaps_client: Optional[googlemaps.Client] = None


def get_gmaps_client() -> googlemaps.Client:
    """
    Get or create Google Maps client instance.

    Returns:
        Google Maps client instance

    Raises:
        ValueError: If Google Maps API key is not configured
    """
    global _gmaps_client
    if _gmaps_client is None:
        api_key = os.getenv("GOOGLE_MAPS_API_KEY") or getattr(
            settings, "google_maps_api_key", None
        )
        if not api_key:
            raise ValueError(
                "GOOGLE_MAPS_API_KEY environment variable is required for Google Maps integration"
            )
        _gmaps_client = googlemaps.Client(key=api_key)
    return _gmaps_client


# Request/Response Models
class SearchNearbyRequest(BaseModel):
    """Request model for searching nearby places."""

    location: str = Field(..., description="Location as 'latitude,longitude' or address")
    radius: int = Field(default=1000, description="Search radius in meters")
    type: Optional[str] = Field(
        default=None, description="Type of place (e.g., 'restaurant', 'hospital', 'pharmacy')"
    )
    keyword: Optional[str] = Field(
        default=None, description="Keyword to search for (e.g., 'coffee', 'pharmacy')"
    )


class GetDirectionsRequest(BaseModel):
    """Request model for getting directions."""

    origin: str = Field(..., description="Starting location (address or lat,lng)")
    destination: str = Field(..., description="Destination location (address or lat,lng)")
    mode: str = Field(
        default="walking", description="Transportation mode: 'walking', 'driving', or 'transit'"
    )
    alternatives: bool = Field(default=False, description="Return alternative routes")


class GeocodeRequest(BaseModel):
    """Request model for geocoding an address."""

    address: str = Field(..., description="Address to geocode")


class ReverseGeocodeRequest(BaseModel):
    """Request model for reverse geocoding coordinates."""

    lat: float = Field(..., description="Latitude")
    lng: float = Field(..., description="Longitude")


# MCP Protocol Endpoints
@app.get("/tools")
async def list_tools() -> Dict[str, Any]:
    """
    List available MCP tools following the MCP protocol.

    Returns:
        Dictionary containing list of available tools
    """
    return {
        "tools": [
            {
                "name": "search_nearby_places",
                "description": "Search for places near a location. Useful for finding restaurants, hospitals, pharmacies, stores, and other points of interest. Returns up to 5 nearby places with names, addresses, ratings, and distances.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "Location as 'latitude,longitude' (e.g., '48.8566,2.3522') or address (e.g., 'Paris, France')",
                        },
                        "radius": {
                            "type": "integer",
                            "description": "Search radius in meters (default: 1000, max: 50000)",
                            "default": 1000,
                        },
                        "type": {
                            "type": "string",
                            "description": "Type of place (e.g., 'restaurant', 'hospital', 'pharmacy', 'store', 'bank', 'gas_station')",
                        },
                        "keyword": {
                            "type": "string",
                            "description": "Keyword to search for (e.g., 'coffee', 'pharmacy', 'ATM')",
                        },
                    },
                    "required": ["location"],
                },
            },
            {
                "name": "get_directions",
                "description": "Get step-by-step directions between two locations. Perfect for navigation assistance. Returns detailed walking, driving, or transit directions with turn-by-turn instructions.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "origin": {
                            "type": "string",
                            "description": "Starting location (address or 'latitude,longitude')",
                        },
                        "destination": {
                            "type": "string",
                            "description": "Destination location (address or 'latitude,longitude')",
                        },
                        "mode": {
                            "type": "string",
                            "enum": ["walking", "driving", "transit"],
                            "description": "Transportation mode (default: 'walking')",
                            "default": "walking",
                        },
                        "alternatives": {
                            "type": "boolean",
                            "description": "Return alternative routes if available",
                            "default": False,
                        },
                    },
                    "required": ["origin", "destination"],
                },
            },
            {
                "name": "geocode_address",
                "description": "Convert an address to latitude and longitude coordinates. Useful for converting user-provided addresses to coordinates for other operations.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "address": {
                            "type": "string",
                            "description": "Address to geocode (e.g., '1600 Amphitheatre Parkway, Mountain View, CA')",
                        },
                    },
                    "required": ["address"],
                },
            },
            {
                "name": "reverse_geocode",
                "description": "Convert latitude and longitude coordinates to a human-readable address. Useful for describing the user's current location.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "lat": {
                            "type": "number",
                            "description": "Latitude coordinate",
                        },
                        "lng": {
                            "type": "number",
                            "description": "Longitude coordinate",
                        },
                    },
                    "required": ["lat", "lng"],
                },
            },
        ]
    }


@app.post("/tools/search_nearby_places")
async def search_nearby_places(request: SearchNearbyRequest) -> Dict[str, Any]:
    """
    Search for places near a location.

    Args:
        request: Search request with location, radius, and optional filters

    Returns:
        Dictionary containing list of nearby places with details

    Raises:
        HTTPException: If the search fails
    """
    try:
        gmaps = get_gmaps_client()

        # Geocode the location if it's an address
        if "," not in request.location.replace(" ", ""):
            # Likely an address, geocode it
            geocode_result = gmaps.geocode(request.location)
            if not geocode_result:
                raise HTTPException(
                    status_code=400, detail=f"Could not find location: {request.location}"
                )
            location = geocode_result[0]["geometry"]["location"]
            location_str = f"{location['lat']},{location['lng']}"
        else:
            # Already in lat,lng format
            location_str = request.location

        # Prepare search parameters
        search_params: Dict[str, Any] = {
            "location": location_str,
            "radius": min(request.radius, 50000),  # Max radius is 50000 meters
        }

        if request.type:
            search_params["type"] = request.type
        if request.keyword:
            search_params["keyword"] = request.keyword

        # Search nearby places
        places_result = gmaps.places_nearby(**search_params)

        # Format results for voice output
        results = []
        for place in places_result.get("results", [])[:5]:  # Limit to 5 results
            place_data = {
                "name": place.get("name", "Unknown"),
                "address": place.get("vicinity", place.get("formatted_address", "Address not available")),
                "rating": place.get("rating"),
                "rating_count": place.get("user_ratings_total", 0),
                "types": place.get("types", []),
            }

            # Calculate distance if location is available
            if "geometry" in place and "location" in place["geometry"]:
                place_loc = place["geometry"]["location"]
                # Simple distance calculation (could use more accurate method)
                place_data["location"] = f"{place_loc['lat']},{place_loc['lng']}"

            results.append(place_data)

        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Found {len(results)} nearby places",
                }
            ],
            "places": results,
            "count": len(results),
            "isError": False,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching places: {str(e)}")


@app.post("/tools/get_directions")
async def get_directions(request: GetDirectionsRequest) -> Dict[str, Any]:
    """
    Get walking directions between two points.

    Args:
        request: Directions request with origin, destination, and mode

    Returns:
        Dictionary containing step-by-step directions

    Raises:
        HTTPException: If directions cannot be found
    """
    try:
        gmaps = get_gmaps_client()

        # Validate mode
        valid_modes = ["walking", "driving", "transit", "bicycling"]
        if request.mode not in valid_modes:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid mode '{request.mode}'. Must be one of: {', '.join(valid_modes)}",
            )

        # Get directions
        directions_result = gmaps.directions(
            request.origin, request.destination, mode=request.mode, alternatives=request.alternatives
        )

        if not directions_result:
            raise HTTPException(
                status_code=404, detail="No directions found between the specified locations"
            )

        # Format for voice output
        routes = []
        for route in directions_result:
            leg = route["legs"][0]

            # Format steps for voice output
            steps = []
            for step in leg["steps"]:
                # Clean HTML from instructions
                instruction = step["html_instructions"]
                # Remove HTML tags
                import re

                instruction = re.sub(r"<[^>]+>", "", instruction)

                steps.append(
                    {
                        "instruction": instruction,
                        "distance": step["distance"]["text"],
                        "duration": step["duration"]["text"],
                    }
                )

            routes.append(
                {
                    "origin": leg["start_address"],
                    "destination": leg["end_address"],
                    "total_distance": leg["distance"]["text"],
                    "total_duration": leg["duration"]["text"],
                    "steps": steps,
                }
            )

        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Directions from {routes[0]['origin']} to {routes[0]['destination']}. Total distance: {routes[0]['total_distance']}, estimated time: {routes[0]['total_duration']}.",
                }
            ],
            "routes": routes,
            "isError": False,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting directions: {str(e)}")


@app.post("/tools/geocode_address")
async def geocode_address(request: GeocodeRequest) -> Dict[str, Any]:
    """
    Convert an address to coordinates.

    Args:
        request: Geocode request with address

    Returns:
        Dictionary containing coordinates and formatted address

    Raises:
        HTTPException: If geocoding fails
    """
    try:
        gmaps = get_gmaps_client()
        geocode_result = gmaps.geocode(request.address)

        if not geocode_result:
            raise HTTPException(status_code=404, detail=f"Could not geocode address: {request.address}")

        result = geocode_result[0]
        location = result["geometry"]["location"]
        formatted_address = result.get("formatted_address", request.address)

        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Address '{request.address}' is located at {formatted_address}",
                }
            ],
            "address": formatted_address,
            "latitude": location["lat"],
            "longitude": location["lng"],
            "location": f"{location['lat']},{location['lng']}",
            "isError": False,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error geocoding address: {str(e)}")


@app.post("/tools/reverse_geocode")
async def reverse_geocode(request: ReverseGeocodeRequest) -> Dict[str, Any]:
    """
    Convert coordinates to an address.

    Args:
        request: Reverse geocode request with lat/lng

    Returns:
        Dictionary containing formatted address

    Raises:
        HTTPException: If reverse geocoding fails
    """
    try:
        gmaps = get_gmaps_client()
        reverse_result = gmaps.reverse_geocode((request.lat, request.lng))

        if not reverse_result:
            raise HTTPException(
                status_code=404, detail=f"Could not reverse geocode coordinates: {request.lat}, {request.lng}"
            )

        result = reverse_result[0]
        formatted_address = result.get("formatted_address", "Address not available")

        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Coordinates {request.lat}, {request.lng} correspond to {formatted_address}",
                }
            ],
            "address": formatted_address,
            "latitude": request.lat,
            "longitude": request.lng,
            "isError": False,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reverse geocoding: {str(e)}")


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint.

    Returns:
        Health status
    """
    try:
        get_gmaps_client()
        return {"status": "healthy", "service": "google_maps_mcp"}
    except ValueError:
        return {"status": "unhealthy", "error": "Google Maps API key not configured"}


# MCP protocol endpoint for tool calls (alternative format)
@app.post("/tools/{tool_name}")
async def call_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Call an MCP tool by name.

    Args:
        tool_name: Name of the tool to call
        arguments: Tool arguments

    Returns:
        Tool call response

    Raises:
        HTTPException: If tool is not found or call fails
    """
    if tool_name == "search_nearby_places":
        request = SearchNearbyRequest(**arguments)
        return await search_nearby_places(request)
    elif tool_name == "get_directions":
        request = GetDirectionsRequest(**arguments)
        return await get_directions(request)
    elif tool_name == "geocode_address":
        request = GeocodeRequest(**arguments)
        return await geocode_address(request)
    elif tool_name == "reverse_geocode":
        request = ReverseGeocodeRequest(**arguments)
        return await reverse_geocode(request)
    else:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")

