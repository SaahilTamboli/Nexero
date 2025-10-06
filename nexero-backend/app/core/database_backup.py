"""
Supabase databafrom typing import List, Optional, Dict, Any
from supabase import create_client, Client
from app.config import get_settings
from datetime import datetime, timezone

# Configure logging
logger = logging.getLogger(__name__)


def _convert_timestamp_to_iso(value: Any) -> str:
    """
    Convert various timestamp formats to ISO 8601 string.
    
    Handles:
    - Unix timestamp (float/int): 1759479689.384201
    - ISO string: "2025-10-03T08:21:25+00:00"
    - datetime object
    
    Args:
        value: Timestamp in various formats
        
    Returns:
        str: ISO 8601 formatted timestamp string
    """
    # Already a string in ISO format
    if isinstance(value, str):
        # If it's a numeric string, convert to float first
        try:
            if '.' in value or value.isdigit():
                value = float(value)
            else:
                return value  # Already ISO format
        except ValueError:
            return value  # Already ISO format
    
    # Unix timestamp (float or int)
    if isinstance(value, (int, float)):
        dt = datetime.fromtimestamp(value, tz=timezone.utc)
        return dt.isoformat()
    
    # datetime object
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()
    
    # Fallback: return as-is
    return str(value)pper for Nexero VR backend.

This module provides async methods to interact with Supabase (PostgreSQL)
for storing VR session data and tracking events from Unreal Engine.

Database Tables:
- vr_sessions: Session metadata (start/end times, customer, property)
- tracking_events: Individual tracking events (gaze, zones, interactions)
- customers: Customer information

Usage:
    from app.core.database import SupabaseDB
    
    db = SupabaseDB()
    session = await db.create_session(session_data)
    await db.insert_tracking_events_batch(events)
"""

import logging
from typing import List, Optional
from supabase import create_client, Client
from app.config import get_settings

# Configure logging
logger = logging.getLogger(__name__)


