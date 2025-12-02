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
from fastapi import APIRouter, HTTPException, Depends, status, Request

from app.models.unreal import (
    UnrealSessionData,
    TrackingEventFromUnreal,
    TrackingBatchFromUnreal,
    FlexibleEventData
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
    request: Request,
    session_service: SessionService = Depends(get_session_service),
    db: SupabaseDB = Depends(get_database)
):
    """
    Universal endpoint that accepts ANY data from Unreal Engine.
    
    Automatically detects the data type and routes appropriately:
    - Session data (has session_start/session_end) → stored in vr_sessions
    - POI data (has POI, Parent, POI_Duration) → stored in simple_events
    - View data (has View, TotalDuration) → stored in simple_events
    - Any other data → stored in simple_events as generic event
    
    This allows Unreal to send all data to one endpoint without changing URLs.
    """
    try:
        # Get raw JSON body
        raw_data = await request.json()
        
        # Log the RAW data received
        logger.info("="*70)
        logger.info("📥 INCOMING DATA FROM UNREAL (universal endpoint):")
        logger.info(f"  Raw data: {raw_data}")
        logger.info("="*70)
        
        # Detect data type and route accordingly
        
        # === SESSION DATA (has session_start and session_end) ===
        if "session_start" in raw_data and "session_end" in raw_data:
            logger.info("📊 Detected: SESSION DATA")
            
            # Process session data through service layer
            session = await session_service.process_unreal_session_data(
                session_start=raw_data.get("session_start"),
                session_end=raw_data.get("session_end"),
                customer_id=raw_data.get("customer_id"),
                property_id=raw_data.get("property_id")
            )
            
            logger.info(f"Successfully processed session {session['id']}: duration={session['duration_seconds']}s")
            
            return {
                "status": "success",
                "data_type": "session",
                "message": "Session data received and processed",
                "session_id": session["id"],
                "duration_seconds": session["duration_seconds"],
                "received_at": datetime.now(timezone.utc).isoformat()
            }
        
        # === POI DATA (has POI, Parent, POI_Duration) ===
        elif "POI" in raw_data or "Parent" in raw_data or "POI_Duration" in raw_data:
            logger.info("📍 Detected: POI DATA")
            
            event_record = {
                "event_type": "POI_Visit",
                "received_at": datetime.now(timezone.utc).isoformat(),
                "data": raw_data
            }
            
            try:
                db.client.table("simple_events").insert(event_record).execute()
                logger.info(f"Stored POI event: {raw_data}")
            except Exception as db_error:
                logger.warning(f"Could not store POI in DB: {db_error}")
            
            return {
                "status": "success",
                "data_type": "poi",
                "message": "POI data received",
                "received_at": datetime.now(timezone.utc).isoformat()
            }
        
        # === VIEW DATA (has View, TotalDuration) ===
        elif "View" in raw_data or "TotalDuration" in raw_data:
            logger.info("👁️ Detected: VIEW DATA")
            
            event_record = {
                "event_type": "View_Change",
                "received_at": datetime.now(timezone.utc).isoformat(),
                "data": raw_data
            }
            
            try:
                db.client.table("simple_events").insert(event_record).execute()
                logger.info(f"Stored View event: {raw_data}")
            except Exception as db_error:
                logger.warning(f"Could not store View in DB: {db_error}")
            
            return {
                "status": "success",
                "data_type": "view",
                "message": "View data received",
                "received_at": datetime.now(timezone.utc).isoformat()
            }
        
        # === GENERIC EVENT (anything else) ===
        else:
            logger.info("📦 Detected: GENERIC EVENT")
            
            event_record = {
                "event_type": raw_data.get("event_type", "unknown"),
                "received_at": datetime.now(timezone.utc).isoformat(),
                "data": raw_data
            }
            
            try:
                db.client.table("simple_events").insert(event_record).execute()
                logger.info(f"Stored generic event: {raw_data}")
            except Exception as db_error:
                logger.warning(f"Could not store event in DB: {db_error}")
            
            return {
                "status": "success",
                "data_type": "event",
                "message": "Event data received",
                "received_at": datetime.now(timezone.utc).isoformat()
            }
        
    except ValueError as e:
        logger.error(f"Invalid data format: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid data format: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error processing data: {e}", exc_info=True)
        # Return success anyway - don't break VR client
        return {
            "status": "received",
            "message": "Data received (with warnings)",
            "received_at": datetime.now(timezone.utc).isoformat()
        }


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
        # Log the RAW event data received
        logger.info("="*70)
        logger.info("📥 INCOMING TRACKING EVENT FROM CLIENT:")
        logger.info(f"  event_type: {event.event_type}")
        logger.info(f"  timestamp: {event.timestamp} (type: {type(event.timestamp).__name__})")
        logger.info(f"  session_id: {event.session_id}")
        logger.info(f"  event_data: {event.event_data}")
        logger.info("="*70)
        
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
        # Log the RAW batch data received
        logger.info("="*70)
        logger.info("📥 INCOMING TRACKING BATCH FROM CLIENT:")
        logger.info(f"  session_id: {batch.session_id}")
        logger.info(f"  sent_at: {batch.sent_at} (type: {type(batch.sent_at).__name__})")
        logger.info(f"  events_count: {len(batch.events)}")
        logger.info(f"  First 3 events preview:")
        for i, event in enumerate(batch.events[:3], 1):
            logger.info(f"    Event {i}: type={event.event_type}, timestamp={event.timestamp}")
        logger.info("="*70)
        
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


