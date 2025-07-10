"""
Usage tracking and billing API endpoints
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def get_usage():
    """Get user usage statistics"""
    return {"message": "Usage endpoint - to be implemented"}


@router.get("/credits")
async def get_credits():
    """Get user credit balance"""
    return {"message": "Credits endpoint - to be implemented"}