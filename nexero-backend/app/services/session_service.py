"""
Session Service for Nexero VR Real Estate Platform.

This module handles the business logic for VR session lifecycle management.
It orchestrates session creation, completion, and data processing between
Unreal Engine VR client and the database.

Session Lifecycle:
1. User starts VR tour → start_session() creates active session
2. User explores property → tracking events recorded (separate service)
3. User ends tour → end_session() calculates duration and marks complete

Usage:
    from app.services.session_service import SessionService
    from app.core.database import SupabaseDB
    
    db = SupabaseDB()
    service = SessionService(db)
    
    # Start new session
    session = await service.start_session(
        customer_id="cust_12345",
        property_id="prop_67890"
    )
    
    # End session
    completed = await service.end_session(session["session_id"])
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional
from app.core.database import SupabaseDB

# Configure logging
logger = logging.getLogger(__name__)


# Date formats Unreal might send
DATE_FORMATS = [
    "%d-%b-%Y, %I:%M:%S %p",  # "02-Dec-2025, 2:54:12 pm"
    "%d-%b-%Y, %I:%M:%S%p",   # "02-Dec-2025, 2:54:12pm"
    "%Y-%m-%d %H:%M:%S",       # "2025-12-02 14:54:12"
    "%Y-%m-%dT%H:%M:%S",       # "2025-12-02T14:54:12"
    "%Y-%m-%dT%H:%M:%S.%f",    # "2025-12-02T14:54:12.000"
    "%Y-%m-%dT%H:%M:%S%z",     # "2025-12-02T14:54:12+00:00"
]


class SessionService:
    """
    Service layer for VR session management.
    
    Handles session lifecycle operations including creation, completion,
    and data processing. Provides business logic layer between API
    endpoints and database operations.
    
    Attributes:
        db: SupabaseDB instance for database operations
    """
    
    def __init__(self, db: SupabaseDB):
        """
        Initialize SessionService with database connection.
        
        Args:
            db: SupabaseDB instance for data persistence
        """
        self.db = db
        logger.info("SessionService initialized")
    
    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """
        Parse timestamp string in various formats to datetime.
        
        Supports:
        - Unix timestamp: "1733148852" or 1733148852
        - Human readable: "02-Dec-2025, 2:54:12 pm"
        - ISO format: "2025-12-02T14:54:12"
        
        Args:
            timestamp_str: Timestamp as string or number
            
        Returns:
            datetime: Parsed datetime with UTC timezone
            
        Raises:
            ValueError: If timestamp cannot be parsed
        """
        # Handle numeric string (Unix timestamp)
        try:
            timestamp_float = float(timestamp_str)
            return datetime.fromtimestamp(timestamp_float, tz=timezone.utc)
        except (ValueError, TypeError):
            pass
        
        # Try various date formats
        for fmt in DATE_FORMATS:
            try:
                dt = datetime.strptime(str(timestamp_str), fmt)
                # Add UTC timezone if not present
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except ValueError:
                continue
        
        # Nothing worked
        raise ValueError(f"Could not parse timestamp: {timestamp_str}")
    
    async def start_session(
        self,
        customer_id: Optional[str] = None,
        property_id: Optional[str] = None
    ) -> dict:
        """
        Create a new VR session when customer starts a tour.
        
        Generates a unique session ID and records the start time.
        The session remains active until explicitly ended.
        
        Args:
            customer_id: Optional customer identifier for tracking
            property_id: Optional property/listing being toured
        
        Returns:
            dict: Created session data including:
                - session_id: Unique session identifier (UUID)
                - started_at: UTC timestamp when session started
                - status: "active"
                - customer_id: Customer identifier (if provided)
                - property_id: Property identifier (if provided)
                
        Raises:
            Exception: If database insertion fails
            
        Example:
            session = await service.start_session(
                customer_id="cust_12345",
                property_id="prop_67890"
            )
            print(f"Session started: {session['session_id']}")
        """
        try:
            # Generate unique session identifier
            session_id = str(uuid.uuid4())
            
            # Get current UTC timestamp
            started_at = datetime.now(timezone.utc)
            
            # Create session data structure
            session_data = {
                "id": session_id,
                "started_at": started_at.isoformat(),
                "status": "active",
                "customer_id": customer_id,
                "property_id": property_id
            }
            
            # Insert into database
            created_session = await self.db.create_session(session_data)
            
            if not created_session:
                raise Exception("Failed to create session in database")
            
            logger.info(
                f"Started VR session {session_id} for customer={customer_id}, "
                f"property={property_id}"
            )
            
            return created_session
            
        except Exception as e:
            logger.error(f"Failed to start session: {e}", exc_info=True)
            raise
    
    async def end_session(
        self,
        session_id: str,
        ended_at: Optional[datetime] = None
    ) -> dict:
        """
        End an active VR session and calculate duration.
        
        Marks the session as completed and calculates the total time
        spent in the VR tour. This is typically called when the customer
        exits the VR experience.
        
        Args:
            session_id: UUID of the session to end
            ended_at: Optional end timestamp (defaults to current time)
        
        Returns:
            dict: Updated session data including:
                - ended_at: Timestamp when session ended
                - duration_seconds: Total session duration in seconds
                - status: "completed"
                - All original session fields
                
        Raises:
            ValueError: If session not found in database
            Exception: If database update fails
            
        Example:
            completed = await service.end_session("session_abc123")
            print(f"Session lasted {completed['duration_seconds']} seconds")
        """
        try:
            # Fetch existing session
            session = await self.db.get_session(session_id)
            
            if not session:
                error_msg = f"Session not found: {session_id}"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            # Use provided end time or current time
            if ended_at is None:
                ended_at = datetime.now(timezone.utc)
            
            # Parse started_at timestamp from database
            started_at = datetime.fromisoformat(
                session["started_at"].replace("Z", "+00:00")
            )
            
            # Calculate session duration
            duration = ended_at - started_at
            duration_seconds = int(duration.total_seconds())
            
            # Prepare update data
            updates = {
                "ended_at": ended_at.isoformat(),
                "duration_seconds": duration_seconds,
                "status": "completed"
            }
            
            # Update session in database
            updated_session = await self.db.update_session(session_id, updates)
            
            if not updated_session:
                raise Exception("Failed to update session in database")
            
            logger.info(
                f"Ended VR session {session_id}: duration={duration_seconds}s, "
                f"status=completed"
            )
            
            return updated_session
            
        except ValueError:
            # Re-raise ValueError as is
            raise
        except Exception as e:
            logger.error(f"Failed to end session {session_id}: {e}", exc_info=True)
            raise
    
    async def get_session(self, session_id: str) -> Optional[dict]:
        """
        Fetch VR session details by ID.
        
        Retrieves complete session information for validation,
        analytics, or display purposes.
        
        Args:
            session_id: UUID of the session to retrieve
        
        Returns:
            dict: Session data if found, None otherwise
            
        Example:
            session = await service.get_session("session_abc123")
            if session:
                print(f"Status: {session['status']}")
                print(f"Duration: {session.get('duration_seconds')}s")
        """
        try:
            session = await self.db.get_session(session_id)
            
            if session:
                logger.debug(f"Retrieved session {session_id}")
            else:
                logger.warning(f"Session not found: {session_id}")
            
            return session
            
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}", exc_info=True)
            return None
    
    async def process_unreal_session_data(
        self,
        session_start: str,
        session_end: str,
        customer_id: Optional[str] = None,
        property_id: Optional[str] = None
    ) -> dict:
        """
        Process legacy session data format from Unreal Engine.
        
        Handles backward compatibility with test formats where Unreal
        sends session start/end times as Unix timestamp strings.
        Creates a complete session record with pre-determined timestamps.
        
        This is useful for:
        - Processing historical VR session data
        - Testing with pre-recorded sessions
        - Handling offline VR experiences synced later
        
        Args:
            session_start: Unix timestamp string (e.g., "1727653800")
            session_end: Unix timestamp string (e.g., "1727654100")
            customer_id: Optional customer identifier
            property_id: Optional property identifier
        
        Returns:
            dict: Complete session data with calculated duration
            
        Raises:
            ValueError: If timestamp strings are invalid
            Exception: If database operations fail
            
        Example:
            session = await service.process_unreal_session_data(
                session_start="1727653800",
                session_end="1727654100",
                customer_id="cust_12345",
                property_id="prop_67890"
            )
            print(f"Processed session: {session['id']}")
            print(f"Duration: {session['duration_seconds']}s")
        """
        try:
            # Try to parse timestamps - support multiple formats
            started_at = self._parse_timestamp(session_start)
            ended_at = self._parse_timestamp(session_end)
            
            logger.info(
                f"Processing Unreal session data: "
                f"start={started_at.isoformat()}, end={ended_at.isoformat()}"
            )
            
            # Generate session ID
            session_id = str(uuid.uuid4())
            
            # Calculate duration
            duration = ended_at - started_at
            duration_seconds = int(duration.total_seconds())
            
            # Create complete session data
            session_data = {
                "id": session_id,
                "started_at": started_at.isoformat(),
                "ended_at": ended_at.isoformat(),
                "duration_seconds": duration_seconds,
                "status": "completed",
                "customer_id": customer_id,
                "property_id": property_id
            }
            
            # Insert complete session into database
            created_session = await self.db.create_session(session_data)
            
            if not created_session:
                raise Exception("Failed to create session in database")
            
            logger.info(
                f"Processed Unreal session {session_id}: "
                f"duration={duration_seconds}s, status=completed"
            )
            
            return created_session
            
        except ValueError as e:
            logger.error(f"Invalid timestamp format: {e}", exc_info=True)
            raise ValueError(f"Invalid timestamp strings: {e}")
        except Exception as e:
            logger.error(f"Failed to process Unreal session data: {e}", exc_info=True)
            raise
