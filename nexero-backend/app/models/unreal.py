"""
Pydantic models for Unreal Engine VR data validation.

This module defines the data structures that Unreal Engine VR client sends
to our FastAPI backend. All incoming data is validated against these models.

Data Flow:
Unreal Engine VR Tour → HTTP POST → These Models → Database Storage

Models:
- UnrealSessionData: Session start/end metadata
- POIData: Point of Interest tracking (zones, rooms, amenities)
- ViewData: View/navigation tracking with duration
- TrackingEventFromUnreal: Individual tracking events (gaze, zones, interactions)
- TrackingBatchFromUnreal: Batch of multiple tracking events
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator


class ViewModePayload(BaseModel):
    ViewMode: str
    Duration: str
    sesh_id: Optional[str] = None

class POIPayload(BaseModel):
    POI: str
    Click_Source: str
    Category: Optional[str] = None
    Castegory: Optional[str] = None
    POI_Duration: Optional[str] = None
    sesh_id: Optional[str] = None
    Datetime: Optional[str] = None
    
    @property
    def category_name(self) -> str:
        """Return Category or fallback to Castegory for backward compatibility."""
        return self.Category or self.Castegory or ""

class UnitSelectionPayload(BaseModel):
    Name: str
    Sqft: str
    Type: str
    Duration: Optional[str] = None
    sesh_id: Optional[str] = None
    Datetime: Optional[str] = None

class SessionSummaryPayload(BaseModel):
    sesh_id: Optional[str] = None
    session_id: Optional[str] = None
    session_start: str
    session_end: str
    duration: str
    
    @property
    def session_id_value(self) -> str:
        """Return sesh_id or fallback to session_id."""
        return self.sesh_id or self.session_id or ""


class ConnectTypePayload(BaseModel):
    """New event type for site visits and other connection events."""
    Connect_Type: str
    sesh_id: Optional[str] = None


class TrackingEventFromUnreal(BaseModel):
    """
    Single tracking event captured during VR session.
    
    Unreal Engine sends these events to track user behavior:
    - Where they look (gaze tracking)
    - Where they move (position tracking)
    - Which zones they enter/exit (room transitions)
    - What they interact with (clicks, grabs, teleports)
    - How long they spend in each area (dwell time)
    
    The flexible structure allows different event types to include
    only relevant fields. For example:
    - "gaze" events include gaze_target and dwell_time_ms
    - "zone_enter" events include zone_name and position
    - "interaction" events include object_name and interaction_type
    
    Attributes:
        event_type: Type of event (gaze, zone_enter, zone_exit, interaction)
        timestamp: Unix timestamp with milliseconds precision
        session_id: Session identifier (backend adds if not present)
        zone_name: Name of zone/room (e.g., "kitchen", "master_bedroom")
        object_name: Name of object being tracked (e.g., "dining_table")
        position: 3D position in VR space {x, y, z}
        rotation: 3D rotation {pitch, yaw, roll}
        gaze_target: What the user is looking at
        dwell_time_ms: How long user stayed/looked (milliseconds)
        interaction_type: Type of interaction (click, grab, teleport)
        metadata: Additional custom data from Unreal
        
    Example gaze event:
        {
            "event_type": "gaze",
            "timestamp": 1727653850.125,
            "zone_name": "kitchen",
            "gaze_target": "granite_countertop",
            "dwell_time_ms": 2500
        }
        
    Example zone transition:
        {
            "event_type": "zone_enter",
            "timestamp": 1727653855.450,
            "zone_name": "master_bedroom",
            "position": {"x": 10.5, "y": 2.0, "z": -5.3}
        }
    """
    
    event_type: str
    timestamp: float
    session_id: Optional[str] = None
    zone_name: Optional[str] = None
    object_name: Optional[str] = None
    position: Optional[Dict[str, float]] = None
    rotation: Optional[Dict[str, float]] = None
    gaze_target: Optional[str] = None
    dwell_time_ms: Optional[int] = None
    interaction_type: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "event_type": "gaze",
                    "timestamp": 1727653850.125,
                    "session_id": "session_abc123",
                    "zone_name": "kitchen",
                    "gaze_target": "granite_countertop",
                    "dwell_time_ms": 2500,
                    "metadata": {"heat_level": "high"}
                },
                {
                    "event_type": "zone_enter",
                    "timestamp": 1727653855.450,
                    "session_id": "session_abc123",
                    "zone_name": "master_bedroom",
                    "position": {"x": 10.5, "y": 2.0, "z": -5.3},
                    "rotation": {"pitch": 0.0, "yaw": 90.0, "roll": 0.0}
                },
                {
                    "event_type": "interaction",
                    "timestamp": 1727653860.780,
                    "session_id": "session_abc123",
                    "zone_name": "living_room",
                    "object_name": "window_blinds",
                    "interaction_type": "click",
                    "position": {"x": 15.2, "y": 3.5, "z": -2.1}
                }
            ]
        }


class FlexibleEventData(BaseModel):
    """
    Flexible event model that accepts ANY event type from Unreal Engine.
    
    This model is designed to be maximally flexible - it only requires
    an event_type field and accepts any additional data as metadata.
    Perfect for UI events (NavBar_Click, Button_Press, etc.) that
    don't fit the structured tracking event format.
    
    Attributes:
        event_type: Required - type of event (e.g., "NavBar_Click", "Menu_Open")
        timestamp: Optional - Unix timestamp as string, int, or float
        session_id: Optional - session identifier
        **extra fields: Any additional fields are captured in model_extra
        
    Example NavBar click:
        {
            "event_type": "NavBar_Click",
            "Menu_Item": "Amenities",
            "timestamp": "1764540726"
        }
        
    Example button press:
        {
            "event_type": "Button_Press",
            "button_name": "Floor_Select",
            "floor_number": 3
        }
    """
    
    event_type: str
    timestamp: Optional[Union[str, int, float]] = None
    session_id: Optional[str] = None
    
    class Config:
        # Allow any extra fields to be captured
        extra = "allow"
        json_schema_extra = {
            "examples": [
                {
                    "event_type": "NavBar_Click",
                    "Menu_Item": "Amenities",
                    "timestamp": "1764540726"
                },
                {
                    "event_type": "Button_Press",
                    "button_name": "Floor_Select",
                    "floor_number": 3,
                    "session_id": "session_abc123"
                }
            ]
        }


class TrackingBatchFromUnreal(BaseModel):
    """
    Batch of tracking events sent together from Unreal Engine.
    
    For efficiency, Unreal Engine can send multiple events in a single
    HTTP request rather than making individual calls for each event.
    This reduces network overhead and improves performance during VR sessions.
    
    Future Enhancement:
    Currently events are sent at session end. Future versions will send
    batches continuously during the tour (e.g., every 5 seconds or 50 events).
    
    Attributes:
        session_id: Session identifier for all events in batch
        events: List of tracking events
        sent_at: Timestamp when batch was sent from Unreal
        
    Example batch:
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
    
    session_id: str
    events: List[TrackingEventFromUnreal]
    sent_at: float
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "session_abc123",
                "sent_at": 1727654100.500,
                "events": [
                    {
                        "event_type": "gaze",
                        "timestamp": 1727653850.125,
                        "zone_name": "kitchen",
                        "gaze_target": "granite_countertop",
                        "dwell_time_ms": 2500
                    },
                    {
                        "event_type": "zone_enter",
                        "timestamp": 1727653855.450,
                        "zone_name": "master_bedroom",
                        "position": {"x": 10.5, "y": 2.0, "z": -5.3}
                    },
                    {
                        "event_type": "interaction",
                        "timestamp": 1727653860.780,
                        "zone_name": "living_room",
                        "object_name": "window_blinds",
                        "interaction_type": "click"
                    }
                ]
            }
        }
