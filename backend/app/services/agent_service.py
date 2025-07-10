"""
Agent service for AIRIES AI platform
Handles agent-related business logic and database operations
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_
from sqlalchemy.orm import selectinload
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import uuid
import json

from ..models.agent import Agent, AgentStatus, AgentType
from ..models.user import User
from ..schemas.agent import AgentCreate, AgentUpdate, AgentResponse, AgentTest, AgentAnalyticsResponse
from ..core.logging import get_logger
from ..core.config import settings
from .account_service import ensure_user_has_account_id, log_account_activity, AccountContextManager


class AgentService:
    """Service class for agent operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.logger = get_logger(__name__)
    
    async def create_agent(self, user_id: str, agent_data: AgentCreate) -> Agent:
        """Create a new AI agent"""
        try:
            # Get user and ensure account ID exists
            user = await self._get_user_by_id(user_id)
            if not user:
                raise ValueError("User not found")
            
            account_id = await ensure_user_has_account_id(self.db, user)
            
            # Create agent instance
            agent = Agent(
                user_id=uuid.UUID(user_id),
                account_id=account_id,
                name=agent_data.name,
                description=agent_data.description,
                agent_type=agent_data.agent_type,
                system_prompt=agent_data.system_prompt,
                welcome_message=agent_data.welcome_message,
                fallback_message=agent_data.fallback_message,
                max_conversation_length=agent_data.max_conversation_length or 50,
                
                # LLM Configuration
                llm_provider=agent_data.llm_provider or "groq",
                llm_model=agent_data.llm_model or "mixtral-8x7b-32768",
                temperature=agent_data.temperature or 0.7,
                max_tokens=agent_data.max_tokens or 1000,
                
                # Voice Configuration
                voice_provider=agent_data.voice_provider,
                voice_id=agent_data.voice_id,
                voice_settings=agent_data.voice_settings,
                
                # STT Configuration
                stt_provider=agent_data.stt_provider or "deepgram",
                stt_model=agent_data.stt_model or "nova-2",
                stt_language=agent_data.stt_language or "en",
                
                # Telephony Configuration
                phone_number=agent_data.phone_number,
                sip_endpoint=agent_data.sip_endpoint,
                telephony_provider=agent_data.telephony_provider,
                
                # Knowledge Base Configuration
                knowledge_base_id=agent_data.knowledge_base_id,
                rag_enabled=agent_data.rag_enabled or False,
                rag_similarity_threshold=agent_data.rag_similarity_threshold or 0.7,
                rag_max_results=agent_data.rag_max_results or 5,
                
                # Conversation Settings
                conversation_timeout=agent_data.conversation_timeout or 300,
                silence_timeout=agent_data.silence_timeout or 10,
                interrupt_enabled=agent_data.interrupt_enabled if agent_data.interrupt_enabled is not None else True,
                
                # Advanced Features
                tools_enabled=agent_data.tools_enabled or False,
                available_tools=agent_data.available_tools,
                webhook_url=agent_data.webhook_url,
                webhook_events=agent_data.webhook_events,
                
                # Scheduling and Availability
                is_available=agent_data.is_available if agent_data.is_available is not None else True,
                availability_schedule=agent_data.availability_schedule,
                timezone=agent_data.timezone or "UTC",
                
                # Additional metadata
                metadata=agent_data.metadata,
                
                # Set initial status
                status=AgentStatus.INACTIVE
            )
            
            # Add to database
            self.db.add(agent)
            await self.db.commit()
            await self.db.refresh(agent)
            
            # Log agent creation with account context
            async with AccountContextManager(account_id, user_id):
                self.logger.log_user_action(
                    action="create_agent",
                    resource="agent",
                    resource_id=str(agent.id),
                    extra_data={
                        'name': agent.name,
                        'type': agent.agent_type,
                        'llm_provider': agent.llm_provider,
                        'voice_enabled': agent.is_voice_enabled
                    }
                )
                
                await log_account_activity(
                    self.db,
                    account_id,
                    'agent_created',
                    'agent',
                    str(agent.id),
                    {
                        'name': agent.name,
                        'type': agent.agent_type,
                        'llm_provider': agent.llm_provider,
                        'llm_model': agent.llm_model
                    }
                )
            
            return agent
            
        except Exception as e:
            await self.db.rollback()
            self.logger.error(f"Failed to create agent: {str(e)}")
            raise
    
    async def get_user_agents(self, user_id: str, skip: int = 0, limit: int = 100) -> List[Agent]:
        """Get all agents for a user with pagination"""
        try:
            user_uuid = uuid.UUID(user_id)
            result = await self.db.execute(
                select(Agent)
                .where(Agent.user_id == user_uuid)
                .order_by(Agent.created_at.desc())
                .offset(skip)
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            self.logger.error(f"Failed to get user agents: {str(e)}")
            return []
    
    async def get_agent_by_id(self, user_id: str, agent_id: str) -> Optional[Agent]:
        """Get agent by ID, ensuring user ownership"""
        try:
            user_uuid = uuid.UUID(user_id)
            agent_uuid = uuid.UUID(agent_id)
            
            result = await self.db.execute(
                select(Agent)
                .where(
                    and_(
                        Agent.id == agent_uuid,
                        Agent.user_id == user_uuid
                    )
                )
            )
            return result.scalar_one_or_none()
        except Exception as e:
            self.logger.error(f"Failed to get agent by ID: {str(e)}")
            return None
    
    async def update_agent(self, user_id: str, agent_id: str, update_data: AgentUpdate) -> Optional[Agent]:
        """Update agent configuration"""
        try:
            agent = await self.get_agent_by_id(user_id, agent_id)
            if not agent:
                return None
            
            # Update fields
            update_dict = update_data.dict(exclude_unset=True)
            for field, value in update_dict.items():
                if hasattr(agent, field):
                    setattr(agent, field, value)
            
            agent.updated_at = datetime.utcnow()
            
            await self.db.commit()
            await self.db.refresh(agent)
            
            # Log agent update
            async with AccountContextManager(agent.account_id, user_id):
                self.logger.log_user_action(
                    action="update_agent",
                    resource="agent",
                    resource_id=str(agent.id),
                    extra_data={'updated_fields': list(update_dict.keys())}
                )
            
            return agent
            
        except Exception as e:
            await self.db.rollback()
            self.logger.error(f"Failed to update agent: {str(e)}")
            return None
    
    async def delete_agent(self, user_id: str, agent_id: str) -> bool:
        """Delete agent (soft delete by setting status to archived)"""
        try:
            agent = await self.get_agent_by_id(user_id, agent_id)
            if not agent:
                return False
            
            # Soft delete by archiving
            agent.status = AgentStatus.ARCHIVED
            agent.is_available = False
            agent.updated_at = datetime.utcnow()
            
            await self.db.commit()
            
            # Log agent deletion
            async with AccountContextManager(agent.account_id, user_id):
                self.logger.log_user_action(
                    action="delete_agent",
                    resource="agent",
                    resource_id=str(agent.id),
                    extra_data={'name': agent.name}
                )
            
            return True
            
        except Exception as e:
            await self.db.rollback()
            self.logger.error(f"Failed to delete agent: {str(e)}")
            return False
    
    async def deploy_agent(self, user_id: str, agent_id: str) -> bool:
        """Deploy agent (activate for production use)"""
        try:
            agent = await self.get_agent_by_id(user_id, agent_id)
            if not agent:
                return False
            
            # Validate agent configuration before deployment
            validation_result = await self.validate_agent_config(agent)
            if not validation_result["valid"]:
                self.logger.warning(f"Agent validation failed: {validation_result['errors']}")
                return False
            
            # Update agent status to active
            agent.status = AgentStatus.ACTIVE
            agent.is_available = True
            agent.updated_at = datetime.utcnow()
            
            await self.db.commit()
            
            # Log agent deployment
            async with AccountContextManager(agent.account_id, user_id):
                self.logger.log_user_action(
                    action="deploy_agent",
                    resource="agent",
                    resource_id=str(agent.id),
                    extra_data={'name': agent.name}
                )
                
                await log_account_activity(
                    self.db,
                    agent.account_id,
                    'agent_deployed',
                    'agent',
                    str(agent.id),
                    {'name': agent.name, 'type': agent.agent_type}
                )
            
            return True
            
        except Exception as e:
            await self.db.rollback()
            self.logger.error(f"Failed to deploy agent: {str(e)}")
            return False
    
    async def test_agent(self, user_id: str, agent_id: str, test_input: str) -> Dict[str, Any]:
        """Test agent with sample input (mock implementation for now)"""
        try:
            agent = await self.get_agent_by_id(user_id, agent_id)
            if not agent:
                return {"error": "Agent not found"}
            
            # Mock test response - in production this would integrate with LLM service
            test_response = {
                "success": True,
                "input": test_input,
                "output": f"Hello! I'm {agent.name}. You said: '{test_input}'. This is a test response.",
                "response_time_ms": 150,
                "tokens_used": 25,
                "model_used": agent.llm_model,
                "provider_used": agent.llm_provider,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Log test activity
            async with AccountContextManager(agent.account_id, user_id):
                self.logger.log_user_action(
                    action="test_agent",
                    resource="agent",
                    resource_id=str(agent.id),
                    extra_data={'test_input_length': len(test_input)}
                )
            
            return test_response
            
        except Exception as e:
            self.logger.error(f"Failed to test agent: {str(e)}")
            return {"error": str(e)}
    
    async def get_agent_analytics(self, user_id: str, agent_id: str, period: str = "7d") -> Dict[str, Any]:
        """Get agent analytics and performance metrics"""
        try:
            agent = await self.get_agent_by_id(user_id, agent_id)
            if not agent:
                return {"error": "Agent not found"}
            
            # Calculate period dates
            now = datetime.utcnow()
            if period == "24h":
                start_date = now - timedelta(hours=24)
            elif period == "7d":
                start_date = now - timedelta(days=7)
            elif period == "30d":
                start_date = now - timedelta(days=30)
            else:
                start_date = now - timedelta(days=7)
            
            # Mock analytics data - in production this would query conversation tables
            analytics = {
                "agent_id": str(agent.id),
                "agent_name": agent.name,
                "period": period,
                "start_date": start_date.isoformat(),
                "end_date": now.isoformat(),
                "metrics": {
                    "total_conversations": agent.total_conversations,
                    "total_minutes": agent.total_minutes,
                    "total_tokens": agent.total_tokens,
                    "average_rating": agent.average_rating,
                    "response_time_avg": agent.response_time_avg,
                    "success_rate": agent.success_rate,
                    "error_count": agent.error_count
                },
                "usage_by_day": [
                    {"date": (now - timedelta(days=i)).strftime("%Y-%m-%d"), "conversations": 0, "minutes": 0.0}
                    for i in range(7, 0, -1)
                ],
                "performance": {
                    "uptime_percentage": 99.5,
                    "avg_response_time": agent.response_time_avg or 200,
                    "error_rate": (agent.error_count / max(agent.total_conversations, 1)) * 100
                }
            }
            
            return analytics
            
        except Exception as e:
            self.logger.error(f"Failed to get agent analytics: {str(e)}")
            return {"error": str(e)}
    
    async def clone_agent(self, user_id: str, agent_id: str, new_name: str) -> Optional[Agent]:
        """Clone an existing agent with a new name"""
        try:
            original_agent = await self.get_agent_by_id(user_id, agent_id)
            if not original_agent:
                return None
            
            # Create agent data from original
            agent_data = AgentCreate(
                name=new_name,
                description=f"Clone of {original_agent.name}",
                agent_type=original_agent.agent_type,
                system_prompt=original_agent.system_prompt,
                welcome_message=original_agent.welcome_message,
                fallback_message=original_agent.fallback_message,
                max_conversation_length=original_agent.max_conversation_length,
                
                # Copy LLM configuration
                llm_provider=original_agent.llm_provider,
                llm_model=original_agent.llm_model,
                temperature=original_agent.temperature,
                max_tokens=original_agent.max_tokens,
                
                # Copy voice configuration
                voice_provider=original_agent.voice_provider,
                voice_id=original_agent.voice_id,
                voice_settings=original_agent.voice_settings,
                
                # Copy STT configuration
                stt_provider=original_agent.stt_provider,
                stt_model=original_agent.stt_model,
                stt_language=original_agent.stt_language,
                
                # Copy knowledge base configuration
                knowledge_base_id=original_agent.knowledge_base_id,
                rag_enabled=original_agent.rag_enabled,
                rag_similarity_threshold=original_agent.rag_similarity_threshold,
                rag_max_results=original_agent.rag_max_results,
                
                # Copy conversation settings
                conversation_timeout=original_agent.conversation_timeout,
                silence_timeout=original_agent.silence_timeout,
                interrupt_enabled=original_agent.interrupt_enabled,
                
                # Copy advanced features
                tools_enabled=original_agent.tools_enabled,
                available_tools=original_agent.available_tools,
                
                # Copy scheduling
                availability_schedule=original_agent.availability_schedule,
                timezone=original_agent.timezone
            )
            
            # Create the cloned agent
            cloned_agent = await self.create_agent(user_id, agent_data)
            
            # Log cloning activity
            async with AccountContextManager(cloned_agent.account_id, user_id):
                self.logger.log_user_action(
                    action="clone_agent",
                    resource="agent",
                    resource_id=str(cloned_agent.id),
                    extra_data={
                        'original_agent_id': str(original_agent.id),
                        'original_name': original_agent.name,
                        'new_name': new_name
                    }
                )
            
            return cloned_agent
            
        except Exception as e:
            self.logger.error(f"Failed to clone agent: {str(e)}")
            return None
    
    async def validate_agent_config(self, agent: Agent) -> Dict[str, Any]:
        """Validate agent configuration for deployment"""
        errors = []
        warnings = []
        
        # Basic validation
        if not agent.name or len(agent.name.strip()) < 2:
            errors.append("Agent name must be at least 2 characters long")
        
        if not agent.system_prompt or len(agent.system_prompt.strip()) < 10:
            errors.append("System prompt must be at least 10 characters long")
        
        # LLM validation
        if not agent.llm_provider:
            errors.append("LLM provider is required")
        
        if not agent.llm_model:
            errors.append("LLM model is required")
        
        if agent.temperature < 0 or agent.temperature > 2:
            errors.append("Temperature must be between 0 and 2")
        
        if agent.max_tokens < 1 or agent.max_tokens > 4000:
            errors.append("Max tokens must be between 1 and 4000")
        
        # Voice validation for voice-enabled agents
        if agent.is_voice_enabled:
            if not agent.voice_provider:
                warnings.append("Voice provider not configured for voice-enabled agent")
            
            if not agent.voice_id:
                warnings.append("Voice ID not configured for voice-enabled agent")
            
            if not agent.stt_provider:
                errors.append("STT provider is required for voice-enabled agents")
        
        # Phone number validation for telephony
        if agent.phone_number and not agent.telephony_provider:
            warnings.append("Phone number configured but no telephony provider set")
        
        # Knowledge base validation
        if agent.rag_enabled and not agent.knowledge_base_id:
            errors.append("Knowledge base ID is required when RAG is enabled")
        
        # Timeout validation
        if agent.conversation_timeout < 30 or agent.conversation_timeout > 3600:
            warnings.append("Conversation timeout should be between 30 seconds and 1 hour")
        
        if agent.silence_timeout < 3 or agent.silence_timeout > 60:
            warnings.append("Silence timeout should be between 3 and 60 seconds")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "agent_id": str(agent.id),
            "agent_name": agent.name
        }
    
    async def get_agent_templates(self) -> List[Dict[str, Any]]:
        """Get predefined agent templates"""
        templates = [
            {
                "id": "customer_support",
                "name": "Customer Support Agent",
                "description": "Friendly customer support agent for handling inquiries and issues",
                "agent_type": AgentType.HYBRID,
                "system_prompt": "You are a helpful customer support agent. Be friendly, professional, and solution-oriented. Always try to resolve customer issues efficiently.",
                "welcome_message": "Hello! I'm here to help you with any questions or issues you might have. How can I assist you today?",
                "fallback_message": "I apologize, but I didn't quite understand that. Could you please rephrase your question?",
                "llm_provider": "groq",
                "llm_model": "mixtral-8x7b-32768",
                "temperature": 0.7,
                "conversation_timeout": 600,
                "silence_timeout": 15
            },
            {
                "id": "sales_assistant",
                "name": "Sales Assistant",
                "description": "Persuasive sales agent for lead qualification and product demos",
                "agent_type": AgentType.VOICE,
                "system_prompt": "You are a professional sales assistant. Your goal is to understand customer needs, qualify leads, and guide them towards making a purchase decision. Be consultative, not pushy.",
                "welcome_message": "Hi there! I'm excited to learn about your needs and show you how our solution can help your business grow.",
                "fallback_message": "Let me make sure I understand your requirements correctly. Could you tell me more about what you're looking for?",
                "llm_provider": "openai",
                "llm_model": "gpt-4",
                "temperature": 0.8,
                "conversation_timeout": 900,
                "silence_timeout": 10
            },
            {
                "id": "appointment_scheduler",
                "name": "Appointment Scheduler",
                "description": "Efficient agent for booking and managing appointments",
                "agent_type": AgentType.VOICE,
                "system_prompt": "You are an appointment scheduling assistant. Help customers book, reschedule, or cancel appointments efficiently. Always confirm details and provide clear next steps.",
                "welcome_message": "Hello! I can help you schedule an appointment. What type of service are you looking to book?",
                "fallback_message": "I want to make sure I get your appointment details right. Could you please repeat that information?",
                "llm_provider": "groq",
                "llm_model": "llama2-70b-4096",
                "temperature": 0.5,
                "tools_enabled": True,
                "available_tools": ["calendar_integration", "sms_notifications"],
                "conversation_timeout": 300,
                "silence_timeout": 8
            },
            {
                "id": "technical_support",
                "name": "Technical Support Agent",
                "description": "Knowledgeable technical support agent for troubleshooting",
                "agent_type": AgentType.HYBRID,
                "system_prompt": "You are a technical support specialist. Help users troubleshoot technical issues step-by-step. Be patient, clear, and thorough in your explanations.",
                "welcome_message": "Hi! I'm here to help you resolve any technical issues you're experiencing. Can you describe the problem you're having?",
                "fallback_message": "Let me help you with that technical issue. Can you provide more details about what's happening?",
                "llm_provider": "deepinfra",
                "llm_model": "meta-llama/Llama-2-70b-chat-hf",
                "temperature": 0.3,
                "rag_enabled": True,
                "conversation_timeout": 1200,
                "silence_timeout": 20
            }
        ]
        
        return templates
    
    async def _get_user_by_id(self, user_id: str) -> Optional[User]:
        """Helper method to get user by ID"""
        try:
            user_uuid = uuid.UUID(user_id)
            result = await self.db.execute(
                select(User).where(User.id == user_uuid)
            )
            return result.scalar_one_or_none()
        except Exception:
            return None