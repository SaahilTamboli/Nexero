"""
Unreal Engine Integration API Endpoints.

This module provides HTTP endpoints for Unreal Engine VR client to send
session data and tracking events to the Nexero backend.

Integration Points:
1. Session Management - Start/end VR sessions
2. Tracking Events - Single event logging
3. Batch Processing - Efficient bulk event upload
4. Health Checks - Session status and heartbeat

Current Workflow:
- Sales person initiates session from dashboard
- Unreal Engine collects tracking data during VR tour
- After session ends, Unreal sends all data via batch endpoint
- Backend processes and stores for AI/ML analytics

Endpoints:
- POST /unreal/session - Receive session start/end data
- POST /unreal/tracking/event - Single event (legacy/fallback)
- POST /unreal/tracking/batch - Batch events (preferred)
- GET /unreal/session/{session_id}/status - Check session status
- POST /unreal/session/{session_id}/heartbeat - Keep session alive
"""

import logging
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, status

from app.models.unreal import (
    UnrealSessionData,
    TrackingEventFromUnreal,
    TrackingBatchFromUnreal
)
from app.services.session_service import SessionService
from app.services.tracking_service import TrackingService
from app.core.database import SupabaseDB

# Configure logging
logger = logging.getLogger(__name__)

# Create router for Unreal Engine endpoints
router = APIRouter(
    prefix="/unreal",
    tags=["Unreal Integration"]
)


# Dependency injection functions
def get_database() -> SupabaseDB:
    """
    Get database instance for dependency injection.
    
    Returns:
        SupabaseDB: Database connection instance
    """
    return SupabaseDB()


def get_session_service(db: SupabaseDB = Depends(get_database)) -> SessionService:
    """
    Get SessionService instance with database dependency.
    
    Args:
        db: Injected database instance
        
    Returns:
        SessionService: Session management service
    """
    return SessionService(db)


def get_tracking_service(db: SupabaseDB = Depends(get_database)) -> TrackingService:
    """
    Get TrackingService instance with database dependency.
    
    Args:
        db: Injected database instance
        
    Returns:
        TrackingService: Tracking event service
    """
    return TrackingService(db)


@router.post("/session", status_code=status.HTTP_201_CREATED)
async def receive_session_data(
    session_data: UnrealSessionData,
    session_service: SessionService = Depends(get_session_service)
):
    """
    Receive VR session start/end data from Unreal Engine.
    
    Legacy endpoint supporting test format where Unreal sends session
    data with Unix timestamp strings. Creates a complete session record
    with pre-determined start and end times.
    
    Request Body:
        - session_start: Unix timestamp string (e.g., "1727653800")
        - session_end: Unix timestamp string (e.g., "1727654100")
        - customer_id: Optional customer identifier
        - property_id: Optional property identifier
    
    Response:
        - status: "success"
        - message: Description
        - session_id: Generated UUID
        - duration_seconds: Calculated session duration
        - received_at: Current timestamp
        
    Raises:
        HTTPException 400: Invalid timestamp format
        HTTPException 500: Database or processing error
        
    Example Request:
        POST /unreal/session
        {
            "session_start": "1727653800",
            "session_end": "1727654100",
            "customer_id": "cust_12345",
            "property_id": "prop_67890"
        }
    """
    try:
        logger.info(
            f"Received session data from Unreal: "
            f"customer={session_data.customer_id}, "
            f"property={session_data.property_id}"
        )
        
        # Process session data through service layer
        session = await session_service.process_unreal_session_data(
            session_start=session_data.session_start,
            session_end=session_data.session_end,
            customer_id=session_data.customer_id,
            property_id=session_data.property_id
        )
        
        logger.info(
            f"Successfully processed session {session['id']}: "
            f"duration={session['duration_seconds']}s"
        )
        
        return {
            "status": "success",
            "message": "Session data received and processed",
            "session_id": session["id"],
            "duration_seconds": session["duration_seconds"],
            "received_at": datetime.now(timezone.utc).isoformat()
        }
        
    except ValueError as e:
        # Invalid timestamp format
        logger.error(f"Invalid timestamp format: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid timestamp format: {str(e)}"
        )
    except Exception as e:
        # Database or unexpected errors
        logger.error(f"Error processing session data: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process session data"
        )


