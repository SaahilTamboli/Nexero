"""
Tracking Service for Nexero VR Real Estate Platform.

This module handles tracking events from Unreal Engine VR sessions.
Events include gaze tracking, zone transitions, and user interactions.

CURRENT WORKFLOW (MVP):
1. Sales person starts VR session from dashboard
2. Customer experiences VR tour (events collected locally in Unreal)
3. Session ends, Unreal sends all tracking data in batch to backend
4. Backend processes and stores events for analytics
5. AI/ML analyzes data to generate insights for builders and sales team

FUTURE ENHANCEMENT:
Live streaming of events during tour (currently not implemented).
Current batch approach is more reliable and reduces network overhead.

Usage:
    from app.services.tracking_service import TrackingService
    from app.core.database import SupabaseDB
    
    db = SupabaseDB()
    service = TrackingService(db)
    
    # Process batch of events after session ends
    result = await service.log_events_batch(session_id, events)
    print(f"Stored {result['successful_count']} events")
"""

import logging
from typing import List, Optional
from app.core.database import SupabaseDB

# Configure logging
logger = logging.getLogger(__name__)


class TrackingService:
    """
    Service layer for VR tracking event management.
    
    Handles storage and retrieval of tracking events captured during
    VR tours. Designed for defensive operation - tracking failures
    should never crash the VR client or interrupt the user experience.
    
    Current Implementation:
    - Post-session batch processing (events sent after tour ends)
    - Efficient bulk insertion with error tolerance
    - Analytics-focused event retrieval
    
    Attributes:
        db: SupabaseDB instance for database operations
    """
    
    def __init__(self, db: SupabaseDB):
        """
        Initialize TrackingService with database connection.
        
        Args:
            db: SupabaseDB instance for data persistence
        """
        self.db = db
        logger.info("TrackingService initialized")
    
    async def log_event(self, session_id: str, event_data: dict) -> bool:
        """
        Store a single tracking event from VR session.
        
        Defensive implementation: validates data but never raises exceptions
        that could interrupt VR experience. Logs warnings for invalid data.
        
        Args:
            session_id: UUID of the VR session
            event_data: Dictionary containing event information:
                - event_type: Required (gaze, zone_enter, zone_exit, interaction)
                - timestamp: Optional (added if missing)
                - Additional fields based on event type
        
        Returns:
            bool: True if event stored successfully, False otherwise
            
        Example:
            success = await service.log_event(
                session_id="session_abc123",
                event_data={
                    "event_type": "gaze",
                    "zone_name": "kitchen",
                    "gaze_target": "granite_countertop",
                    "dwell_time_ms": 2500
                }
            )
        """
        try:
            # Validate required field
            if "event_type" not in event_data:
                logger.warning(
                    f"Missing event_type in event data for session {session_id}. "
                    f"Skipping event."
                )
                return False
            
            # Ensure session_id is in event data
            if "session_id" not in event_data:
                event_data["session_id"] = session_id
            
            # Add timestamp if not present (use database default)
            # Database will handle timestamp if not provided
            
            # Insert event into database
            success = await self.db.insert_tracking_event(event_data)
            
            if success:
                logger.debug(
                    f"Logged event: session={session_id}, "
                    f"type={event_data['event_type']}"
                )
            else:
                logger.warning(
                    f"Failed to insert event for session {session_id}: "
                    f"type={event_data.get('event_type')}"
                )
            
            return success
            
        except Exception as e:
            # Defensive: log error but don't raise exception
            logger.error(
                f"Error logging event for session {session_id}: {e}",
                exc_info=True
            )
            return False
    
    async def log_events_batch(
        self,
        session_id: str,
        events: List[dict]
    ) -> dict:
        """
        Store multiple tracking events efficiently in a batch.
        
        Primary method for current workflow where Unreal sends all events
        after the VR session ends. Optimized for bulk processing with
        error tolerance to maximize data capture.
        
        Args:
            session_id: UUID of the VR session
            events: List of event dictionaries to store
        
        Returns:
            dict: Processing results with:
                - total_events: Total number of events received
                - successful_count: Number of events stored successfully
                - failed_count: Number of events that failed to store
                - success_rate: Percentage of successful insertions
                
        Example:
            events = [
                {"event_type": "gaze", "zone_name": "kitchen", ...},
                {"event_type": "zone_enter", "zone_name": "bedroom", ...},
                {"event_type": "interaction", "object_name": "window", ...}
            ]
            
            result = await service.log_events_batch("session_abc123", events)
            print(f"Stored {result['successful_count']}/{result['total_events']} events")
        """
        try:
            total_events = len(events)
            
            if total_events == 0:
                logger.warning(f"Empty events list for session {session_id}")
                return {
                    "total_events": 0,
                    "successful_count": 0,
                    "failed_count": 0,
                    "success_rate": 0.0
                }
            
            # Ensure all events have session_id
            for event in events:
                if "session_id" not in event:
                    event["session_id"] = session_id
                
                # Validate event_type (log warning but include anyway)
                if "event_type" not in event:
                    logger.warning(
                        f"Event missing event_type in session {session_id}, "
                        f"event data: {event}"
                    )
            
            # Batch insert events
            successful_count = await self.db.insert_tracking_events_batch(events)
            failed_count = total_events - successful_count
            success_rate = (successful_count / total_events * 100) if total_events > 0 else 0
            
            logger.info(
                f"Batch processed for session {session_id}: "
                f"{successful_count}/{total_events} events stored "
                f"({success_rate:.1f}% success rate)"
            )
            
            result = {
                "total_events": total_events,
                "successful_count": successful_count,
                "failed_count": failed_count,
                "success_rate": success_rate
            }
            
            return result
            
        except Exception as e:
            # Defensive: log error but return failure stats instead of raising
            logger.error(
                f"Error in batch processing for session {session_id}: {e}",
                exc_info=True
            )
            return {
                "total_events": len(events) if events else 0,
                "successful_count": 0,
                "failed_count": len(events) if events else 0,
                "success_rate": 0.0
            }
    
    async def get_session_events(
        self,
        session_id: str,
        event_type: Optional[str] = None
    ) -> List[dict]:
        """
        Retrieve tracking events for analytics and insights generation.
        
        Fetches events for a specific session, optionally filtered by type.
        Used by analytics engine and dashboard to understand user behavior.
        
        Args:
            session_id: UUID of the VR session
            event_type: Optional filter for specific event type
                       (e.g., "gaze", "zone_enter", "interaction")
        
        Returns:
            list: List of event dictionaries sorted by timestamp,
                  empty list if no events found or on error
                  
        Example:
            # Get all events
            all_events = await service.get_session_events("session_abc123")
            
            # Get only gaze events
            gaze_events = await service.get_session_events(
                "session_abc123",
                event_type="gaze"
            )
            
            # Analyze customer interest
            for event in gaze_events:
                print(f"Looked at {event['gaze_target']} "
                      f"for {event['dwell_time_ms']}ms")
        """
        try:
            # Fetch all events for session
            events = await self.db.get_session_events(session_id)
            
            # Filter by event_type if specified
            if event_type:
                events = [
                    event for event in events
                    if event.get("event_type") == event_type
                ]
                logger.debug(
                    f"Retrieved {len(events)} {event_type} events "
                    f"for session {session_id}"
                )
            else:
                logger.debug(
                    f"Retrieved {len(events)} total events "
                    f"for session {session_id}"
                )
            
            return events
            
        except Exception as e:
            # Defensive: log error and return empty list
            logger.error(
                f"Error retrieving events for session {session_id}: {e}",
                exc_info=True
            )
            return []
    
    async def get_zone_events(
        self,
        session_id: str,
        zone_name: str
    ) -> List[dict]:
        """
        Get all tracking events for a specific zone/room.
        
        Useful for zone-specific analytics like:
        - Which rooms get most attention?
        - How long do customers spend in master bedroom?
        - What do they interact with in the kitchen?
        
        Args:
            session_id: UUID of the VR session
            zone_name: Name of zone to filter (e.g., "kitchen", "master_bedroom")
        
        Returns:
            list: List of events that occurred in the specified zone,
                  sorted by timestamp, empty list if none found
                  
        Example:
            # Analyze kitchen engagement
            kitchen_events = await service.get_zone_events(
                "session_abc123",
                "kitchen"
            )
            
            print(f"Customer spent time in kitchen:")
            for event in kitchen_events:
                print(f"- {event['event_type']}: {event.get('gaze_target')}")
        """
        try:
            # Fetch all events for session
            all_events = await self.db.get_session_events(session_id)
            
            # Filter events by zone_name
            zone_events = [
                event for event in all_events
                if event.get("zone_name") == zone_name
            ]
            
            logger.debug(
                f"Retrieved {len(zone_events)} events for zone '{zone_name}' "
                f"in session {session_id}"
            )
            
            return zone_events
            
        except Exception as e:
            # Defensive: log error and return empty list
            logger.error(
                f"Error retrieving zone events for session {session_id}, "
                f"zone {zone_name}: {e}",
                exc_info=True
            )
            return []
