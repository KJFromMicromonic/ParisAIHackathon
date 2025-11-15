"""FastAPI application for LiveKit agent backend."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.token import TokenRequest, TokenResponse, create_token
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    yield
    # Shutdown


app = FastAPI(
    title="LiveKit Agent Backend",
    description="Backend API for visually-impaired video voice assistant agent",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check() -> JSONResponse:
    """
    Health check endpoint.

    Returns:
        JSON response indicating service health
    """
    return JSONResponse(
        content={
            "status": "healthy",
            "service": "livekit-agent-backend",
        }
    )


@app.post("/api/token", response_model=TokenResponse)
async def generate_token(request: TokenRequest) -> TokenResponse:
    """
    Generate a LiveKit access token.

    Args:
        request: Token generation request

    Returns:
        Token response with JWT token
    """
    return await create_token(request)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=False,
    )

