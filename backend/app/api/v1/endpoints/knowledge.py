"""
Knowledge base management API endpoints
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def get_knowledge_bases():
    """Get user knowledge bases"""
    return {"message": "Knowledge endpoint - to be implemented"}


@router.post("/")
async def create_knowledge_base():
    """Create new knowledge base"""
    return {"message": "Create knowledge base - to be implemented"}