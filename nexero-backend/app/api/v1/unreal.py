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
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Depends, status, Request, Query

from app.models.unreal import (
    ViewModePayload,
    POIPayload,
    UnitSelectionPayload,
    SessionSummaryPayload,
    TrackingEventFromUnreal,
    TrackingBatchFromUnreal,
    FlexibleEventData
)
from app.services.session_service import SessionService
from app.services.tracking_service import TrackingService
from app.core.database import SupabaseDB

# Configure logging
logger = logging.getLogger(__name__)
_LAST_EVENT_TIMESTAMPS: Dict[str, datetime] = {}


def _safe_rows(response: Any) -> List[Dict[str, Any]]:
    """Return list-like Supabase response data safely."""
    if not response:
        return []
    data = getattr(response, "data", None)
    return data if isinstance(data, list) else []


def _safe_seconds(value: Optional[int]) -> int:
    """Normalize nullable duration integers."""
    return int(value or 0)


def _lead_tier(avg_duration_seconds: int, total_sessions: int) -> str:
    """Classify lead quality from engagement depth and repeat sessions."""
    if total_sessions >= 3 and avg_duration_seconds >= 300:
        return "hot"
    if total_sessions >= 2 or avg_duration_seconds >= 180:
        return "warm"
    return "cold"


def _zone_to_xy(zone_name: str) -> Dict[str, int]:
    """Generate deterministic pseudo coordinates for zone heatmap rendering."""
    seed = sum(ord(c) for c in zone_name)
    return {
        "x": (seed * 37) % 100,
        "y": (seed * 53) % 100,
    }


def _parse_duration_to_seconds(duration_str: str) -> int:
    """
    Parse duration string (M:SS format) to seconds.
    
    Examples:
        "0:45" → 45
        "1:30" → 90
        "2:00" → 120
        
    Args:
        duration_str: Duration in "M:SS" format
        
    Returns:
        int: Duration in seconds, 0 if parsing fails
    """
    try:
        if not duration_str:
            return 0
        
        parts = duration_str.split(':')
        if len(parts) == 2:
            minutes = int(parts[0])
            seconds = int(parts[1])
            return (minutes * 60) + seconds
        elif len(parts) == 1:
            return int(parts[0])
        else:
            return 0
    except (ValueError, TypeError):
        return 0


def _normalize_duration_for_storage(duration_str: Optional[str]) -> str:
    """Return a short duration string that fits the database column."""
    if not duration_str:
        return "0:00"

    duration_seconds = _parse_duration_to_seconds(duration_str)
    if duration_seconds <= 0:
        return "0:00"

    minutes, seconds = divmod(duration_seconds, 60)
    if minutes >= 60:
        hours, minutes = divmod(minutes, 60)
        return f"{hours}:{minutes:02d}:{seconds:02d}"

    return f"{minutes}:{seconds:02d}"


def _seconds_to_duration_string(total_seconds: int) -> str:
    """Format elapsed seconds as a short duration string."""
    if total_seconds <= 0:
        return "0:00"

    minutes, seconds = divmod(total_seconds, 60)
    if minutes >= 60:
        hours, minutes = divmod(minutes, 60)
        return f"{hours}:{minutes:02d}:{seconds:02d}"

    return f"{minutes}:{seconds:02d}"


def _parse_unreal_datetime(value: Optional[str]) -> Optional[datetime]:
    """Parse Unreal timestamp strings into timezone-aware datetimes."""
    if not value:
        return None

    text = str(value).strip()
    if not text:
        return None

    try:
        return datetime.fromtimestamp(float(text), tz=timezone.utc)
    except (ValueError, TypeError):
        pass

    formats = [
        "%d-%b-%Y, %I:%M:%S %p",
        "%d-%b-%Y, %I:%M:%S%p",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S%z",
    ]

    for fmt in formats:
        try:
            parsed = datetime.strptime(text, fmt)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed
        except ValueError:
            continue

    return None


