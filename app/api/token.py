"""API endpoints for LiveKit token generation."""

from typing import Optional

from fastapi import HTTPException
from pydantic import BaseModel

from app.core.security import generate_access_token


class TokenRequest(BaseModel):
    """Request model for token generation."""

    room_name: str
    participant_identity: str
    participant_name: Optional[str] = None


class TokenResponse(BaseModel):
    """Response model for token generation."""

    token: str
    room_name: str
    participant_identity: str


async def create_token(request: TokenRequest) -> TokenResponse:
    """
    Generate a LiveKit access token.

    Args:
        request: Token generation request

    Returns:
        Token response with JWT token

    Raises:
        HTTPException: If token generation fails
    """
    try:
        token = generate_access_token(
            room_name=request.room_name,
            participant_identity=request.participant_identity,
            participant_name=request.participant_name,
        )

        return TokenResponse(
            token=token,
            room_name=request.room_name,
            participant_identity=request.participant_identity,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate token: {str(e)}")

