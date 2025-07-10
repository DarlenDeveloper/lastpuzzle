"""
SIP Trunk Service for AIRIES AI telephony platform
Handles SIP trunk management, health monitoring, and call routing
"""

import asyncio
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload

from ..models.sip_trunk import SipTrunk, CallLog, SipTrunkStatus, CallDirection
from ..models.user import User
from ..schemas.sip_trunk import (
    SipTrunkCreate, SipTrunkUpdate, SipTrunkResponse,
    CallLogCreate, CallLogUpdate, CallLogResponse,
    SipTrunkStats, CallLogStats
)
from ..core.config import settings
from .telephony_providers import TwilioProvider, TelnyxProvider

logger = logging.getLogger(__name__)


class SipTrunkService:
    """Service for managing SIP trunks and telephony operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.providers = {
            "twilio": TwilioProvider(),
            "telnyx": TelnyxProvider(),
        }
    
    async def create_sip_trunk(self, user_id: str, trunk_data: SipTrunkCreate) -> SipTrunkResponse:
        """Create a new SIP trunk"""
        try:
            # Validate user exists and has permissions
            user = await self._get_user(user_id)
            if not user:
                raise ValueError("User not found")
            
            # Check user's trunk limit based on tier
            current_trunks = await self._count_user_trunks(user_id)
            max_trunks = self._get_max_trunks_for_tier(user.tier)
            
            if current_trunks >= max_trunks:
                raise ValueError(f"Maximum number of trunks ({max_trunks}) reached for your tier")
            
            # Create SIP trunk
            trunk = SipTrunk(
                user_id=user_id,
                name=trunk_data.name,
                description=trunk_data.description,
                provider=trunk_data.provider,
                sip_domain=trunk_data.sip_domain,
                sip_username=trunk_data.sip_username,
                sip_password=trunk_data.sip_password,
                sip_proxy=trunk_data.sip_proxy,
                sip_port=trunk_data.sip_port,
                auth_username=trunk_data.auth_username,
                auth_password=trunk_data.auth_password,
                call_direction=trunk_data.call_direction,
                max_concurrent_calls=trunk_data.max_concurrent_calls,
                inbound_routing=trunk_data.inbound_routing,
                outbound_routing=trunk_data.outbound_routing,
                codec_preferences=trunk_data.codec_preferences,
                dtmf_mode=trunk_data.dtmf_mode,
                cost_per_minute=trunk_data.cost_per_minute,
                monthly_cost=trunk_data.monthly_cost,
                allowed_ips=trunk_data.allowed_ips,
                encryption_enabled=trunk_data.encryption_enabled,
                custom_headers=trunk_data.custom_headers,
                advanced_config=trunk_data.advanced_config,
                priority=trunk_data.priority
            )
            
            self.db.add(trunk)
            await self.db.commit()
            await self.db.refresh(trunk)
            
            # Initialize trunk with provider
            await self._initialize_trunk_with_provider(trunk)
            
            # Perform initial health check
            await self._perform_health_check(trunk)
            
            logger.info(f"Created SIP trunk {trunk.id} for user {user_id}")
            return await self._trunk_to_response(trunk)
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to create SIP trunk: {e}")
            raise
    
    async def get_user_trunks(self, user_id: str, skip: int = 0, limit: int = 100) -> List[SipTrunkResponse]:
        """Get all SIP trunks for a user"""
        query = select(SipTrunk).where(
            and_(SipTrunk.user_id == user_id, SipTrunk.deleted_at.is_(None))
        ).offset(skip).limit(limit).order_by(SipTrunk.priority, SipTrunk.created_at)
        
        result = await self.db.execute(query)
        trunks = result.scalars().all()
        
        return [await self._trunk_to_response(trunk) for trunk in trunks]
    
    async def get_trunk_by_id(self, user_id: str, trunk_id: str) -> Optional[SipTrunkResponse]:
        """Get a specific SIP trunk by ID"""
        query = select(SipTrunk).where(
            and_(
                SipTrunk.id == trunk_id,
                SipTrunk.user_id == user_id,
                SipTrunk.deleted_at.is_(None)
            )
        )
        
        result = await self.db.execute(query)
        trunk = result.scalar_one_or_none()
        
        if trunk:
            return await self._trunk_to_response(trunk)
        return None
    
    async def update_sip_trunk(self, user_id: str, trunk_id: str, update_data: SipTrunkUpdate) -> Optional[SipTrunkResponse]:
        """Update a SIP trunk"""
        try:
            trunk = await self._get_trunk(user_id, trunk_id)
            if not trunk:
                return None
            
            # Update fields
            update_dict = update_data.dict(exclude_unset=True)
            for field, value in update_dict.items():
                setattr(trunk, field, value)
            
            trunk.updated_at = datetime.utcnow()
            
            await self.db.commit()
            await self.db.refresh(trunk)
            
            # Re-initialize with provider if configuration changed
            if any(field in update_dict for field in ['sip_domain', 'sip_username', 'sip_password', 'provider']):
                await self._initialize_trunk_with_provider(trunk)
            
            logger.info(f"Updated SIP trunk {trunk_id}")
            return await self._trunk_to_response(trunk)
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to update SIP trunk {trunk_id}: {e}")
            raise
    
    async def delete_sip_trunk(self, user_id: str, trunk_id: str) -> bool:
        """Soft delete a SIP trunk"""
        try:
            trunk = await self._get_trunk(user_id, trunk_id)
            if not trunk:
                return False
            
            # Check if trunk has active calls
            if trunk.current_active_calls > 0:
                raise ValueError("Cannot delete trunk with active calls")
            
            trunk.deleted_at = datetime.utcnow()
            trunk.status = SipTrunkStatus.INACTIVE
            
            await self.db.commit()
            
            # Cleanup with provider
            await self._cleanup_trunk_with_provider(trunk)
            
            logger.info(f"Deleted SIP trunk {trunk_id}")
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to delete SIP trunk {trunk_id}: {e}")
            raise
    
    async def perform_health_checks(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Perform health checks on SIP trunks"""
        query = select(SipTrunk).where(SipTrunk.deleted_at.is_(None))
        
        if user_id:
            query = query.where(SipTrunk.user_id == user_id)
        
        result = await self.db.execute(query)
        trunks = result.scalars().all()
        
        health_results = {}
        
        for trunk in trunks:
            try:
                health_status = await self._perform_health_check(trunk)
                health_results[str(trunk.id)] = health_status
            except Exception as e:
                logger.error(f"Health check failed for trunk {trunk.id}: {e}")
                health_results[str(trunk.id)] = {
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.utcnow()
                }
        
        await self.db.commit()
        return health_results
    
    async def get_available_trunk_for_call(self, user_id: str, direction: CallDirection) -> Optional[SipTrunk]:
        """Get an available SIP trunk for making a call"""
        query = select(SipTrunk).where(
            and_(
                SipTrunk.user_id == user_id,
                SipTrunk.status == SipTrunkStatus.ACTIVE,
                SipTrunk.deleted_at.is_(None),
                or_(
                    SipTrunk.call_direction == CallDirection.BIDIRECTIONAL,
                    SipTrunk.call_direction == direction
                ),
                SipTrunk.current_active_calls < SipTrunk.max_concurrent_calls
            )
        ).order_by(SipTrunk.priority, SipTrunk.current_active_calls)
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def log_call(self, call_data: CallLogCreate) -> CallLogResponse:
        """Log a call"""
        try:
            # Get trunk to validate and get user_id
            trunk = await self._get_trunk_by_id(call_data.sip_trunk_id)
            if not trunk:
                raise ValueError("SIP trunk not found")
            
            call_log = CallLog(
                user_id=trunk.user_id,
                sip_trunk_id=call_data.sip_trunk_id,
                conversation_id=call_data.conversation_id,
                call_id=call_data.call_id,
                direction=call_data.direction,
                from_number=call_data.from_number,
                to_number=call_data.to_number,
                started_at=call_data.started_at,
                status=call_data.status,
                sip_call_id=call_data.sip_call_id,
                remote_ip=call_data.remote_ip,
                metadata=call_data.metadata
            )
            
            self.db.add(call_log)
            
            # Increment active calls on trunk
            trunk.increment_active_calls()
            
            await self.db.commit()
            await self.db.refresh(call_log)
            
            logger.info(f"Logged call {call_data.call_id}")
            return await self._call_log_to_response(call_log)
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to log call: {e}")
            raise
    
    async def update_call_log(self, call_id: str, update_data: CallLogUpdate) -> Optional[CallLogResponse]:
        """Update a call log"""
        try:
            query = select(CallLog).where(CallLog.call_id == call_id)
            result = await self.db.execute(query)
            call_log = result.scalar_one_or_none()
            
            if not call_log:
                return None
            
            # Update fields
            update_dict = update_data.dict(exclude_unset=True)
            for field, value in update_dict.items():
                setattr(call_log, field, value)
            
            # If call ended, decrement active calls on trunk
            if update_data.ended_at and not call_log.ended_at:
                trunk = await self._get_trunk_by_id(call_log.sip_trunk_id)
                if trunk:
                    trunk.decrement_active_calls()
            
            # Calculate duration and cost if call ended
            if call_log.ended_at and call_log.answered_at:
                call_log.calculate_duration()
                trunk = await self._get_trunk_by_id(call_log.sip_trunk_id)
                if trunk:
                    call_log.calculate_cost(trunk.cost_per_minute)
            
            await self.db.commit()
            await self.db.refresh(call_log)
            
            return await self._call_log_to_response(call_log)
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to update call log {call_id}: {e}")
            raise
    
    async def get_call_logs(self, user_id: str, trunk_id: Optional[str] = None, 
                           skip: int = 0, limit: int = 100) -> List[CallLogResponse]:
        """Get call logs for a user"""
        query = select(CallLog).where(CallLog.user_id == user_id)
        
        if trunk_id:
            query = query.where(CallLog.sip_trunk_id == trunk_id)
        
        query = query.offset(skip).limit(limit).order_by(CallLog.created_at.desc())
        
        result = await self.db.execute(query)
        call_logs = result.scalars().all()
        
        return [await self._call_log_to_response(call_log) for call_log in call_logs]
    
    async def get_trunk_stats(self, user_id: str, trunk_id: str, 
                             start_date: Optional[datetime] = None,
                             end_date: Optional[datetime] = None) -> SipTrunkStats:
        """Get statistics for a SIP trunk"""
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        trunk = await self._get_trunk(user_id, trunk_id)
        if not trunk:
            raise ValueError("SIP trunk not found")
        
        # Get call statistics
        call_stats_query = select(
            func.count(CallLog.id).label('total_calls'),
            func.sum(CallLog.duration_seconds).label('total_duration'),
            func.sum(CallLog.cost).label('total_cost'),
            func.avg(CallLog.duration_seconds).label('avg_duration'),
            func.count(CallLog.id).filter(CallLog.answered_at.isnot(None)).label('answered_calls')
        ).where(
            and_(
                CallLog.sip_trunk_id == trunk_id,
                CallLog.created_at >= start_date,
                CallLog.created_at <= end_date
            )
        )
        
        result = await self.db.execute(call_stats_query)
        stats = result.first()
        
        return SipTrunkStats(
            trunk_id=trunk_id,
            trunk_name=trunk.name,
            total_calls=stats.total_calls or 0,
            active_calls=trunk.current_active_calls,
            utilization_percent=trunk.utilization_percent,
            health_status=trunk.health_status,
            last_24h_calls=stats.total_calls or 0,  # Simplified for now
            last_24h_duration_minutes=(stats.total_duration or 0) / 60,
            last_24h_cost=stats.total_cost or 0,
            uptime_percent=95.0  # Placeholder - would calculate from health checks
        )
    
    # Private helper methods
    async def _get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        query = select(User).where(User.id == user_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def _get_trunk(self, user_id: str, trunk_id: str) -> Optional[SipTrunk]:
        """Get trunk by user and trunk ID"""
        query = select(SipTrunk).where(
            and_(
                SipTrunk.id == trunk_id,
                SipTrunk.user_id == user_id,
                SipTrunk.deleted_at.is_(None)
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def _get_trunk_by_id(self, trunk_id: str) -> Optional[SipTrunk]:
        """Get trunk by ID only"""
        query = select(SipTrunk).where(SipTrunk.id == trunk_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def _count_user_trunks(self, user_id: str) -> int:
        """Count active trunks for a user"""
        query = select(func.count(SipTrunk.id)).where(
            and_(SipTrunk.user_id == user_id, SipTrunk.deleted_at.is_(None))
        )
        result = await self.db.execute(query)
        return result.scalar() or 0
    
    def _get_max_trunks_for_tier(self, tier: str) -> int:
        """Get maximum trunks allowed for user tier"""
        limits = {
            "free": 1,
            "pro": 5,
            "enterprise": 50
        }
        return limits.get(tier, 1)
    
    async def _initialize_trunk_with_provider(self, trunk: SipTrunk) -> None:
        """Initialize trunk with telephony provider"""
        provider = self.providers.get(trunk.provider.value)
        if provider:
            try:
                await provider.initialize_trunk(trunk)
                trunk.status = SipTrunkStatus.ACTIVE
            except Exception as e:
                logger.error(f"Failed to initialize trunk with provider: {e}")
                trunk.status = SipTrunkStatus.ERROR
    
    async def _cleanup_trunk_with_provider(self, trunk: SipTrunk) -> None:
        """Cleanup trunk with telephony provider"""
        provider = self.providers.get(trunk.provider.value)
        if provider:
            try:
                await provider.cleanup_trunk(trunk)
            except Exception as e:
                logger.error(f"Failed to cleanup trunk with provider: {e}")
    
    async def _perform_health_check(self, trunk: SipTrunk) -> Dict[str, Any]:
        """Perform health check on a SIP trunk"""
        provider = self.providers.get(trunk.provider.value)
        if provider:
            try:
                health_result = await provider.health_check(trunk)
                trunk.update_health_status(
                    health_result.get("status", "unknown"),
                    health_result.get("latency_ms"),
                    health_result.get("packet_loss_percent")
                )
                return health_result
            except Exception as e:
                trunk.update_health_status("error")
                return {"status": "error", "error": str(e), "timestamp": datetime.utcnow()}
        
        trunk.update_health_status("unknown")
        return {"status": "unknown", "timestamp": datetime.utcnow()}
    
    async def _trunk_to_response(self, trunk: SipTrunk) -> SipTrunkResponse:
        """Convert SipTrunk model to response schema"""
        return SipTrunkResponse(
            id=str(trunk.id),
            user_id=str(trunk.user_id),
            name=trunk.name,
            description=trunk.description,
            provider=trunk.provider,
            status=trunk.status,
            sip_domain=trunk.sip_domain,
            sip_username=trunk.sip_username,
            sip_port=trunk.sip_port,
            call_direction=trunk.call_direction,
            max_concurrent_calls=trunk.max_concurrent_calls,
            current_active_calls=trunk.current_active_calls,
            last_health_check=trunk.last_health_check,
            health_status=trunk.health_status,
            latency_ms=trunk.latency_ms,
            packet_loss_percent=trunk.packet_loss_percent,
            cost_per_minute=trunk.cost_per_minute,
            monthly_cost=trunk.monthly_cost,
            encryption_enabled=trunk.encryption_enabled,
            created_at=trunk.created_at,
            updated_at=trunk.updated_at,
            utilization_percent=trunk.utilization_percent,
            is_active=trunk.is_active,
            can_handle_call=trunk.can_handle_call
        )
    
    async def _call_log_to_response(self, call_log: CallLog) -> CallLogResponse:
        """Convert CallLog model to response schema"""
        return CallLogResponse(
            id=str(call_log.id),
            user_id=str(call_log.user_id),
            sip_trunk_id=str(call_log.sip_trunk_id),
            conversation_id=str(call_log.conversation_id) if call_log.conversation_id else None,
            call_id=call_log.call_id,
            direction=call_log.direction,
            from_number=call_log.from_number,
            to_number=call_log.to_number,
            started_at=call_log.started_at,
            answered_at=call_log.answered_at,
            ended_at=call_log.ended_at,
            duration_seconds=call_log.duration_seconds,
            status=call_log.status,
            hangup_cause=call_log.hangup_cause,
            quality_score=call_log.quality_score,
            codec_used=call_log.codec_used,
            sip_call_id=call_log.sip_call_id,
            remote_ip=call_log.remote_ip,
            cost=call_log.cost,
            credits_used=call_log.credits_used,
            created_at=call_log.created_at,
            is_completed=call_log.is_completed,
            was_answered=call_log.was_answered
        )