def _elapsed_since_previous(key: str, current_value: Optional[str]) -> tuple[str, Optional[datetime]]:
    """Derive elapsed time from the previous timestamp for the same event stream."""
    current_timestamp = _parse_unreal_datetime(current_value)
    if current_timestamp is None:
        return _normalize_duration_for_storage(current_value), None

    previous_timestamp = _LAST_EVENT_TIMESTAMPS.get(key)
    _LAST_EVENT_TIMESTAMPS[key] = current_timestamp

    if previous_timestamp is None:
        return "0:00", current_timestamp

    delta_seconds = int((current_timestamp - previous_timestamp).total_seconds())
    return _seconds_to_duration_string(max(delta_seconds, 0)), current_timestamp


def _has_non_empty_value(payload: Dict[str, Any]) -> bool:
    """Return True when the payload contains at least one meaningful value."""
    return any(value not in (None, "") for value in payload.values())


def _request_stream_key(request: Request, stream_name: str) -> str:
    """Create a stable in-process key for a client event stream."""
    client_host = request.client.host if request.client else "unknown"
    return f"{client_host}:{stream_name}"


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
@router.post("/sessions", status_code=status.HTTP_201_CREATED)
async def receive_session_data(
    request: Request,
    session_service: SessionService = Depends(get_session_service),
    db: SupabaseDB = Depends(get_database)
):
    """
    Universal endpoint that accepts validated data from Unreal Engine.
    
    Automatically detects the data type and validates with Pydantic models:
    - Session data (has session_start/session_end) → validated with UnrealSessionData
    - POI data (has Parent, POI_Duration) → validated with POIData
    - View data (has View, TotalDuration) → validated with ViewData
    - Unknown data types → rejected with 400 error
    
    This is SAFE because all data is validated before storage.
    """
    try:
        # Get raw JSON body
        raw_data = await request.json()

        if not isinstance(raw_data, dict):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "Invalid payload",
                    "message": "Request body must be a JSON object",
                },
            )
        
        # Log the RAW data received
        logger.info("="*70)
        logger.info("📥 INCOMING DATA FROM UNREAL (universal endpoint):")
        logger.info(f"  Raw data: {raw_data}")
        logger.info("="*70)

        # Unreal sends an empty startup packet before the real events begin.
        if not raw_data or not _has_non_empty_value(raw_data):
            logger.info("Ignoring empty Unreal payload")
            return {"status": "ignored", "event_type": "empty_payload", "processed": False}
        
        if "ViewMode" in raw_data and "Duration" in raw_data:
            data = ViewModePayload(**raw_data)
            view_stream_key = _request_stream_key(request, "view_mode")
            normalized_duration, current_timestamp = _elapsed_since_previous(view_stream_key, data.Duration)
            duration_seconds = _parse_duration_to_seconds(normalized_duration)
            view_record = {
                "view_name": data.ViewMode,
                "duration_string": normalized_duration,
                "duration_seconds": duration_seconds,
                "event_time": current_timestamp.isoformat() if current_timestamp else None,
                "received_at": datetime.now(timezone.utc).isoformat()
            }
            try:
                db.client.table("view_events").insert(view_record).execute()
            except Exception as db_error:
                logger.warning(f"Could not store View in view_events: {db_error}")
            return {"status": "success", "event_type": "view_mode", "processed": True}

        elif "POI" in raw_data and "Castegory" in raw_data:
            data = POIPayload(**raw_data)
            poi_stream_key = _request_stream_key(request, "poi")
            normalized_poi_duration, current_timestamp = _elapsed_since_previous(poi_stream_key, raw_data.get("POI_Duration"))
            poi_record = {
                "poi_name": data.POI,
                "parent_zone": data.Castegory,
                "poi_source": data.Click_Source,
                "received_at": datetime.now(timezone.utc).isoformat(),
                "event_time": data.Datetime or (current_timestamp.isoformat() if current_timestamp else datetime.now(timezone.utc).isoformat()),
                "duration_string": normalized_poi_duration,
                "duration_seconds": _parse_duration_to_seconds(normalized_poi_duration),
            }
            try:
                db.client.table("poi_visits").insert(poi_record).execute()
            except Exception as db_error:
                logger.warning(f"Could not store POI in poi_visits: {db_error}")
            return {"status": "success", "event_type": "poi", "processed": True}

        elif "Name" in raw_data and "Sqft" in raw_data:
            data = UnitSelectionPayload(**raw_data)
            unit_record = {
                "unit_name": data.Name,
                "sqft": data.Sqft,
                "unit_type": data.Type,
                "received_at": datetime.now(timezone.utc).isoformat(),
                "event_time": data.Datetime or datetime.now(timezone.utc).isoformat()
            }
            try:
                # Store in a generic/unit tracking table
                db.client.table("simple_events").insert({
                    "event_type": "Unit_Selection",
                    "received_at": datetime.now(timezone.utc).isoformat(),
                    "data": unit_record
                }).execute()
            except Exception as db_error:
                logger.warning(f"Could not store Unit in metadata table: {db_error}")
            return {"status": "success", "event_type": "unit_selection", "processed": True}

        elif "session_id" in raw_data and "session_start" in raw_data:
            data = SessionSummaryPayload(**raw_data)
            # Process session data through service layer
            try:
                session = await session_service.process_unreal_session_data(
                    session_start=data.session_start,
                    session_end=data.session_end
                )
                return {"status": "success", "event_type": "session_summary", "processed": True, "session_id": session["id"]}
            except Exception as e:
                logger.warning(f"Could not process session: {e}")
                return {"status": "error", "event_type": "session_summary", "processed": False}

        else:
            logger.warning(f"❌ Unknown data type received: {list(raw_data.keys())}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "Unknown data type",
                    "message": "Payload did not match any known event footprint",
                    "received_keys": list(raw_data.keys())
                }
            )
        
    except HTTPException:
        # Re-raise HTTP exceptions (like our 400 above)
        raise
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid data format: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error processing data: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while processing data"
        )