class SupabaseDB:
    """
    Database wrapper for Supabase operations.
    
    Provides async methods to store and retrieve VR session data and
    tracking events. Handles errors gracefully and logs all database
    operations for debugging and monitoring.
    
    Attributes:
        client: Supabase client instance
    """
    
    def __init__(self):
        """
        Initialize Supabase database connection.
        
        Loads configuration from environment variables and creates
        a Supabase client instance for database operations.
        """
        settings = get_settings()
        self.client: Client = create_client(
            supabase_url=settings.SUPABASE_URL,
            supabase_key=settings.SUPABASE_KEY
        )
        logger.info("Supabase database connection initialized")
    
    async def create_session(self, session_data: dict) -> Optional[dict]:
        """
        Create a new VR session record in the database.
        
        Inserts session metadata when a VR tour starts. This creates
        the parent record that tracking events will link to.
        
        Args:
            session_data: Dictionary containing session fields:
                - session_start: datetime
                - session_end: datetime (can be updated later)
                - customer_id: Optional customer identifier
                - property_id: Optional property identifier
        
        Returns:
            dict: Inserted session data with generated ID, or None on failure
            
        Example:
            session_data = {
                "session_start": datetime.now(),
                "session_end": datetime.now(),
                "customer_id": "cust_12345",
                "property_id": "prop_67890"
            }
            session = await db.create_session(session_data)
            print(session["id"])  # Generated session ID
        """
        try:
            response = self.client.table("vr_sessions").insert(session_data).execute()
            logger.info(f"Created VR session: {response.data}")
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Failed to create session: {e}", exc_info=True)
            return None
    
    async def update_session(self, session_id: str, updates: dict) -> Optional[dict]:
        """
        Update an existing VR session record.
        
        Used to update session information, typically when the session ends
        or to add additional metadata after session creation.
        
        Args:
            session_id: UUID of the session to update
            updates: Dictionary of fields to update (e.g., session_end time)
        
        Returns:
            dict: Updated session data, or None on failure
            
        Example:
            updates = {"session_end": datetime.now()}
            updated = await db.update_session("session_abc123", updates)
        """
        try:
            response = (
                self.client.table("vr_sessions")
                .update(updates)
                .eq("id", session_id)
                .execute()
            )
            logger.info(f"Updated session {session_id}: {updates}")
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Failed to update session {session_id}: {e}", exc_info=True)
            return None
    
    async def get_session(self, session_id: str) -> Optional[dict]:
        """
        Fetch a VR session by ID.
        
        Retrieves complete session metadata for analytics, reporting,
        or validation purposes.
        
        Args:
            session_id: UUID of the session to retrieve
        
        Returns:
            dict: Session data including all fields, or None if not found
            
        Example:
            session = await db.get_session("session_abc123")
            if session:
                print(f"Session started: {session['session_start']}")
        """
        try:
            response = (
                self.client.table("vr_sessions")
                .select("*")
                .eq("id", session_id)
                .execute()
            )
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}", exc_info=True)
            return None
    
    async def insert_tracking_event(self, event: dict) -> bool:
        """
        Insert a single tracking event into the database.
        
        Stores individual tracking events like gaze tracking, zone transitions,
        or user interactions during VR tours.
        
        Args:
            event: Dictionary containing event data:
                - session_id: Associated session UUID
                - event_type: Type of event (gaze, zone_enter, etc.)
                - timestamp: Event timestamp
                - Additional fields based on event type
        
        Returns:
            bool: True if insertion succeeded, False otherwise
            
        Example:
            event = {
                "session_id": "session_abc123",
                "event_type": "gaze",
                "timestamp": datetime.now(),
                "zone_name": "kitchen",
                "gaze_target": "countertop",
                "dwell_time_ms": 2500
            }
            success = await db.insert_tracking_event(event)
        """
        try:
            self.client.table("tracking_events").insert(event).execute()
            logger.debug(f"Inserted tracking event: {event.get('event_type')}")
            return True
        except Exception as e:
            logger.error(f"Failed to insert tracking event: {e}", exc_info=True)
            return False
    
    async def insert_tracking_events_batch(self, events: List[dict]) -> int:
        """
        Insert multiple tracking events efficiently in a batch.
        
        Optimized for high-frequency event streams from Unreal Engine.
        Continues processing even if individual events fail, ensuring
        maximum data capture during VR sessions.
        
        Args:
            events: List of event dictionaries to insert
        
        Returns:
            int: Count of successfully inserted events
            
        Example:
            events = [
                {"session_id": "session_abc123", "event_type": "gaze", ...},
                {"session_id": "session_abc123", "event_type": "zone_enter", ...},
                {"session_id": "session_abc123", "event_type": "interaction", ...}
            ]
            count = await db.insert_tracking_events_batch(events)
            print(f"Inserted {count} of {len(events)} events")
        """
        success_count = 0
        
        try:
            # Attempt batch insert (more efficient)
            response = self.client.table("tracking_events").insert(events).execute()
            success_count = len(response.data) if response.data else 0
            logger.info(f"Batch inserted {success_count} tracking events")
            return success_count
        except Exception as e:
            logger.warning(f"Batch insert failed, trying individual inserts: {e}")
            
            # Fallback: Insert individually to save as many as possible
            for event in events:
                try:
                    self.client.table("tracking_events").insert(event).execute()
                    success_count += 1
                except Exception as event_error:
                    logger.error(f"Failed to insert individual event: {event_error}")
                    continue
            
            logger.info(f"Individually inserted {success_count}/{len(events)} events")
            return success_count
    
    async def get_session_events(self, session_id: str) -> List[dict]:
        """
        Retrieve all tracking events for a specific session.
        
        Fetches all events associated with a VR session, ordered
        chronologically for analytics and visualization.
        
        Args:
            session_id: UUID of the session
        
        Returns:
            list: List of event dictionaries ordered by timestamp,
                  empty list if no events found or on error
                  
        Example:
            events = await db.get_session_events("session_abc123")
            for event in events:
                print(f"{event['timestamp']}: {event['event_type']}")
        """
        try:
            response = (
                self.client.table("tracking_events")
                .select("*")
                .eq("session_id", session_id)
                .order("timestamp", desc=False)
                .execute()
            )
            logger.info(f"Retrieved {len(response.data)} events for session {session_id}")
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Failed to get events for session {session_id}: {e}", exc_info=True)
            return []
