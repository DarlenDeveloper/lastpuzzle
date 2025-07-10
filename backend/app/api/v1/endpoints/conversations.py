"""
Conversation management API endpoints
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def get_conversations():
    """Get user conversations"""
    return {"message": "Conversations endpoint - to be implemented"}


@router.post("/")
async def create_conversation():
    """Create new conversation"""
    return {"message": "Create conversation - to be implemented"}