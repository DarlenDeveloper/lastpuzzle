"""
AI Agent management API endpoints
Handles CRUD operations and agent management functionality
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from ....core.database import get_db
from .auth import get_current_user
from ....models.user import User
from ....schemas.agent import (
    AgentCreate, AgentUpdate, AgentResponse, AgentSummary,
    AgentTest, AgentTestResponse, AgentAnalytics, AgentAnalyticsResponse,
    AgentValidation, AgentTemplate, AgentClone, AgentDeployment
)
from ....services.agent_service import AgentService
from ....core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    agent_data: AgentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new AI agent
    
    Creates a new agent with the specified configuration. The agent will be created
    in INACTIVE status and needs to be deployed to become active.
    """
    try:
        agent_service = AgentService(db)
        agent = await agent_service.create_agent(str(current_user.id), agent_data)
        
        logger.info(f"Agent created successfully: {agent.id}")
        return AgentResponse.from_orm(agent)
        
    except ValueError as e:
        logger.warning(f"Invalid agent creation request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to create agent: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create agent"
        )


@router.get("/", response_model=List[AgentSummary])
async def get_agents(
    skip: int = Query(0, ge=0, description="Number of agents to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of agents to return"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user's agents
    
    Returns a paginated list of agents belonging to the current user.
    """
    try:
        agent_service = AgentService(db)
        agents = await agent_service.get_user_agents(str(current_user.id), skip, limit)
        
        return [AgentSummary.from_orm(agent) for agent in agents]
        
    except Exception as e:
        logger.error(f"Failed to get agents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve agents"
        )


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get agent details
    
    Returns detailed information about a specific agent.
    """
    try:
        agent_service = AgentService(db)
        agent = await agent_service.get_agent_by_id(str(current_user.id), agent_id)
        
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found"
            )
        
        return AgentResponse.from_orm(agent)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent {agent_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve agent"
        )


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: str,
    agent_data: AgentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update agent configuration
    
    Updates the configuration of an existing agent. Some changes may require
    redeployment to take effect.
    """
    try:
        agent_service = AgentService(db)
        agent = await agent_service.update_agent(str(current_user.id), agent_id, agent_data)
        
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found"
            )
        
        logger.info(f"Agent updated successfully: {agent_id}")
        return AgentResponse.from_orm(agent)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update agent {agent_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update agent"
        )


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete agent
    
    Soft deletes an agent by setting its status to ARCHIVED. The agent will
    no longer be available for conversations but historical data is preserved.
    """
    try:
        agent_service = AgentService(db)
        success = await agent_service.delete_agent(str(current_user.id), agent_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found"
            )
        
        logger.info(f"Agent deleted successfully: {agent_id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete agent {agent_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete agent"
        )


@router.post("/{agent_id}/deploy", response_model=dict)
async def deploy_agent(
    agent_id: str,
    deployment_config: AgentDeployment = AgentDeployment(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Deploy agent
    
    Activates an agent for production use. The agent configuration will be
    validated before deployment unless force_deploy is set to True.
    """
    try:
        agent_service = AgentService(db)
        
        # Validate configuration if requested
        if deployment_config.validate_config:
            agent = await agent_service.get_agent_by_id(str(current_user.id), agent_id)
            if not agent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Agent not found"
                )
            
            validation = await agent_service.validate_agent_config(agent)
            if not validation["valid"] and not deployment_config.force_deploy:
                return {
                    "success": False,
                    "message": "Agent configuration validation failed",
                    "validation": validation
                }
        
        # Deploy the agent
        success = await agent_service.deploy_agent(str(current_user.id), agent_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found or deployment failed"
            )
        
        logger.info(f"Agent deployed successfully: {agent_id}")
        return {
            "success": True,
            "message": "Agent deployed successfully",
            "agent_id": agent_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to deploy agent {agent_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deploy agent"
        )


@router.post("/{agent_id}/test", response_model=AgentTestResponse)
async def test_agent(
    agent_id: str,
    test_data: AgentTest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Test agent
    
    Tests an agent with sample input to verify its configuration and responses.
    This is useful for debugging and validating agent behavior before deployment.
    """
    try:
        agent_service = AgentService(db)
        result = await agent_service.test_agent(str(current_user.id), agent_id, test_data.input_text)
        
        if "error" in result:
            if result["error"] == "Agent not found":
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Agent not found"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=result["error"]
                )
        
        return AgentTestResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to test agent {agent_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to test agent"
        )


@router.post("/{agent_id}/clone", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def clone_agent(
    agent_id: str,
    clone_data: AgentClone,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Clone agent
    
    Creates a copy of an existing agent with a new name. All configuration
    settings are copied to the new agent.
    """
    try:
        agent_service = AgentService(db)
        cloned_agent = await agent_service.clone_agent(
            str(current_user.id), 
            agent_id, 
            clone_data.new_name
        )
        
        if not cloned_agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found"
            )
        
        logger.info(f"Agent cloned successfully: {agent_id} -> {cloned_agent.id}")
        return AgentResponse.from_orm(cloned_agent)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to clone agent {agent_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clone agent"
        )


@router.get("/{agent_id}/analytics", response_model=AgentAnalyticsResponse)
async def get_agent_analytics(
    agent_id: str,
    analytics_request: AgentAnalytics = Depends(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get agent analytics
    
    Returns performance metrics and usage analytics for the specified agent.
    """
    try:
        agent_service = AgentService(db)
        analytics = await agent_service.get_agent_analytics(
            str(current_user.id), 
            agent_id, 
            analytics_request.period
        )
        
        if "error" in analytics:
            if analytics["error"] == "Agent not found":
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Agent not found"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=analytics["error"]
                )
        
        return AgentAnalyticsResponse(**analytics)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get analytics for agent {agent_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve agent analytics"
        )


@router.get("/{agent_id}/validate", response_model=AgentValidation)
async def validate_agent_config(
    agent_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Validate agent configuration
    
    Validates the agent's configuration and returns any errors or warnings
    that would prevent successful deployment.
    """
    try:
        agent_service = AgentService(db)
        agent = await agent_service.get_agent_by_id(str(current_user.id), agent_id)
        
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found"
            )
        
        validation = await agent_service.validate_agent_config(agent)
        return AgentValidation(**validation)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to validate agent {agent_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate agent configuration"
        )


@router.get("/templates/", response_model=List[AgentTemplate])
async def get_agent_templates(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get agent templates
    
    Returns a list of predefined agent templates that can be used as starting
    points for creating new agents.
    """
    try:
        agent_service = AgentService(db)
        templates = await agent_service.get_agent_templates()
        
        return [AgentTemplate(**template) for template in templates]
        
    except Exception as e:
        logger.error(f"Failed to get agent templates: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve agent templates"
        )