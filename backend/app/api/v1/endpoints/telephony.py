"""
Telephony API endpoints for SIP trunk management
Handles CRUD operations for SIP trunks and call management
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime, timedelta

from ....core.database import get_db
from ....core.security import get_current_user
from ....models.user import User
from ....models.sip_trunk import CallDirection
from ....schemas.sip_trunk import (
    SipTrunkCreate, SipTrunkUpdate, SipTrunkResponse, SipTrunkList,
    CallLogCreate, CallLogUpdate, CallLogResponse, CallLogList,
    SipTrunkStats, SipTrunkDashboard, SipTrunkHealthCheck,
    WebRTCOffer, WebRTCAnswer, ICECandidate
)
from ....services.sip_trunk_service import SipTrunkService

router = APIRouter()
security = HTTPBearer()


@router.post("/trunks", response_model=SipTrunkResponse, status_code=status.HTTP_201_CREATED)
async def create_sip_trunk(
    trunk_data: SipTrunkCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new SIP trunk for the authenticated user.
    
    This endpoint allows users to configure a new SIP trunk connection
    with their telephony provider (Twilio, Telnyx, or custom SIP).
    """
    try:
        service = SipTrunkService(db)
        trunk = await service.create_sip_trunk(str(current_user.id), trunk_data)
        return trunk
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create SIP trunk"
        )


@router.get("/trunks", response_model=List[SipTrunkResponse])
async def get_sip_trunks(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all SIP trunks for the authenticated user.
    
    Returns a paginated list of SIP trunks with their current status,
    health information, and utilization metrics.
    """
    try:
        service = SipTrunkService(db)
        trunks = await service.get_user_trunks(str(current_user.id), skip, limit)
        return trunks
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve SIP trunks"
        )


@router.get("/trunks/{trunk_id}", response_model=SipTrunkResponse)
async def get_sip_trunk(
    trunk_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific SIP trunk by ID.
    
    Returns detailed information about a single SIP trunk including
    configuration, status, and performance metrics.
    """
    try:
        service = SipTrunkService(db)
        trunk = await service.get_trunk_by_id(str(current_user.id), trunk_id)
        
        if not trunk:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="SIP trunk not found"
            )
        
        return trunk
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve SIP trunk"
        )


@router.put("/trunks/{trunk_id}", response_model=SipTrunkResponse)
async def update_sip_trunk(
    trunk_id: str,
    update_data: SipTrunkUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a SIP trunk configuration.
    
    Allows modification of trunk settings including credentials,
    routing configuration, and capacity limits.
    """
    try:
        service = SipTrunkService(db)
        trunk = await service.update_sip_trunk(str(current_user.id), trunk_id, update_data)
        
        if not trunk:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="SIP trunk not found"
            )
        
        return trunk
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update SIP trunk"
        )


@router.delete("/trunks/{trunk_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sip_trunk(
    trunk_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a SIP trunk.
    
    Performs a soft delete of the trunk and cleans up any
    provider-specific configurations.
    """
    try:
        service = SipTrunkService(db)
        success = await service.delete_sip_trunk(str(current_user.id), trunk_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="SIP trunk not found"
            )
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete SIP trunk"
        )


@router.post("/trunks/{trunk_id}/health-check", response_model=SipTrunkHealthCheck)
async def perform_trunk_health_check(
    trunk_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Perform a health check on a specific SIP trunk.
    
    Tests connectivity, latency, and provider-specific health metrics.
    """
    try:
        service = SipTrunkService(db)
        trunk = await service.get_trunk_by_id(str(current_user.id), trunk_id)
        
        if not trunk:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="SIP trunk not found"
            )
        
        # Perform health check in background
        health_results = await service.perform_health_checks(str(current_user.id))
        trunk_health = health_results.get(trunk_id)
        
        if not trunk_health:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Health check failed"
            )
        
        return SipTrunkHealthCheck(
            trunk_id=trunk_id,
            status=trunk_health.get("status", "unknown"),
            latency_ms=trunk_health.get("latency_ms"),
            packet_loss_percent=trunk_health.get("packet_loss_percent"),
            timestamp=trunk_health.get("timestamp", datetime.utcnow()),
            details=trunk_health.get("details")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform health check"
        )


@router.get("/trunks/{trunk_id}/stats", response_model=SipTrunkStats)
async def get_trunk_statistics(
    trunk_id: str,
    start_date: Optional[datetime] = Query(None, description="Start date for statistics"),
    end_date: Optional[datetime] = Query(None, description="End date for statistics"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get statistics for a specific SIP trunk.
    
    Returns call volume, duration, costs, and performance metrics
    for the specified time period.
    """
    try:
        service = SipTrunkService(db)
        stats = await service.get_trunk_stats(
            str(current_user.id), 
            trunk_id, 
            start_date, 
            end_date
        )
        return stats
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve trunk statistics"
        )


