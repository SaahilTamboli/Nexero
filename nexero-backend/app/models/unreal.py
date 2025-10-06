"""
Pydantic models for Unreal Engine VR data validation.

This module defines the data structures that Unreal Engine VR client sends
to our FastAPI backend. All incoming data is validated against these models.

Data Flow:
Unreal Engine VR Tour → HTTP POST → These Models → Database Storage

Models:
- UnrealSessionData: Session start/end metadata
- TrackingEventFromUnreal: Individual tracking events (gaze, zones, interactions)
- TrackingBatchFromUnreal: Batch of multiple tracking events
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class UnrealSessionData(BaseModel):
    """
    Session metadata sent from Unreal Engine when VR tour starts/ends.
    
    This model is backward compatible with test formats where timestamps
    are sent as Unix timestamp strings. The backend will convert these
    to proper datetime objects for database storage.
    
    Attributes:
        session_start: Unix timestamp as string (e.g., "1727653800")
        session_end: Unix timestamp as string (e.g., "1727654100")
        customer_id: Optional customer identifier
        property_id: Optional property/listing identifier
        
    Example from Unreal:
        {
            "session_start": "1727653800",
            "session_end": "1727654100",
            "customer_id": "cust_12345",
            "property_id": "prop_67890"
        }
    """
    
    session_start: str  # Unix timestamp as string
    session_end: str    # Unix timestamp as string
    customer_id: Optional[str] = None
    property_id: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_start": "1727653800",
                "session_end": "1727654100",
                "customer_id": "cust_12345",
                "property_id": "prop_67890"
            }
        }


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