@router.post("/event", status_code=status.HTTP_201_CREATED)
async def receive_flexible_event(
    event: FlexibleEventData,
    db: SupabaseDB = Depends(get_database)
):
    """
    Receive any event type from Unreal Engine (FLEXIBLE ENDPOINT).
    
    This is the most flexible endpoint - it accepts ANY event with at minimum
    an event_type field. Perfect for UI events, navigation clicks, custom
    interactions, or any new event types you add to Unreal without needing
    backend changes.
    
    All fields except event_type are optional and will be stored in a JSONB
    metadata column for flexible querying later.
    
    Request Body:
        - event_type: Required - Event type (e.g., "NavBar_Click", "Menu_Open")
        - timestamp: Optional - Unix timestamp (string, int, or float)
        - session_id: Optional - Session identifier
        - Any other fields you want to track
    
    Response:
        - status: "received"
        - event_type: The event type that was received
        - timestamp: Server timestamp when event was processed
        
    Example NavBar Click:
        POST /unreal/event
        {
            "event_type": "NavBar_Click",
            "Menu_Item": "Amenities",
            "timestamp": "1764540726"
        }
        
    Example Custom Event:
        POST /unreal/event
        {
            "event_type": "Floor_Selected",
            "floor_number": 3,
            "building_id": "tower_a",
            "session_id": "session_abc123"
        }
    """
    try:
        # Log the raw event data
        logger.info("="*70)
        logger.info("📥 INCOMING FLEXIBLE EVENT FROM CLIENT:")
        logger.info(f"  event_type: {event.event_type}")
        logger.info(f"  timestamp: {event.timestamp}")
        logger.info(f"  session_id: {event.session_id}")
        
        # Get all extra fields that were passed
        extra_fields = event.model_extra or {}
        if extra_fields:
            logger.info(f"  extra_fields: {extra_fields}")
        logger.info("="*70)
        
        # Build event record for database
        event_record = {
            "event_type": event.event_type,
            "session_id": event.session_id,
            "received_at": datetime.now(timezone.utc).isoformat(),
            # Store all data including extras as JSONB
            "data": {
                "timestamp": str(event.timestamp) if event.timestamp else None,
                **extra_fields
            }
        }
        
        # Insert into simple_events table
        try:
            db.client.table("simple_events").insert(event_record).execute()
            logger.info(f"Stored flexible event: {event.event_type}")
        except Exception as db_error:
            # Log but don't fail - defensive for VR client stability
            logger.warning(f"Could not store event in DB (table may not exist): {db_error}")
        
        return {
            "status": "received",
            "event_type": event.event_type,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error processing flexible event: {e}", exc_info=True)
        # Return success anyway - don't break VR client
        return {
            "status": "received",
            "event_type": event.event_type if hasattr(event, 'event_type') else "unknown",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
