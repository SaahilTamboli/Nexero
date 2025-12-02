"""
Enhanced Supabase database operations for Nexero VR Analytics.

This module provides comprehensive database operations for:
- Session management (create, update, end sessions)
- Zone visit tracking
- POI interaction logging
- Customer profile management
- Analytics queries

Usage:
    from app.core.database_v2 import NexeroDB
    
    db = NexeroDB()
    session = await db.create_session(session_data)
    await db.record_zone_visit(session_id, zone_data)
    analytics = await db.get_session_analytics(session_id)
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from supabase import create_client, Client
from app.config import get_settings

logger = logging.getLogger(__name__)


def _to_iso(value: Any) -> str:
    """Convert timestamp to ISO 8601 format."""
    if isinstance(value, str):
        try:
            if '.' in value or value.isdigit():
                value = float(value)
            else:
                return value
        except ValueError:
            return value
    
    if isinstance(value, (int, float)):
        dt = datetime.fromtimestamp(value, tz=timezone.utc)
        return dt.isoformat()
    
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()
    
    return str(value)


def _now_iso() -> str:
    """Get current UTC time in ISO format."""
    return datetime.now(timezone.utc).isoformat()


class NexeroDB:
    """
    Enhanced database wrapper for Nexero VR Analytics.
    
    Provides methods for all analytics data operations including
    sessions, zone visits, POI interactions, and customer profiles.
    """
    
    def __init__(self):
        """Initialize Supabase connection."""
        settings = get_settings()
        self.client: Client = create_client(
            supabase_url=settings.SUPABASE_URL,
            supabase_key=settings.SUPABASE_KEY
        )
        logger.info("NexeroDB initialized")
    
    # =========================================================================
    # SESSION MANAGEMENT
    # =========================================================================
    
    async def create_session(
        self,
        session_code: str,
        started_at: Any,
        property_id: Optional[str] = None,
        unit_id: Optional[str] = None,
        customer_id: Optional[str] = None,
        device_type: Optional[str] = None,
        entry_source: Optional[str] = None,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Create a new VR session.
        
        Args:
            session_code: Unique session identifier from Unreal
            started_at: Session start timestamp
            property_id: UUID of property being viewed
            unit_id: UUID of specific unit
            customer_id: UUID of customer (if known)
            device_type: "desktop", "mobile", "vr_headset"
            entry_source: "website", "qr_code", "direct_link"
        
        Returns:
            Created session data or None on failure
        """
        try:
            # Check if this is a return visit
            is_return = False
            visit_number = 1
            
            if customer_id:
                existing = self.client.table("vr_sessions").select("id").eq(
                    "customer_id", customer_id
                ).execute()
                if existing.data:
                    is_return = True
                    visit_number = len(existing.data) + 1
            
            session_data = {
                "session_code": session_code,
                "started_at": _to_iso(started_at),
                "status": "active",
                "is_return_visit": is_return,
                "visit_number": visit_number
            }
            
            # Add optional fields
            if property_id:
                session_data["property_id"] = property_id
            if unit_id:
                session_data["unit_id"] = unit_id
            if customer_id:
                session_data["customer_id"] = customer_id
            if device_type:
                session_data["device_type"] = device_type
            if entry_source:
                session_data["entry_source"] = entry_source
            if user_agent:
                session_data["user_agent"] = user_agent
            if ip_address:
                session_data["ip_address"] = ip_address
            
            response = self.client.table("vr_sessions").insert(session_data).execute()
            logger.info(f"Created session: {session_code}")
            return response.data[0] if response.data else None
            
        except Exception as e:
            logger.error(f"Failed to create session: {e}", exc_info=True)
            return None
    
    async def end_session(
        self,
        session_id: str,
        ended_at: Any,
        status: str = "completed",
        exit_point: Optional[str] = None
    ) -> Optional[Dict]:
        """
        End a VR session and compute final metrics.
        
        Args:
            session_id: UUID of session to end
            ended_at: Session end timestamp
            status: "completed", "dropped", "error"
            exit_point: Last zone visited
        
        Returns:
            Updated session data or None on failure
        """
        try:
            # Get zone visit stats
            zone_stats = self.client.table("zone_visits").select(
                "id", count="exact"
            ).eq("session_id", session_id).execute()
            
            # Get POI stats
            poi_stats = self.client.table("poi_interactions").select(
                "id", count="exact"
            ).eq("session_id", session_id).execute()
            
            updates = {
                "ended_at": _to_iso(ended_at),
                "status": status,
                "zones_visited": zone_stats.count or 0,
                "pois_viewed": poi_stats.count or 0,
                "updated_at": _now_iso()
            }
            
            if exit_point:
                updates["exit_point"] = exit_point
            
            response = self.client.table("vr_sessions").update(updates).eq(
                "id", session_id
            ).execute()
            
            logger.info(f"Ended session: {session_id} with status: {status}")
            return response.data[0] if response.data else None
            
        except Exception as e:
            logger.error(f"Failed to end session: {e}", exc_info=True)
            return None
    
    async def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session by ID."""
        try:
            response = self.client.table("vr_sessions").select("*").eq(
                "id", session_id
            ).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Failed to get session: {e}", exc_info=True)
            return None
    
    async def get_session_by_code(self, session_code: str) -> Optional[Dict]:
        """Get session by session_code (from Unreal)."""
        try:
            response = self.client.table("vr_sessions").select("*").eq(
                "session_code", session_code
            ).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Failed to get session by code: {e}", exc_info=True)
            return None
    
    # =========================================================================
    # ZONE VISIT TRACKING
    # =========================================================================
    
    async def record_zone_enter(
        self,
        session_id: str,
        zone_name: str,
        zone_type: str,
        entered_at: Any,
        zone_id: Optional[str] = None,
        visit_order: Optional[int] = None,
        is_entry_point: bool = False
    ) -> Optional[Dict]:
        """
        Record when user enters a zone.
        
        Args:
            session_id: UUID of active session
            zone_name: Name of zone entered
            zone_type: Type of zone (living_room, bedroom, etc.)
            entered_at: Timestamp of entry
            zone_id: UUID of zone (if known)
            visit_order: Order of this zone in the journey
            is_entry_point: True if first zone of session
        
        Returns:
            Created zone visit record or None
        """
        try:
            visit_data = {
                "session_id": session_id,
                "zone_name": zone_name,
                "zone_type": zone_type,
                "entered_at": _to_iso(entered_at),
                "is_entry_point": is_entry_point
            }
            
            if zone_id:
                visit_data["zone_id"] = zone_id
            if visit_order is not None:
                visit_data["visit_order"] = visit_order
            
            # Update session entry point if this is first zone
            if is_entry_point:
                self.client.table("vr_sessions").update({
                    "entry_point": zone_name
                }).eq("id", session_id).execute()
            
            response = self.client.table("zone_visits").insert(visit_data).execute()
            logger.debug(f"Zone enter recorded: {zone_name}")
            return response.data[0] if response.data else None
            
        except Exception as e:
            logger.error(f"Failed to record zone enter: {e}", exc_info=True)
            return None
    
    async def record_zone_exit(
        self,
        zone_visit_id: str,
        exited_at: Any,
        interactions_count: int = 0,
        pois_viewed: int = 0
    ) -> Optional[Dict]:
        """
        Record when user exits a zone.
        
        Args:
            zone_visit_id: UUID of zone visit to update
            exited_at: Timestamp of exit
            interactions_count: Number of interactions in zone
            pois_viewed: Number of POIs viewed in zone
        
        Returns:
            Updated zone visit record or None
        """
        try:
            updates = {
                "exited_at": _to_iso(exited_at),
                "interactions_count": interactions_count,
                "pois_viewed": pois_viewed
            }
            
            response = self.client.table("zone_visits").update(updates).eq(
                "id", zone_visit_id
            ).execute()
            
            logger.debug(f"Zone exit recorded: {zone_visit_id}")
            return response.data[0] if response.data else None
            
        except Exception as e:
            logger.error(f"Failed to record zone exit: {e}", exc_info=True)
            return None
    
    # =========================================================================
    # POI INTERACTION TRACKING
    # =========================================================================
    
    async def record_poi_interaction(
        self,
        session_id: str,
        poi_name: str,
        poi_type: str,
        interaction_type: str,
        started_at: Any,
        zone_name: Optional[str] = None,
        zone_visit_id: Optional[str] = None,
        poi_id: Optional[str] = None,
        duration_ms: Optional[int] = None,
        gaze_duration_ms: Optional[int] = None,
        position: Optional[Dict[str, float]] = None
    ) -> Optional[Dict]:
        """
        Record an interaction with a Point of Interest.
        
        Args:
            session_id: UUID of active session
            poi_name: Name of POI
            poi_type: Type of POI (furniture, view, fixture)
            interaction_type: "view", "gaze", "click", "hover", "zoom"
            started_at: When interaction started
            zone_name: Zone where POI is located
            duration_ms: How long the interaction lasted
            gaze_duration_ms: Gaze dwell time
            position: Viewer position when interacting
        
        Returns:
            Created interaction record or None
        """
        try:
            interaction_data = {
                "session_id": session_id,
                "poi_name": poi_name,
                "poi_type": poi_type,
                "interaction_type": interaction_type,
                "started_at": _to_iso(started_at)
            }
            
            if zone_name:
                interaction_data["zone_name"] = zone_name
            if zone_visit_id:
                interaction_data["zone_visit_id"] = zone_visit_id
            if poi_id:
                interaction_data["poi_id"] = poi_id
            if duration_ms is not None:
                interaction_data["duration_ms"] = duration_ms
            if gaze_duration_ms is not None:
                interaction_data["gaze_duration_ms"] = gaze_duration_ms
            if position:
                interaction_data["viewer_position_x"] = position.get("x")
                interaction_data["viewer_position_y"] = position.get("y")
                interaction_data["viewer_position_z"] = position.get("z")
            
            response = self.client.table("poi_interactions").insert(
                interaction_data
            ).execute()
            
            logger.debug(f"POI interaction recorded: {poi_name}")
            return response.data[0] if response.data else None
            
        except Exception as e:
            logger.error(f"Failed to record POI interaction: {e}", exc_info=True)
            return None
    
    # =========================================================================
    # RAW TRACKING EVENTS
    # =========================================================================
    
    async def insert_tracking_event(self, event: Dict) -> bool:
        """Insert a single raw tracking event."""
        try:
            event_data = event.copy()
            if "timestamp" in event_data:
                event_data["timestamp"] = _to_iso(event_data["timestamp"])
            
            # Handle position/rotation
            if "position" in event_data and isinstance(event_data["position"], dict):
                pos = event_data.pop("position")
                event_data["position_x"] = pos.get("x")
                event_data["position_y"] = pos.get("y")
                event_data["position_z"] = pos.get("z")
            
            if "rotation" in event_data and isinstance(event_data["rotation"], dict):
                rot = event_data.pop("rotation")
                event_data["rotation_pitch"] = rot.get("pitch")
                event_data["rotation_yaw"] = rot.get("yaw")
                event_data["rotation_roll"] = rot.get("roll")
            
            self.client.table("tracking_events").insert(event_data).execute()
            return True
            
        except Exception as e:
            logger.error(f"Failed to insert tracking event: {e}", exc_info=True)
            return False
    
    async def insert_tracking_events_batch(self, events: List[Dict]) -> int:
        """Insert multiple tracking events efficiently."""
        try:
            processed_events = []
            for event in events:
                event_data = event.copy()
                
                if "timestamp" in event_data:
                    event_data["timestamp"] = _to_iso(event_data["timestamp"])
                
                if "position" in event_data and isinstance(event_data["position"], dict):
                    pos = event_data.pop("position")
                    event_data["position_x"] = pos.get("x")
                    event_data["position_y"] = pos.get("y")
                    event_data["position_z"] = pos.get("z")
                
                if "rotation" in event_data and isinstance(event_data["rotation"], dict):
                    rot = event_data.pop("rotation")
                    event_data["rotation_pitch"] = rot.get("pitch")
                    event_data["rotation_yaw"] = rot.get("yaw")
                    event_data["rotation_roll"] = rot.get("roll")
                
                processed_events.append(event_data)
            
            self.client.table("tracking_events").insert(processed_events).execute()
            logger.info(f"Batch inserted {len(processed_events)} tracking events")
            return len(processed_events)
            
        except Exception as e:
            logger.error(f"Failed batch insert: {e}", exc_info=True)
            # Fallback to individual inserts
            count = 0
            for event in events:
                if await self.insert_tracking_event(event):
                    count += 1
            return count
    
    # =========================================================================
    # CUSTOMER MANAGEMENT
    # =========================================================================
    
    async def get_or_create_customer(
        self,
        customer_code: str,
        name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        source: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Get existing customer or create new one.
        
        Args:
            customer_code: Unique customer identifier
            name: Customer name
            email: Customer email
            phone: Customer phone
            source: Lead source
        
        Returns:
            Customer record or None
        """
        try:
            # Try to get existing
            response = self.client.table("customers").select("*").eq(
                "customer_code", customer_code
            ).execute()
            
            if response.data:
                return response.data[0]
            
            # Create new
            customer_data = {"customer_code": customer_code}
            if name:
                customer_data["name"] = name
            if email:
                customer_data["email"] = email
            if phone:
                customer_data["phone"] = phone
            if source:
                customer_data["source"] = source
            
            response = self.client.table("customers").insert(customer_data).execute()
            logger.info(f"Created customer: {customer_code}")
            return response.data[0] if response.data else None
            
        except Exception as e:
            logger.error(f"Failed to get/create customer: {e}", exc_info=True)
            return None
    
    async def update_customer_lead_score(
        self,
        customer_id: str,
        lead_score: int,
        lead_status: str
    ) -> Optional[Dict]:
        """Update customer's lead score and status."""
        try:
            updates = {
                "lead_score": lead_score,
                "lead_status": lead_status,
                "updated_at": _now_iso()
            }
            
            response = self.client.table("customers").update(updates).eq(
                "id", customer_id
            ).execute()
            
            return response.data[0] if response.data else None
            
        except Exception as e:
            logger.error(f"Failed to update lead score: {e}", exc_info=True)
            return None
    
    # =========================================================================
    # ANALYTICS QUERIES
    # =========================================================================
    
    async def get_session_zone_summary(self, session_id: str) -> List[Dict]:
        """Get zone visit summary for a session."""
        try:
            response = self.client.table("zone_visits").select(
                "zone_name, zone_type, duration_seconds, interactions_count, visit_order"
            ).eq("session_id", session_id).order("visit_order").execute()
            
            return response.data or []
            
        except Exception as e:
            logger.error(f"Failed to get zone summary: {e}", exc_info=True)
            return []
    
    async def get_session_poi_summary(self, session_id: str) -> List[Dict]:
        """Get POI interaction summary for a session."""
        try:
            response = self.client.table("poi_interactions").select(
                "poi_name, poi_type, zone_name, interaction_type, duration_ms, gaze_duration_ms"
            ).eq("session_id", session_id).execute()
            
            return response.data or []
            
        except Exception as e:
            logger.error(f"Failed to get POI summary: {e}", exc_info=True)
            return []
    
    async def get_property_sessions(
        self,
        property_id: str,
        days: int = 30,
        limit: int = 100
    ) -> List[Dict]:
        """Get recent sessions for a property."""
        try:
            from_date = datetime.now(timezone.utc).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            from_date = from_date.replace(day=from_date.day - days)
            
            response = self.client.table("vr_sessions").select("*").eq(
                "property_id", property_id
            ).gte("started_at", from_date.isoformat()).order(
                "started_at", desc=True
            ).limit(limit).execute()
            
            return response.data or []
            
        except Exception as e:
            logger.error(f"Failed to get property sessions: {e}", exc_info=True)
            return []
    
    async def get_hot_leads(self, limit: int = 20) -> List[Dict]:
        """Get top leads by score."""
        try:
            response = self.client.table("customers").select("*").eq(
                "lead_status", "hot"
            ).order("lead_score", desc=True).limit(limit).execute()
            
            return response.data or []
            
        except Exception as e:
            logger.error(f"Failed to get hot leads: {e}", exc_info=True)
            return []
    
    async def get_zone_heatmap_data(self, property_id: str) -> List[Dict]:
        """Get zone engagement data for heatmap visualization."""
        try:
            # This would use a more complex query in production
            response = self.client.rpc(
                "get_zone_heatmap",
                {"p_property_id": property_id}
            ).execute()
            
            return response.data or []
            
        except Exception as e:
            logger.error(f"Failed to get heatmap data: {e}", exc_info=True)
            return []


# Singleton instance
_db_instance: Optional[NexeroDB] = None


def get_nexero_db() -> NexeroDB:
    """Get singleton database instance."""
    global _db_instance
    if _db_instance is None:
        _db_instance = NexeroDB()
    return _db_instance