@router.post("/tracking/event", status_code=status.HTTP_202_ACCEPTED)
@router.post("/events", status_code=status.HTTP_202_ACCEPTED)
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
@router.post("/batch", status_code=status.HTTP_202_ACCEPTED)
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
@router.post("/heartbeat/{session_id}")
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


@router.get("/leads")
async def get_leads(
    limit: int = Query(default=100, ge=1, le=1000),
    db: SupabaseDB = Depends(get_database)
):
    """Return customer-level lead rollups derived from session data."""
    try:
        sessions_res = (
            db.client.table("vr_sessions")
            .select("id, customer_id, property_id, duration_seconds, started_at")
            .order("started_at", desc=True)
            .limit(limit * 20)
            .execute()
        )
        sessions = _safe_rows(sessions_res)

        lead_map: Dict[str, Dict[str, Any]] = {}
        for session in sessions:
            customer_id = session.get("customer_id")
            if not customer_id:
                continue

            info = lead_map.setdefault(
                customer_id,
                {
                    "customer_id": customer_id,
                    "total_sessions": 0,
                    "total_engagement_seconds": 0,
                    "avg_session_duration": 0,
                    "last_seen": session.get("started_at"),
                    "top_property_id": None,
                    "_property_counts": {},
                }
            )

            info["total_sessions"] += 1
            info["total_engagement_seconds"] += _safe_seconds(session.get("duration_seconds"))

            started_at = session.get("started_at")
            if started_at and (not info["last_seen"] or started_at > info["last_seen"]):
                info["last_seen"] = started_at

            property_id = session.get("property_id")
            if property_id:
                property_counts = info["_property_counts"]
                property_counts[property_id] = property_counts.get(property_id, 0) + 1

        leads: List[Dict[str, Any]] = []
        for lead in lead_map.values():
            total_sessions = lead["total_sessions"]
            if total_sessions > 0:
                lead["avg_session_duration"] = int(
                    lead["total_engagement_seconds"] / total_sessions
                )

            if lead["_property_counts"]:
                lead["top_property_id"] = max(
                    lead["_property_counts"],
                    key=lead["_property_counts"].get
                )

            lead["engagement_tier"] = _lead_tier(
                avg_duration_seconds=lead["avg_session_duration"],
                total_sessions=lead["total_sessions"]
            )
            lead.pop("_property_counts", None)
            leads.append(lead)

        leads.sort(
            key=lambda item: (
                item.get("total_engagement_seconds", 0),
                item.get("total_sessions", 0),
            ),
            reverse=True,
        )
        leads = leads[:limit]

        return {
            "status": "success",
            "count": len(leads),
            "data": leads,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.error(f"Error retrieving leads: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve leads",
        )


@router.get("/leads/{customer_id}")
async def get_lead_details(
    customer_id: str,
    db: SupabaseDB = Depends(get_database)
):
    """Return detailed customer engagement using sessions + POI + view data."""
    try:
        sessions_res = (
            db.client.table("vr_sessions")
            .select("id, started_at, ended_at, duration_seconds, property_id")
            .eq("customer_id", customer_id)
            .order("started_at", desc=True)
            .execute()
        )
        sessions = _safe_rows(sessions_res)

        if not sessions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No sessions found for customer_id={customer_id}",
            )

        session_ids = [s["id"] for s in sessions if s.get("id")]

        poi_rows: List[Dict[str, Any]] = []
        view_rows: List[Dict[str, Any]] = []
        tracking_rows: List[Dict[str, Any]] = []
        if session_ids:
            poi_rows = _safe_rows(
                db.client.table("poi_visits")
                .select("poi_name, parent_zone, duration_seconds, session_id")
                .in_("session_id", session_ids)
                .execute()
            )
            view_rows = _safe_rows(
                db.client.table("view_events")
                .select("view_name, duration_seconds, session_id")
                .in_("session_id", session_ids)
                .execute()
            )
            tracking_rows = _safe_rows(
                db.client.table("tracking_events")
                .select("id, event_type, session_id")
                .in_("session_id", session_ids)
                .execute()
            )

        total_seconds = sum(_safe_seconds(s.get("duration_seconds")) for s in sessions)
        avg_seconds = int(total_seconds / len(sessions)) if sessions else 0

        return {
            "status": "success",
            "data": {
                "customer_id": customer_id,
                "total_sessions": len(sessions),
                "total_engagement_seconds": total_seconds,
                "avg_session_duration": avg_seconds,
                "engagement_tier": _lead_tier(avg_seconds, len(sessions)),
                "last_seen": sessions[0].get("started_at"),
                "sessions": sessions,
                "metrics": {
                    "poi_visits": len(poi_rows),
                    "view_events": len(view_rows),
                    "tracking_events": len(tracking_rows),
                },
            },
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving lead details for {customer_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve lead details",
        )


@router.get("/properties/{property_id}")
async def get_property_analytics(
    property_id: str,
    db: SupabaseDB = Depends(get_database)
):
    """Return aggregated analytics for one property."""
    try:
        sessions = _safe_rows(
            db.client.table("vr_sessions")
            .select("id, customer_id, duration_seconds, started_at")
            .eq("property_id", property_id)
            .order("started_at", desc=True)
            .execute()
        )

        session_ids = [s["id"] for s in sessions if s.get("id")]
        unique_customers = len({s.get("customer_id") for s in sessions if s.get("customer_id")})
        total_seconds = sum(_safe_seconds(s.get("duration_seconds")) for s in sessions)
        avg_seconds = int(total_seconds / len(sessions)) if sessions else 0

        poi_rows: List[Dict[str, Any]] = []
        view_rows: List[Dict[str, Any]] = []
        if session_ids:
            poi_rows = _safe_rows(
                db.client.table("poi_visits")
                .select("poi_name, parent_zone, duration_seconds")
                .in_("session_id", session_ids)
                .execute()
            )
            view_rows = _safe_rows(
                db.client.table("view_events")
                .select("view_name, duration_seconds")
                .in_("session_id", session_ids)
                .execute()
            )

        poi_map: Dict[str, int] = {}
        for row in poi_rows:
            name = row.get("poi_name") or row.get("parent_zone") or "unknown"
            poi_map[name] = poi_map.get(name, 0) + 1

        view_map: Dict[str, int] = {}
        for row in view_rows:
            name = row.get("view_name") or "unknown"
            view_map[name] = view_map.get(name, 0) + 1

        top_pois = sorted(poi_map.items(), key=lambda x: x[1], reverse=True)[:5]
        top_views = sorted(view_map.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "status": "success",
            "data": {
                "property_id": property_id,
                "total_sessions": len(sessions),
                "unique_customers": unique_customers,
                "total_engagement_seconds": total_seconds,
                "avg_session_duration": avg_seconds,
                "poi_visit_count": len(poi_rows),
                "view_event_count": len(view_rows),
                "top_pois": [{"name": name, "count": count} for name, count in top_pois],
                "top_views": [{"name": name, "count": count} for name, count in top_views],
            },
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.error(f"Error retrieving property analytics for {property_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve property analytics",
        )


@router.get("/zones/{property_id}")
async def get_zone_analytics(
    property_id: str,
    db: SupabaseDB = Depends(get_database)
):
    """Return zone-level engagement for a property based on POI visits."""
    try:
        sessions = _safe_rows(
            db.client.table("vr_sessions")
            .select("id")
            .eq("property_id", property_id)
            .execute()
        )
        session_ids = [s["id"] for s in sessions if s.get("id")]

        if not session_ids:
            return {
                "status": "success",
                "data": [],
                "count": 0,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }

        poi_rows = _safe_rows(
            db.client.table("poi_visits")
            .select("parent_zone, duration_seconds, session_id")
            .in_("session_id", session_ids)
            .execute()
        )

        zone_map: Dict[str, Dict[str, Any]] = {}
        for row in poi_rows:
            zone_name = row.get("parent_zone") or "unknown"
            zone = zone_map.setdefault(
                zone_name,
                {
                    "zone_name": zone_name,
                    "visit_count": 0,
                    "total_seconds": 0,
                    "session_ids": set(),
                },
            )
            zone["visit_count"] += 1
            zone["total_seconds"] += _safe_seconds(row.get("duration_seconds"))
            if row.get("session_id"):
                zone["session_ids"].add(row["session_id"])

        zone_data: List[Dict[str, Any]] = []
        for zone in zone_map.values():
            avg_seconds = int(zone["total_seconds"] / zone["visit_count"]) if zone["visit_count"] else 0
            zone_data.append(
                {
                    "zone_name": zone["zone_name"],
                    "visit_count": zone["visit_count"],
                    "total_seconds": zone["total_seconds"],
                    "avg_seconds": avg_seconds,
                    "unique_sessions": len(zone["session_ids"]),
                }
            )

        zone_data.sort(key=lambda item: item["visit_count"], reverse=True)

        return {
            "status": "success",
            "count": len(zone_data),
            "data": zone_data,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.error(f"Error retrieving zone analytics for {property_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve zone analytics",
        )


@router.get("/heatmap/{property_id}")
async def get_property_heatmap(
    property_id: str,
    db: SupabaseDB = Depends(get_database)
):
    """Return zone intensity heatmap data for a property."""
    try:
        sessions = _safe_rows(
            db.client.table("vr_sessions")
            .select("id")
            .eq("property_id", property_id)
            .execute()
        )
        session_ids = [s["id"] for s in sessions if s.get("id")]

        if not session_ids:
            return {
                "status": "success",
                "data": [],
                "count": 0,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }

        tracking_rows = _safe_rows(
            db.client.table("tracking_events")
            .select("zone_name, dwell_time_ms")
            .in_("session_id", session_ids)
            .execute()
        )

        if not tracking_rows:
            # Fallback to POI zones if detailed tracking is sparse
            poi_rows = _safe_rows(
                db.client.table("poi_visits")
                .select("parent_zone, duration_seconds")
                .in_("session_id", session_ids)
                .execute()
            )
            heatmap_map: Dict[str, int] = {}
            for row in poi_rows:
                zone_name = row.get("parent_zone") or "unknown"
                heatmap_map[zone_name] = heatmap_map.get(zone_name, 0) + _safe_seconds(row.get("duration_seconds"))
        else:
            heatmap_map = {}
            for row in tracking_rows:
                zone_name = row.get("zone_name") or "unknown"
                dwell_ms = int(row.get("dwell_time_ms") or 0)
                heatmap_map[zone_name] = heatmap_map.get(zone_name, 0) + dwell_ms

        max_value = max(heatmap_map.values()) if heatmap_map else 1
        heatmap_data: List[Dict[str, Any]] = []
        for zone_name, raw_value in heatmap_map.items():
            coords = _zone_to_xy(zone_name)
            heatmap_data.append(
                {
                    "zone_name": zone_name,
                    "x": coords["x"],
                    "y": coords["y"],
                    "intensity": round((raw_value / max_value) * 100, 2),
                    "raw_value": raw_value,
                }
            )

        heatmap_data.sort(key=lambda item: item["intensity"], reverse=True)

        return {
            "status": "success",
            "count": len(heatmap_data),
            "data": heatmap_data,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.error(f"Error retrieving heatmap for {property_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve heatmap data",
        )


@router.get("/analytics/dashboard")
async def get_dashboard_analytics(db: SupabaseDB = Depends(get_database)):
    """Return global dashboard metrics for frontend overview cards/charts."""
    try:
        sessions = _safe_rows(
            db.client.table("vr_sessions")
            .select("id, started_at, duration_seconds, customer_id, property_id")
            .order("started_at", desc=True)
            .execute()
        )
        poi_rows = _safe_rows(db.client.table("poi_visits").select("id, duration_seconds").execute())
        view_rows = _safe_rows(db.client.table("view_events").select("id, duration_seconds").execute())
        tracking_rows = _safe_rows(db.client.table("tracking_events").select("id").execute())

        total_sessions = len(sessions)
        total_customers = len({s.get("customer_id") for s in sessions if s.get("customer_id")})
        total_properties = len({s.get("property_id") for s in sessions if s.get("property_id")})
        total_session_seconds = sum(_safe_seconds(s.get("duration_seconds")) for s in sessions)
        avg_session_duration = int(total_session_seconds / total_sessions) if total_sessions else 0

        # Last 7-day trend from session start date
        trend_map: Dict[str, int] = {}
        for session in sessions:
            started_at = session.get("started_at")
            if not started_at:
                continue
            day = started_at[:10]
            trend_map[day] = trend_map.get(day, 0) + 1

        trend = [{"date": day, "sessions": count} for day, count in sorted(trend_map.items())][-7:]

        return {
            "status": "success",
            "data": {
                "total_sessions": total_sessions,
                "total_customers": total_customers,
                "total_properties": total_properties,
                "total_session_seconds": total_session_seconds,
                "avg_session_duration": avg_session_duration,
                "poi_visit_count": len(poi_rows),
                "view_event_count": len(view_rows),
                "tracking_event_count": len(tracking_rows),
                "session_trend": trend,
            },
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.error(f"Error retrieving dashboard analytics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dashboard analytics",
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