@router.get("/dashboard", response_model=SipTrunkDashboard)
async def get_telephony_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get telephony dashboard with overview of all trunks and recent activity.
    
    Provides a comprehensive view of trunk status, utilization,
    and recent call activity.
    """
    try:
        service = SipTrunkService(db)
        
        # Get all trunks
        trunks = await service.get_user_trunks(str(current_user.id), 0, 100)
        
        # Calculate dashboard metrics
        total_trunks = len(trunks)
        active_trunks = len([t for t in trunks if t.is_active])
        total_active_calls = sum(t.current_active_calls for t in trunks)
        total_capacity = sum(t.max_concurrent_calls for t in trunks)
        overall_utilization = (total_active_calls / total_capacity * 100) if total_capacity > 0 else 0
        
        # Get recent calls
        recent_calls = await service.get_call_logs(str(current_user.id), None, 0, 10)
        
        # Get trunk stats
        trunk_stats = []
        for trunk in trunks[:10]:  # Limit to first 10 trunks
            try:
                stats = await service.get_trunk_stats(str(current_user.id), trunk.id)
                trunk_stats.append(stats)
            except:
                continue  # Skip if stats fail
        
        return SipTrunkDashboard(
            total_trunks=total_trunks,
            active_trunks=active_trunks,
            total_active_calls=total_active_calls,
            total_capacity=total_capacity,
            overall_utilization_percent=overall_utilization,
            trunk_stats=trunk_stats,
            recent_calls=recent_calls,
            call_stats={
                "total_calls": len(recent_calls),
                "answered_calls": len([c for c in recent_calls if c.was_answered]),
                "failed_calls": len([c for c in recent_calls if c.status == "failed"]),
                "total_duration_minutes": sum(c.duration_seconds or 0 for c in recent_calls) / 60,
                "total_cost": sum(c.cost for c in recent_calls),
                "average_duration_seconds": sum(c.duration_seconds or 0 for c in recent_calls) / len(recent_calls) if recent_calls else 0,
                "answer_rate_percent": len([c for c in recent_calls if c.was_answered]) / len(recent_calls) * 100 if recent_calls else 0,
                "quality_score_average": None
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dashboard data"
        )


# Call Log endpoints
@router.post("/calls", response_model=CallLogResponse, status_code=status.HTTP_201_CREATED)
async def create_call_log(
    call_data: CallLogCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new call log entry.
    
    Used by the system to track call initiation and details.
    """
    try:
        service = SipTrunkService(db)
        call_log = await service.log_call(call_data)
        return call_log
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create call log"
        )


@router.get("/calls", response_model=List[CallLogResponse])
async def get_call_logs(
    trunk_id: Optional[str] = Query(None, description="Filter by SIP trunk ID"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get call logs for the authenticated user.
    
    Returns a paginated list of call logs with optional filtering by trunk.
    """
    try:
        service = SipTrunkService(db)
        call_logs = await service.get_call_logs(
            str(current_user.id), 
            trunk_id, 
            skip, 
            limit
        )
        return call_logs
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve call logs"
        )


@router.put("/calls/{call_id}", response_model=CallLogResponse)
async def update_call_log(
    call_id: str,
    update_data: CallLogUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a call log entry.
    
    Used to update call status, duration, and other metrics
    as the call progresses.
    """
    try:
        service = SipTrunkService(db)
        call_log = await service.update_call_log(call_id, update_data)
        
        if not call_log:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Call log not found"
            )
        
        return call_log
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update call log"
        )


# WebRTC endpoints for real-time communication
@router.post("/webrtc/offer", response_model=WebRTCAnswer)
async def handle_webrtc_offer(
    offer: WebRTCOffer,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Handle WebRTC offer for establishing real-time communication.
    
    Processes SDP offer and returns SDP answer for WebRTC connection.
    """
    try:
        # This would integrate with a WebRTC server/gateway
        # For now, return a placeholder response
        return WebRTCAnswer(
            sdp="v=0\r\no=- 0 0 IN IP4 127.0.0.1\r\ns=-\r\nt=0 0\r\n",
            type="answer"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process WebRTC offer"
        )


@router.post("/webrtc/ice-candidate")
async def handle_ice_candidate(
    candidate: ICECandidate,
    current_user: User = Depends(get_current_user)
):
    """
    Handle ICE candidate for WebRTC connection establishment.
    
    Processes ICE candidates for NAT traversal and connectivity.
    """
    try:
        # This would be handled by the WebRTC server
        return {"status": "received"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process ICE candidate"
        )


# Webhook endpoints for provider callbacks
@router.post("/webhooks/twilio")
async def twilio_webhook(
    # Twilio webhook parameters would be defined here
    db: AsyncSession = Depends(get_db)
):
    """
    Handle Twilio webhook callbacks for call events.
    
    Processes call status updates, recordings, and other events from Twilio.
    """
    try:
        # Process Twilio webhook data
        # Update call logs, handle events, etc.
        return {"status": "received"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process Twilio webhook"
        )


@router.post("/webhooks/telnyx")
async def telnyx_webhook(
    # Telnyx webhook parameters would be defined here
    db: AsyncSession = Depends(get_db)
):
    """
    Handle Telnyx webhook callbacks for call events.
    
    Processes call status updates, media, and other events from Telnyx.
    """
    try:
        # Process Telnyx webhook data
        # Update call logs, handle events, etc.
        return {"status": "received"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process Telnyx webhook"
        )