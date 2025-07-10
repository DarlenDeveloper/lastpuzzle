"""
Main API router for v1 endpoints
Combines all API routes into a single router
"""

from fastapi import APIRouter

from .endpoints import auth, users, agents, conversations, usage, knowledge, telephony

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(conversations.router, prefix="/conversations", tags=["conversations"])
api_router.include_router(usage.router, prefix="/usage", tags=["usage"])
api_router.include_router(knowledge.router, prefix="/knowledge", tags=["knowledge"])
api_router.include_router(telephony.router, prefix="/telephony", tags=["telephony"])