@router.post("/tracking/event", status_code=status.HTTP_202_ACCEPTED)
async def receive_tracking_event(
    event: TrackingEventFromUnreal,
    tracking_service: TrackingService = Depends(get_tracking_service)
):
    """
    Receive single tracking event from Unreal Engine.
    
    Legacy/fallback endpoint for individual event submission.
    For better performance, use /tracking/batch endpoint instead.
    
    Request Body:
        - event_type: Event type (gaze, zone_enter, zone_exit, interaction)
        - timestamp: Unix timestamp with milliseconds
        - session_id: Session UUID (required)
        - Additional fields based on event type
    
    Response:
        - status: "received"
        - timestamp: Current server time
        
    Raises:
        HTTPException 400: Missing session_id or invalid data
        
    Example Request:
        POST /unreal/tracking/event
        {
            "event_type": "gaze",
            "timestamp": 1727653850.125,
            "session_id": "session_abc123",
            "zone_name": "kitchen",
            "gaze_target": "granite_countertop",
            "dwell_time_ms": 2500
        }
    """
    try:
        # Validate session_id is present
        if not event.session_id:
            logger.warning("Tracking event received without session_id")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="session_id is required"
            )
        
        logger.debug(
            f"Received tracking event: session={event.session_id}, "
            f"type={event.event_type}"
        )
        
        # Convert Pydantic model to dict and log event
        event_dict = event.model_dump()
        await tracking_service.log_event(
            session_id=event.session_id,
            event_data=event_dict
        )
        
        # Minimal response for speed
        return {
            "status": "received",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log error but return success (defensive - don't break VR client)
        logger.error(f"Error processing tracking event: {e}", exc_info=True)
        return {
            "status": "received",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


@router.post("/tracking/batch", status_code=status.HTTP_202_ACCEPTED)
async def receive_tracking_batch(
    batch: TrackingBatchFromUnreal,
    tracking_service: TrackingService = Depends(get_tracking_service)
):
    """
    Receive batch of tracking events from Unreal Engine (PREFERRED).
    
    Primary endpoint for current workflow. After VR session ends,
    Unreal sends all collected tracking events in a single batch
    for efficient processing.
    
    Benefits:
    - Reduces network overhead (single HTTP request)
    - Faster processing with bulk database operations
    - Better error tolerance
    
    Request Body:
        - session_id: Session UUID
        - events: List of tracking events
        - sent_at: Timestamp when batch was sent
    
    Response:
        - status: "received"
        - total_events: Total events in batch
        - processed: Successfully stored events
        - failed: Failed events (if any)
        - success_rate: Percentage of successful storage
        - timestamp: Current server time
        
    Example Request:
        POST /unreal/tracking/batch
        {
            "session_id": "session_abc123",
            "sent_at": 1727654100.500,
            "events": [
                {"event_type": "gaze", "timestamp": 1727653850.125, ...},
                {"event_type": "zone_enter", "timestamp": 1727653855.450, ...},
                {"event_type": "interaction", "timestamp": 1727653860.780, ...}
            ]
        }
    """
    try:
        logger.info(
            f"Received tracking batch: session={batch.session_id}, "
            f"events_count={len(batch.events)}"
        )
        
        # Convert Pydantic models to dicts
        events_list = [event.model_dump() for event in batch.events]
        
        # Process batch through tracking service
        result = await tracking_service.log_events_batch(
            session_id=batch.session_id,
            events=events_list
        )
        
        logger.info(
            f"Batch processed: {result['successful_count']}/{result['total_events']} "
            f"events stored ({result['success_rate']:.1f}% success)"
        )
        
        return {
            "status": "received",
            "total_events": result["total_events"],
            "processed": result["successful_count"],
            "failed": result["failed_count"],
            "success_rate": result["success_rate"],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        # Log error but return partial success (defensive)
        logger.error(f"Error processing tracking batch: {e}", exc_info=True)
        return {
            "status": "received",
            "total_events": len(batch.events),
            "processed": 0,
            "failed": len(batch.events),
            "success_rate": 0.0,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


@router.get("/session/{session_id}/status")
async def get_session_status(
    session_id: str,
    session_service: SessionService = Depends(get_session_service)
):
    """
    Check VR session status from Unreal Engine.
    
    Allows Unreal to verify session exists and check its current state.
    Useful for reconnection scenarios or multi-client coordination.
    
    Path Parameters:
        - session_id: UUID of the session
    
    Response:
        - session_id: Session UUID
        - status: "active" | "completed" | "not_found"
        - started_at: Session start timestamp
        - ended_at: Session end timestamp (if completed)
        - duration_seconds: Total duration (if completed)
        - duration_so_far: Current duration (if active)
        
    Example Request:
        GET /unreal/session/session_abc123/status
    """
    try:
        logger.debug(f"Status check requested for session {session_id}")
        
        # Fetch session from database
        session = await session_service.get_session(session_id)
        
        if not session:
            logger.warning(f"Session not found: {session_id}")
            return {
                "session_id": session_id,
                "status": "not_found",
                "started_at": None,
                "duration_so_far": None
            }
        
        # Calculate duration for active sessions
        duration_so_far = None
        if session["status"] == "active":
            started_at = datetime.fromisoformat(
                session["started_at"].replace("Z", "+00:00")
            )
            current_time = datetime.now(timezone.utc)
            duration_delta = current_time - started_at
            duration_so_far = int(duration_delta.total_seconds())
        
        response = {
            "session_id": session["id"],
            "status": session["status"],
            "started_at": session["started_at"],
            "duration_so_far": duration_so_far
        }
        
        # Add completion data if available
        if session.get("ended_at"):
            response["ended_at"] = session["ended_at"]
            response["duration_seconds"] = session.get("duration_seconds")
        
        return response
        
    except Exception as e:
        logger.error(f"Error checking session status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve session status"
        )


@router.post("/session/{session_id}/heartbeat")
async def session_heartbeat(
    session_id: str,
    session_service: SessionService = Depends(get_session_service)
):
    """
    Keep session alive with heartbeat ping.
    
    Optional endpoint for Unreal to signal the session is still active.
    Can be used to update last_activity timestamp or detect disconnections.
    
    Future Enhancement:
    - Track last_activity timestamp
    - Auto-end sessions after timeout period
    - Monitor connection health
    
    Path Parameters:
        - session_id: UUID of the session
    
    Response:
        - status: "alive"
        - session_id: Session UUID
        - timestamp: Current server time
        
    Example Request:
        POST /unreal/session/session_abc123/heartbeat
    """
    try:
        logger.debug(f"Heartbeat received for session {session_id}")
        
        # Verify session exists
        session = await session_service.get_session(session_id)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session not found: {session_id}"
            )
        
        # Future: Update last_activity timestamp
        # await session_service.update_session(
        #     session_id,
        #     {"last_activity": datetime.now(timezone.utc)}
        # )
        
        return {
            "status": "alive",
            "session_id": session_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing heartbeat: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process heartbeat"
        )
