"""
Dashboard and business API endpoints for Nexero frontend integration.

Mounted under /api/v1.
Unreal ingestion endpoints remain under /api/v1/unreal/*.
"""

import logging
from datetime import datetime, timedelta, timezone
from math import ceil
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.auth import get_current_user
from app.core.database import SupabaseDB
from app.models.dashboard import FollowUpCreate, FollowUpUpdate, LeadCreate, LeadUpdate, SessionCreate
from app.services.session_service import SessionService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Dashboard API"])


# -----------------------------
# Shared helpers
# -----------------------------
def get_database() -> SupabaseDB:
    return SupabaseDB()


def get_session_service(db: SupabaseDB = Depends(get_database)) -> SessionService:
    return SessionService(db)


def _safe_rows(response: Any) -> List[Dict[str, Any]]:
    if not response:
        return []
    data = getattr(response, "data", None)
    return data if isinstance(data, list) else []


def _safe_seconds(value: Optional[int]) -> int:
    return int(value or 0)


def _table_exists(db: SupabaseDB, table_name: str) -> bool:
    try:
        db.client.table(table_name).select("*", count="exact").limit(1).execute()
        return True
    except Exception:
        return False


def _parse_iso(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def _parse_period_days(period: str) -> int:
    if not period:
        return 30
    token = period.strip().lower()
    try:
        if token.endswith("d"):
            return max(1, int(token[:-1]))
        if token.endswith("w"):
            return max(1, int(token[:-1])) * 7
        if token.endswith("m"):
            return max(1, int(token[:-1])) * 30
        return max(1, int(token))
    except Exception:
        return 30


def _period_bounds(period: str) -> Tuple[datetime, datetime, int]:
    days = _parse_period_days(period)
    now = datetime.now(timezone.utc)
    current_start = now - timedelta(days=days)
    previous_start = current_start - timedelta(days=days)
    return current_start, previous_start, days


def _pct_change(current: float, previous: float) -> int:
    if previous <= 0:
        return 100 if current > 0 else 0
    return int(round(((current - previous) / previous) * 100))


def _lead_status(total_sessions: int, total_duration_seconds: int) -> str:
    if total_sessions >= 3 and total_duration_seconds >= 1200:
        return "hot"
    if total_sessions >= 2 or total_duration_seconds >= 600:
        return "warm"
    return "cold"


def _lead_score(total_sessions: int, total_duration_seconds: int) -> int:
    return min(100, int((total_sessions * 15) + (total_duration_seconds / 60)))


def _success_response(data: Any, message: Optional[str] = None) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"success": True, "data": data}
    if message:
        payload["message"] = message
    return payload


def _list_response(data: List[Dict[str, Any]], total: int, limit: int, offset: int) -> Dict[str, Any]:
    page = (offset // limit) + 1 if limit > 0 else 1
    total_pages = ceil(total / limit) if limit > 0 else 1
    return {
        "success": True,
        "data": data,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
    }


def _zone_coords(zone_name: str) -> Tuple[float, float]:
    seed = sum(ord(c) for c in zone_name)
    x = ((seed * 37) % 100) / 100.0
    y = ((seed * 53) % 100) / 100.0
    return x, y


def _resolve_customer_id(db: SupabaseDB, lead_id: str) -> Tuple[str, Optional[Dict[str, Any]]]:
    if not _table_exists(db, "customers"):
        return lead_id, None

    by_id = _safe_rows(db.client.table("customers").select("*").eq("id", lead_id).limit(1).execute())
    if by_id:
        row = by_id[0]
        return str(row.get("customer_id") or lead_id), row

    by_customer_id = _safe_rows(
        db.client.table("customers").select("*").eq("customer_id", lead_id).limit(1).execute()
    )
    if by_customer_id:
        row = by_customer_id[0]
        return str(row.get("customer_id") or lead_id), row

    return lead_id, None


def _lead_api_shape(
    customer_id: str,
    customer_row: Optional[Dict[str, Any]],
    total_sessions: int,
    total_duration_seconds: int,
    last_contact: Optional[str],
    properties_viewed: List[str],
) -> Dict[str, Any]:
    row = customer_row or {}
    computed_score = _lead_score(total_sessions, total_duration_seconds)
    computed_status = _lead_status(total_sessions, total_duration_seconds)
    now_iso = datetime.now(timezone.utc).isoformat()

    return {
        "id": str(row.get("id") or customer_id),
        "customer_id": customer_id,
        "name": row.get("name") or customer_id,
        "email": row.get("email") or "",
        "phone": row.get("phone"),
        "status": row.get("status") or computed_status,
        "score": int(row.get("score") or computed_score),
        "source": row.get("source") or "unknown",
        "last_contact": last_contact,
        "created_at": row.get("created_at") or last_contact or now_iso,
        "updated_at": row.get("updated_at") or now_iso,
        "total_sessions": total_sessions,
        "total_duration_seconds": total_duration_seconds,
        "properties_viewed": properties_viewed,
    }


def _follow_up_api_shape(row: Dict[str, Any], lead_name: Optional[str] = None) -> Dict[str, Any]:
    return {
        "id": row.get("id"),
        "lead_id": row.get("lead_id") or row.get("customer_id"),
        "lead_name": lead_name or row.get("customer_id") or "Unknown",
        "scheduled_date": row.get("scheduled_at"),
        "type": row.get("type") or "call",
        "status": row.get("status") or "pending",
        "notes": row.get("notes"),
    }


def _campaign_api_shape(row: Dict[str, Any]) -> Dict[str, Any]:
    metadata = row.get("metadata") or {}
    return {
        "id": row.get("id"),
        "name": row.get("name"),
        "status": row.get("status") or "active",
        "type": row.get("type") or row.get("source") or "campaign",
        "start_date": row.get("started_at") or row.get("created_at"),
        "end_date": row.get("ended_at"),
        "budget": row.get("budget"),
        "spent": metadata.get("spent", 0),
        "leads_generated": metadata.get("leads_generated", 0),
        "conversion_rate": metadata.get("conversion_rate", 0),
    }


# -----------------------------
# Health
# -----------------------------
@router.get("/health")
async def api_health():
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# -----------------------------
# Sessions
# -----------------------------
@router.get("/sessions/active/count")
async def get_active_sessions_count(
    db: SupabaseDB = Depends(get_database),
    user: Dict[str, Any] = Depends(get_current_user),
):
    del user
    try:
        rows = _safe_rows(db.client.table("vr_sessions").select("id").eq("status", "active").execute())
        count = len(rows)
        return _success_response({"count": count, "active_sessions": count})
    except Exception as e:
        logger.error(f"Failed to fetch active session count: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to fetch active session count", "code": "DB_ERROR"},
        )


@router.get("/sessions/stats")
async def get_session_stats(
    period: str = Query(default="30d"),
    db: SupabaseDB = Depends(get_database),
    user: Dict[str, Any] = Depends(get_current_user),
):
    del user
    try:
        current_start, _, _ = _period_bounds(period)
        rows = _safe_rows(
            db.client.table("vr_sessions")
            .select("id, customer_id, duration_seconds, status, ended_at")
            .gte("started_at", current_start.isoformat())
            .execute()
        )

        total_sessions = len(rows)
        completed_sessions = len([r for r in rows if r.get("status") == "completed" or r.get("ended_at")])
        total_duration = sum(_safe_seconds(r.get("duration_seconds")) for r in rows)
        unique_customers = len({r.get("customer_id") for r in rows if r.get("customer_id")})

        return _success_response(
            {
                "period": period,
                "total_sessions": total_sessions,
                "completed_sessions": completed_sessions,
                "avg_duration_seconds": int(total_duration / total_sessions) if total_sessions else 0,
                "unique_customers": unique_customers,
            }
        )
    except Exception as e:
        logger.error(f"Failed to fetch session stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to fetch session stats", "code": "DB_ERROR"},
        )


@router.get("/sessions")
async def list_sessions(
    status_filter: Optional[str] = Query(default=None, alias="status"),
    customer_id: Optional[str] = None,
    property_id: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: SupabaseDB = Depends(get_database),
    user: Dict[str, Any] = Depends(get_current_user),
):
    del user
    try:
        query = db.client.table("vr_sessions").select("*", count="exact")
        if status_filter:
            query = query.eq("status", status_filter)
        if customer_id:
            query = query.eq("customer_id", customer_id)
        if property_id:
            query = query.eq("property_id", property_id)
        if date_from:
            query = query.gte("started_at", date_from)
        if date_to:
            query = query.lte("started_at", date_to)

        response = query.order("started_at", desc=True).range(offset, offset + limit - 1).execute()
        rows = _safe_rows(response)
        total = int(getattr(response, "count", len(rows)) or len(rows))
        return _list_response(rows, total=total, limit=limit, offset=offset)
    except Exception as e:
        logger.error(f"Failed to list sessions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to list sessions", "code": "DB_ERROR"},
        )


@router.post("/sessions", status_code=status.HTTP_201_CREATED)
async def create_session(
    payload: SessionCreate,
    session_service: SessionService = Depends(get_session_service),
    user: Dict[str, Any] = Depends(get_current_user),
):
    del user
    try:
        session = await session_service.process_unreal_session_data(
            session_start=payload.session_start,
            session_end=payload.session_end,
            customer_id=payload.customer_id,
            property_id=payload.property_id,
        )
        return _success_response(session)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": str(e), "code": "VALIDATION_ERROR"},
        )
    except Exception as e:
        logger.error(f"Failed to create session: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to create session", "code": "DB_ERROR"},
        )


@router.get("/sessions/{session_id}/events")
async def get_session_events(
    session_id: str,
    event_type: Optional[str] = None,
    limit: int = Query(default=200, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: SupabaseDB = Depends(get_database),
    user: Dict[str, Any] = Depends(get_current_user),
):
    del user
    try:
        query = db.client.table("tracking_events").select("*", count="exact").eq("session_id", session_id)
        if event_type:
            query = query.eq("event_type", event_type)

        response = query.order("timestamp", desc=False).range(offset, offset + limit - 1).execute()
        rows = _safe_rows(response)
        total = int(getattr(response, "count", len(rows)) or len(rows))
        return _list_response(rows, total=total, limit=limit, offset=offset)
    except Exception as e:
        logger.error(f"Failed to fetch events for session {session_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to fetch session events", "code": "DB_ERROR"},
        )


@router.get("/sessions/{session_id}/poi-visits")
async def get_session_poi_visits(
    session_id: str,
    limit: int = Query(default=200, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: SupabaseDB = Depends(get_database),
    user: Dict[str, Any] = Depends(get_current_user),
):
    del user
    try:
        response = (
            db.client.table("poi_visits")
            .select("*", count="exact")
            .eq("session_id", session_id)
            .order("received_at", desc=False)
            .range(offset, offset + limit - 1)
            .execute()
        )
        rows = _safe_rows(response)
        total = int(getattr(response, "count", len(rows)) or len(rows))
        return _list_response(rows, total=total, limit=limit, offset=offset)
    except Exception as e:
        logger.error(f"Failed to fetch poi visits for session {session_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to fetch session POI visits", "code": "DB_ERROR"},
        )


@router.get("/sessions/{session_id}")
async def get_session_details(
    session_id: str,
    db: SupabaseDB = Depends(get_database),
    user: Dict[str, Any] = Depends(get_current_user),
):
    del user
    try:
        session_rows = _safe_rows(db.client.table("vr_sessions").select("*").eq("id", session_id).limit(1).execute())
        if not session_rows:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "Session not found", "code": "NOT_FOUND"},
            )

        events = _safe_rows(
            db.client.table("tracking_events").select("*").eq("session_id", session_id).order("timestamp", desc=False).execute()
        )
        poi_visits = _safe_rows(
            db.client.table("poi_visits").select("*").eq("session_id", session_id).order("received_at", desc=False).execute()
        )
        view_events = _safe_rows(
            db.client.table("view_events").select("*").eq("session_id", session_id).order("received_at", desc=False).execute()
        )

        return _success_response(
            {
                **session_rows[0],
                "tracking_events": events,
                "poi_visits": poi_visits,
                "view_events": view_events,
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch session details for {session_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to fetch session details", "code": "DB_ERROR"},
        )


# -----------------------------
# Leads
# -----------------------------
@router.get("/leads")
async def list_leads(
    status_filter: Optional[str] = Query(default=None, alias="status"),
    source: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = Query(default="score"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: SupabaseDB = Depends(get_database),
    user: Dict[str, Any] = Depends(get_current_user),
):
    del user
    try:
        customer_map: Dict[str, Dict[str, Any]] = {}
        if _table_exists(db, "customers"):
            for row in _safe_rows(db.client.table("customers").select("*").execute()):
                key = str(row.get("customer_id") or "")
                if key:
                    customer_map[key] = row

        sessions = _safe_rows(
            db.client.table("vr_sessions")
            .select("customer_id, property_id, duration_seconds, started_at")
            .order("started_at", desc=True)
            .limit(10000)
            .execute()
        )

        metrics: Dict[str, Dict[str, Any]] = {}
        for row in sessions:
            customer_id = row.get("customer_id")
            if not customer_id:
                continue
            key = str(customer_id)
            item = metrics.setdefault(
                key,
                {
                    "total_sessions": 0,
                    "total_duration_seconds": 0,
                    "last_contact": row.get("started_at"),
                    "properties_viewed": set(),
                },
            )
            item["total_sessions"] += 1
            item["total_duration_seconds"] += _safe_seconds(row.get("duration_seconds"))
            if row.get("property_id"):
                item["properties_viewed"].add(row.get("property_id"))

            current_last = _parse_iso(item.get("last_contact"))
            incoming = _parse_iso(row.get("started_at"))
            if incoming and (not current_last or incoming > current_last):
                item["last_contact"] = row.get("started_at")

        for key in customer_map.keys():
            metrics.setdefault(
                key,
                {
                    "total_sessions": 0,
                    "total_duration_seconds": 0,
                    "last_contact": None,
                    "properties_viewed": set(),
                },
            )

        leads: List[Dict[str, Any]] = []
        for key, metric in metrics.items():
            leads.append(
                _lead_api_shape(
                    customer_id=key,
                    customer_row=customer_map.get(key),
                    total_sessions=metric["total_sessions"],
                    total_duration_seconds=metric["total_duration_seconds"],
                    last_contact=metric.get("last_contact"),
                    properties_viewed=sorted(list(metric["properties_viewed"])),
                )
            )

        if status_filter:
            leads = [l for l in leads if l.get("status") == status_filter]
        if source:
            leads = [l for l in leads if l.get("source") == source]
        if search:
            term = search.lower()
            leads = [
                l for l in leads
                if term in (l.get("name") or "").lower()
                or term in (l.get("email") or "").lower()
                or term in (l.get("phone") or "").lower()
                or term in (l.get("customer_id") or "").lower()
            ]

        allowed_sort = {
            "score": "score",
            "last_contact": "last_contact",
            "total_duration_seconds": "total_duration_seconds",
            "total_sessions": "total_sessions",
            "created_at": "created_at",
            "name": "name",
        }
        sort_column = allowed_sort.get(sort_by, "score")
        leads.sort(key=lambda l: l.get(sort_column) or 0, reverse=True)

        total = len(leads)
        return _list_response(leads[offset: offset + limit], total=total, limit=limit, offset=offset)
    except Exception as e:
        logger.error(f"Failed to list leads: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to list leads", "code": "DB_ERROR"},
        )


@router.post("/leads", status_code=status.HTTP_201_CREATED)
async def create_lead(
    payload: LeadCreate,
    db: SupabaseDB = Depends(get_database),
    user: Dict[str, Any] = Depends(get_current_user),
):
    del user
    if not _table_exists(db, "customers"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"message": "customers table is missing. Run migration 002.", "code": "MIGRATION_REQUIRED"},
        )

    try:
        response = db.client.table("customers").insert(payload.model_dump()).execute()
        rows = _safe_rows(response)
        if not rows:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"message": "Failed to create lead", "code": "DB_ERROR"},
            )

        row = rows[0]
        lead = _lead_api_shape(
            customer_id=str(row.get("customer_id")),
            customer_row=row,
            total_sessions=0,
            total_duration_seconds=0,
            last_contact=None,
            properties_viewed=[],
        )
        return _success_response(lead)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create lead: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to create lead", "code": "DB_ERROR"},
        )


@router.get("/leads/{lead_id}")
async def get_lead_details(
    lead_id: str,
    db: SupabaseDB = Depends(get_database),
    user: Dict[str, Any] = Depends(get_current_user),
):
    del user
    try:
        customer_id, customer_row = _resolve_customer_id(db, lead_id)

        sessions = _safe_rows(
            db.client.table("vr_sessions")
            .select("id, started_at, ended_at, duration_seconds, customer_id, property_id, status, created_at, updated_at")
            .eq("customer_id", customer_id)
            .order("started_at", desc=True)
            .execute()
        )

        if not sessions and not customer_row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "Lead not found", "code": "NOT_FOUND"},
            )

        session_ids = [row.get("id") for row in sessions if row.get("id")]
        poi_visits: List[Dict[str, Any]] = []
        tracking_events: List[Dict[str, Any]] = []

        if session_ids:
            poi_visits = _safe_rows(
                db.client.table("poi_visits").select("*").in_("session_id", session_ids).order("received_at", desc=False).execute()
            )
            tracking_events = _safe_rows(
                db.client.table("tracking_events").select("*").in_("session_id", session_ids).order("timestamp", desc=False).execute()
            )

        total_duration = sum(_safe_seconds(s.get("duration_seconds")) for s in sessions)
        total_sessions = len(sessions)
        last_contact = sessions[0].get("started_at") if sessions else (customer_row or {}).get("updated_at")
        properties_viewed = sorted(list({s.get("property_id") for s in sessions if s.get("property_id")}))

        lead_base = _lead_api_shape(
            customer_id=customer_id,
            customer_row=customer_row,
            total_sessions=total_sessions,
            total_duration_seconds=total_duration,
            last_contact=last_contact,
            properties_viewed=properties_viewed,
        )

        zone_names = sorted(list({e.get("zone_name") for e in tracking_events if e.get("zone_name")}))
        intent_score = int(lead_base["score"])

        lead_detail = {
            **lead_base,
            "budget_min": None,
            "budget_max": None,
            "sales_prompt": None,
            "intent_score": intent_score,
            "area_of_interest": zone_names,
            "journey_stage": "intent" if intent_score >= 80 else ("consideration" if intent_score >= 60 else "interest"),
            "assigned_agent": None,
            "follow_up_date": None,
            "sessions": sessions,
            "poi_visits": poi_visits,
            "tracking_events": tracking_events,
        }
        return _success_response(lead_detail)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch lead details for {lead_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to fetch lead details", "code": "DB_ERROR"},
        )


@router.patch("/leads/{lead_id}")
async def update_lead(
    lead_id: str,
    payload: LeadUpdate,
    db: SupabaseDB = Depends(get_database),
    user: Dict[str, Any] = Depends(get_current_user),
):
    del user
    if not _table_exists(db, "customers"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"message": "customers table is missing. Run migration 002.", "code": "MIGRATION_REQUIRED"},
        )

    try:
        updates = payload.model_dump(exclude_none=True)
        if not updates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "No fields to update", "code": "VALIDATION_ERROR"},
            )
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()

        response = db.client.table("customers").update(updates).eq("id", lead_id).execute()
        rows = _safe_rows(response)
        if not rows:
            response = db.client.table("customers").update(updates).eq("customer_id", lead_id).execute()
            rows = _safe_rows(response)

        if not rows:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "Lead not found", "code": "NOT_FOUND"},
            )

        row = rows[0]
        lead = _lead_api_shape(
            customer_id=str(row.get("customer_id")),
            customer_row=row,
            total_sessions=0,
            total_duration_seconds=0,
            last_contact=row.get("updated_at"),
            properties_viewed=[],
        )
        return _success_response(lead)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update lead {lead_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to update lead", "code": "DB_ERROR"},
        )


@router.get("/leads/{lead_id}/sessions")
async def get_lead_sessions(
    lead_id: str,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: SupabaseDB = Depends(get_database),
    user: Dict[str, Any] = Depends(get_current_user),
):
    del user
    try:
        customer_id, _ = _resolve_customer_id(db, lead_id)
        response = (
            db.client.table("vr_sessions")
            .select("*", count="exact")
            .eq("customer_id", customer_id)
            .order("started_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )
        rows = _safe_rows(response)
        total = int(getattr(response, "count", len(rows)) or len(rows))
        return _list_response(rows, total=total, limit=limit, offset=offset)
    except Exception as e:
        logger.error(f"Failed to fetch lead sessions for {lead_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to fetch lead sessions", "code": "DB_ERROR"},
        )


@router.get("/leads/{lead_id}/engagement")
async def get_lead_engagement(
    lead_id: str,
    db: SupabaseDB = Depends(get_database),
    user: Dict[str, Any] = Depends(get_current_user),
):
    del user
    try:
        customer_id, _ = _resolve_customer_id(db, lead_id)

        sessions = _safe_rows(db.client.table("vr_sessions").select("id, duration_seconds").eq("customer_id", customer_id).execute())
        session_ids = [row.get("id") for row in sessions if row.get("id")]
        total_duration = sum(_safe_seconds(s.get("duration_seconds")) for s in sessions)

        if not session_ids:
            return _success_response(
                {
                    "total_sessions": 0,
                    "total_duration_seconds": 0,
                    "zones_visited": 0,
                    "pois_viewed": 0,
                    "intent_score": 0,
                    "zone_breakdown": [],
                }
            )

        events = _safe_rows(
            db.client.table("tracking_events")
            .select("zone_name, dwell_time_ms, event_type")
            .in_("session_id", session_ids)
            .execute()
        )

        zone_map: Dict[str, Dict[str, Any]] = {}
        for row in events:
            zone_name = row.get("zone_name") or "unknown"
            item = zone_map.setdefault(zone_name, {"zone_name": zone_name, "visits": 0, "total_dwell_time_ms": 0})
            item["visits"] += 1
            item["total_dwell_time_ms"] += int(row.get("dwell_time_ms") or 0)

        zone_breakdown = []
        for item in zone_map.values():
            avg = int(item["total_dwell_time_ms"] / item["visits"]) if item["visits"] else 0
            zone_breakdown.append(
                {
                    "zone_name": item["zone_name"],
                    "visits": item["visits"],
                    "total_dwell_time_ms": item["total_dwell_time_ms"],
                    "avg_dwell_time_ms": avg,
                }
            )

        zone_breakdown.sort(key=lambda x: x["visits"], reverse=True)

        poi_count = len(
            _safe_rows(db.client.table("poi_visits").select("id").in_("session_id", session_ids).execute())
        )

        return _success_response(
            {
                "total_sessions": len(session_ids),
                "total_duration_seconds": total_duration,
                "zones_visited": len(zone_breakdown),
                "pois_viewed": poi_count,
                "intent_score": _lead_score(len(session_ids), total_duration),
                "zone_breakdown": zone_breakdown,
            }
        )
    except Exception as e:
        logger.error(f"Failed to fetch lead engagement for {lead_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to fetch lead engagement", "code": "DB_ERROR"},
        )


# -----------------------------
# Analytics
# -----------------------------
@router.get("/analytics/dashboard")
async def analytics_dashboard(
    period: str = Query(default="30d"),
    db: SupabaseDB = Depends(get_database),
    user: Dict[str, Any] = Depends(get_current_user),
):
    del user
    try:
        current_start, previous_start, days = _period_bounds(period)

        current_sessions = _safe_rows(
            db.client.table("vr_sessions")
            .select("customer_id, duration_seconds")
            .gte("started_at", current_start.isoformat())
            .execute()
        )
        previous_sessions = _safe_rows(
            db.client.table("vr_sessions")
            .select("customer_id, duration_seconds")
            .gte("started_at", previous_start.isoformat())
            .lt("started_at", current_start.isoformat())
            .execute()
        )

        current_views = len(
            _safe_rows(
                db.client.table("view_events")
                .select("id")
                .gte("received_at", current_start.isoformat())
                .execute()
            )
        )
        previous_views = len(
            _safe_rows(
                db.client.table("view_events")
                .select("id")
                .gte("received_at", previous_start.isoformat())
                .lt("received_at", current_start.isoformat())
                .execute()
            )
        )

        active_sessions = len(_safe_rows(db.client.table("vr_sessions").select("id").eq("status", "active").execute()))

        current_total_sessions = len(current_sessions)
        previous_total_sessions = len(previous_sessions)

        current_unique = len({r.get("customer_id") for r in current_sessions if r.get("customer_id")})
        previous_unique = len({r.get("customer_id") for r in previous_sessions if r.get("customer_id")})

        current_total_duration = sum(_safe_seconds(r.get("duration_seconds")) for r in current_sessions)
        previous_total_duration = sum(_safe_seconds(r.get("duration_seconds")) for r in previous_sessions)

        current_high_intent = len([r for r in current_sessions if _safe_seconds(r.get("duration_seconds")) >= 600])
        previous_high_intent = len([r for r in previous_sessions if _safe_seconds(r.get("duration_seconds")) >= 600])

        conversion_current = (current_high_intent / current_total_sessions * 100.0) if current_total_sessions else 0.0
        conversion_previous = (previous_high_intent / previous_total_sessions * 100.0) if previous_total_sessions else 0.0

        avg_engagement_current = (current_total_duration / current_total_sessions) if current_total_sessions else 0.0
        avg_engagement_previous = (previous_total_duration / previous_total_sessions) if previous_total_sessions else 0.0

        data = {
            "total_leads": current_unique,
            "leads_change": _pct_change(current_unique, previous_unique),
            "total_views": current_views,
            "views_change": _pct_change(current_views, previous_views),
            "active_sessions": active_sessions,
            "sessions_change": _pct_change(current_total_sessions, previous_total_sessions),
            "conversion_rate": round(conversion_current, 2),
            "conversion_change": _pct_change(conversion_current, conversion_previous),
            "avg_engagement_time": round(avg_engagement_current, 2),
            "engagement_change": _pct_change(avg_engagement_current, avg_engagement_previous),
            "period": period,
            "period_days": days,
        }
        return _success_response(data)
    except Exception as e:
        logger.error(f"Failed to fetch dashboard analytics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to fetch dashboard analytics", "code": "DB_ERROR"},
        )


@router.get("/analytics/views")
async def analytics_views(
    period: str = Query(default="30d"),
    view_name: Optional[str] = None,
    db: SupabaseDB = Depends(get_database),
    user: Dict[str, Any] = Depends(get_current_user),
):
    del user
    try:
        current_start, _, _ = _period_bounds(period)
        query = db.client.table("view_events").select("view_name, duration_seconds, received_at").gte("received_at", current_start.isoformat())
        if view_name:
            query = query.eq("view_name", view_name)

        rows = _safe_rows(query.execute())
        agg: Dict[str, Dict[str, Any]] = {}
        for row in rows:
            key = row.get("view_name") or "unknown"
            item = agg.setdefault(key, {"view_name": key, "view_count": 0, "total_duration": 0})
            item["view_count"] += 1
            item["total_duration"] += _safe_seconds(row.get("duration_seconds"))

        data = []
        for item in agg.values():
            avg = int(item["total_duration"] / item["view_count"]) if item["view_count"] else 0
            data.append(
                {
                    "view_name": item["view_name"],
                    "view_count": item["view_count"],
                    "avg_duration": avg,
                    "total_duration": item["total_duration"],
                }
            )

        data.sort(key=lambda x: x["view_count"], reverse=True)
        return _success_response(data)
    except Exception as e:
        logger.error(f"Failed to fetch view analytics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to fetch view analytics", "code": "DB_ERROR"},
        )


@router.get("/analytics/poi")
async def analytics_poi(
    period: str = Query(default="30d"),
    parent_zone: Optional[str] = None,
    db: SupabaseDB = Depends(get_database),
    user: Dict[str, Any] = Depends(get_current_user),
):
    del user
    try:
        current_start, _, _ = _period_bounds(period)
        query = db.client.table("poi_visits").select("poi_name, parent_zone, duration_seconds, received_at").gte("received_at", current_start.isoformat())
        if parent_zone:
            query = query.eq("parent_zone", parent_zone)

        rows = _safe_rows(query.execute())
        agg: Dict[str, Dict[str, Any]] = {}

        for row in rows:
            poi_name = row.get("poi_name") or "unknown"
            zone = row.get("parent_zone") or "unknown"
            key = f"{zone}::{poi_name}"
            item = agg.setdefault(
                key,
                {
                    "poi_name": poi_name,
                    "parent_zone": zone,
                    "total_visits": 0,
                    "total_duration_seconds": 0,
                },
            )
            item["total_visits"] += 1
            item["total_duration_seconds"] += _safe_seconds(row.get("duration_seconds"))

        data = []
        for item in agg.values():
            avg_seconds = int(item["total_duration_seconds"] / item["total_visits"]) if item["total_visits"] else 0
            data.append(
                {
                    "poi_name": item["poi_name"],
                    "parent_zone": item["parent_zone"],
                    "total_visits": item["total_visits"],
                    "total_duration_seconds": item["total_duration_seconds"],
                    "avg_duration_seconds": avg_seconds,
                }
            )

        data.sort(key=lambda x: x["total_visits"], reverse=True)
        return _success_response(data)
    except Exception as e:
        logger.error(f"Failed to fetch POI analytics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to fetch POI analytics", "code": "DB_ERROR"},
        )


@router.get("/analytics/zones")
async def analytics_zones(
    period: str = Query(default="30d"),
    property_id: Optional[str] = None,
    db: SupabaseDB = Depends(get_database),
    user: Dict[str, Any] = Depends(get_current_user),
):
    del user
    try:
        current_start, _, _ = _period_bounds(period)

        session_ids: Optional[List[str]] = None
        if property_id:
            sessions = _safe_rows(db.client.table("vr_sessions").select("id").eq("property_id", property_id).execute())
            session_ids = [row.get("id") for row in sessions if row.get("id")]
            if not session_ids:
                return _success_response([])

        query = db.client.table("tracking_events").select("zone_name, event_type, dwell_time_ms, session_id, timestamp").gte("timestamp", current_start.isoformat())
        if session_ids is not None:
            query = query.in_("session_id", session_ids)

        rows = _safe_rows(query.execute())

        agg: Dict[str, Dict[str, Any]] = {}
        for row in rows:
            zone = row.get("zone_name") or "unknown"
            item = agg.setdefault(
                zone,
                {
                    "zone_name": zone,
                    "total_visits": 0,
                    "entry_count": 0,
                    "exit_count": 0,
                    "total_dwell_time_ms": 0,
                    "dwell_count": 0,
                },
            )

            item["total_visits"] += 1
            event_type = row.get("event_type")
            if event_type == "zone_enter":
                item["entry_count"] += 1
            elif event_type == "zone_exit":
                item["exit_count"] += 1

            dwell = int(row.get("dwell_time_ms") or 0)
            if dwell > 0:
                item["total_dwell_time_ms"] += dwell
                item["dwell_count"] += 1

        data = []
        for item in agg.values():
            avg_dwell = int(item["total_dwell_time_ms"] / item["dwell_count"]) if item["dwell_count"] else 0
            data.append(
                {
                    "zone_name": item["zone_name"],
                    "total_visits": item["total_visits"],
                    "total_dwell_time_ms": item["total_dwell_time_ms"],
                    "avg_dwell_time_ms": avg_dwell,
                    "entry_count": item["entry_count"],
                    "exit_count": item["exit_count"],
                }
            )

        data.sort(key=lambda x: x["total_visits"], reverse=True)
        return _success_response(data)
    except Exception as e:
        logger.error(f"Failed to fetch zone analytics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to fetch zone analytics", "code": "DB_ERROR"},
        )


@router.get("/analytics/heatmap/{property_id}")
async def analytics_heatmap(
    property_id: str,
    floor: Optional[str] = None,
    db: SupabaseDB = Depends(get_database),
    user: Dict[str, Any] = Depends(get_current_user),
):
    del user
    del floor
    try:
        sessions = _safe_rows(db.client.table("vr_sessions").select("id").eq("property_id", property_id).execute())
        session_ids = [row.get("id") for row in sessions if row.get("id")]
        if not session_ids:
            return _success_response([])

        rows = _safe_rows(
            db.client.table("tracking_events").select("zone_name, event_type, dwell_time_ms").in_("session_id", session_ids).execute()
        )

        agg: Dict[str, Dict[str, Any]] = {}
        for row in rows:
            zone = row.get("zone_name") or "unknown"
            item = agg.setdefault(zone, {"zone_name": zone, "total_visits": 0, "dwell_sum": 0})
            item["total_visits"] += 1
            item["dwell_sum"] += int(row.get("dwell_time_ms") or 0)

        max_visits = max((item["total_visits"] for item in agg.values()), default=1)
        data = []
        for item in agg.values():
            intensity = round(item["total_visits"] / max_visits, 2) if max_visits else 0.0
            avg_seconds = round((item["dwell_sum"] / item["total_visits"]) / 1000.0, 2) if item["total_visits"] else 0.0
            x, y = _zone_coords(item["zone_name"])
            data.append(
                {
                    "zone_name": item["zone_name"],
                    "x": x,
                    "y": y,
                    "radius": round(0.06 + intensity * 0.14, 2),
                    "intensity": intensity,
                    "total_visits": item["total_visits"],
                    "avg_duration_seconds": avg_seconds,
                }
            )

        data.sort(key=lambda x: x["total_visits"], reverse=True)
        return _success_response(data)
    except Exception as e:
        logger.error(f"Failed to fetch heatmap analytics for {property_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to fetch heatmap analytics", "code": "DB_ERROR"},
        )


@router.get("/analytics/engagement")
@router.get("/analytics/engagement-trends")
async def analytics_engagement_trends(
    period: str = Query(default="30d"),
    db: SupabaseDB = Depends(get_database),
    user: Dict[str, Any] = Depends(get_current_user),
):
    del user
    try:
        current_start, _, _ = _period_bounds(period)
        rows = _safe_rows(
            db.client.table("vr_sessions")
            .select("started_at, duration_seconds")
            .gte("started_at", current_start.isoformat())
            .order("started_at", desc=False)
            .execute()
        )

        daily: Dict[str, Dict[str, Any]] = {}
        for row in rows:
            stamp = row.get("started_at")
            day = (stamp or "")[:10] if stamp else "unknown"
            item = daily.setdefault(day, {"date": day, "session_count": 0, "duration_sum": 0})
            item["session_count"] += 1
            item["duration_sum"] += _safe_seconds(row.get("duration_seconds"))

        data = []
        for item in daily.values():
            avg = int(item["duration_sum"] / item["session_count"]) if item["session_count"] else 0
            data.append(
                {
                    "name": item["date"],
                    "date": item["date"],
                    "value": item["session_count"],
                    "session_count": item["session_count"],
                    "avg_duration": avg,
                }
            )

        data.sort(key=lambda x: x["date"])
        return _success_response(data)
    except Exception as e:
        logger.error(f"Failed to fetch engagement trends: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to fetch engagement trends", "code": "DB_ERROR"},
        )


@router.get("/analytics/geo")
@router.get("/analytics/geo-distribution")
async def analytics_geo_distribution(
    db: SupabaseDB = Depends(get_database),
    user: Dict[str, Any] = Depends(get_current_user),
):
    del user
    try:
        if not _table_exists(db, "customers"):
            return _success_response([])

        rows = _safe_rows(db.client.table("customers").select("city, state, country").execute())
        counts: Dict[str, int] = {}
        for row in rows:
            city = row.get("city") or "Unknown"
            state = row.get("state") or "Unknown"
            country = row.get("country") or "Unknown"
            key = f"{city}, {state}, {country}"
            counts[key] = counts.get(key, 0) + 1

        total = sum(counts.values())
        data = [
            {
                "location": location,
                "count": count,
                "percentage": round((count / total) * 100, 2) if total > 0 else 0.0,
            }
            for location, count in counts.items()
        ]
        data.sort(key=lambda x: x["count"], reverse=True)
        return _success_response(data)
    except Exception as e:
        logger.error(f"Failed to fetch geo distribution: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to fetch geo distribution", "code": "DB_ERROR"},
        )


@router.get("/analytics/funnel")
async def analytics_funnel(
    period: str = Query(default="30d"),
    db: SupabaseDB = Depends(get_database),
    user: Dict[str, Any] = Depends(get_current_user),
):
    del user
    try:
        current_start, _, _ = _period_bounds(period)
        sessions = _safe_rows(
            db.client.table("vr_sessions").select("id, duration_seconds").gte("started_at", current_start.isoformat()).execute()
        )

        total_sessions = len(sessions)
        engaged = len([s for s in sessions if _safe_seconds(s.get("duration_seconds")) >= 180])
        high_intent = len([s for s in sessions if _safe_seconds(s.get("duration_seconds")) >= 600])

        follow_up_scheduled = 0
        if _table_exists(db, "follow_ups"):
            follow_up_scheduled = len(
                _safe_rows(
                    db.client.table("follow_ups")
                    .select("id")
                    .in_("status", ["pending", "completed"])
                    .gte("created_at", current_start.isoformat())
                    .execute()
                )
            )

        data = [
            {"name": "Sessions", "value": total_sessions},
            {"name": "Engaged", "value": engaged},
            {"name": "High Intent", "value": high_intent},
            {"name": "Follow Up Scheduled", "value": follow_up_scheduled},
        ]
        return _success_response(data)
    except Exception as e:
        logger.error(f"Failed to fetch funnel analytics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to fetch funnel analytics", "code": "DB_ERROR"},
        )


# -----------------------------
# Properties
# -----------------------------
@router.get("/properties")
async def list_properties(
    status_filter: Optional[str] = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: SupabaseDB = Depends(get_database),
    user: Dict[str, Any] = Depends(get_current_user),
):
    del user
    try:
        if _table_exists(db, "properties"):
            query = db.client.table("properties").select("*", count="exact")
            if status_filter:
                query = query.eq("status", status_filter)
            response = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()
            rows = _safe_rows(response)
            total = int(getattr(response, "count", len(rows)) or len(rows))
            return _list_response(rows, total=total, limit=limit, offset=offset)

        sessions = _safe_rows(db.client.table("vr_sessions").select("property_id").execute())
        unique_props = sorted(list({r.get("property_id") for r in sessions if r.get("property_id")}))
        fallback = [{"id": p, "property_id": p, "name": p, "status": "active"} for p in unique_props]
        return _list_response(fallback[offset: offset + limit], total=len(fallback), limit=limit, offset=offset)
    except Exception as e:
        logger.error(f"Failed to list properties: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to list properties", "code": "DB_ERROR"},
        )


@router.get("/properties/{property_id}")
async def get_property(
    property_id: str,
    db: SupabaseDB = Depends(get_database),
    user: Dict[str, Any] = Depends(get_current_user),
):
    del user
    try:
        if _table_exists(db, "properties"):
            rows = _safe_rows(db.client.table("properties").select("*").eq("id", property_id).limit(1).execute())
            if not rows:
                rows = _safe_rows(
                    db.client.table("properties").select("*").eq("property_id", property_id).limit(1).execute()
                )
            if rows:
                return _success_response(rows[0])

        probe = _safe_rows(
            db.client.table("vr_sessions").select("id").eq("property_id", property_id).limit(1).execute()
        )
        if probe:
            return _success_response({"id": property_id, "property_id": property_id, "name": property_id, "status": "active"})

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": "Property not found", "code": "NOT_FOUND"},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch property {property_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to fetch property", "code": "DB_ERROR"},
        )


@router.get("/properties/{property_id}/analytics")
async def get_property_analytics(
    property_id: str,
    period: str = Query(default="30d"),
    db: SupabaseDB = Depends(get_database),
    user: Dict[str, Any] = Depends(get_current_user),
):
    del user
    try:
        current_start, _, _ = _period_bounds(period)

        sessions = _safe_rows(
            db.client.table("vr_sessions")
            .select("id, customer_id, duration_seconds")
            .eq("property_id", property_id)
            .gte("started_at", current_start.isoformat())
            .execute()
        )

        session_ids = [row.get("id") for row in sessions if row.get("id")]
        total_sessions = len(sessions)
        total_duration = sum(_safe_seconds(item.get("duration_seconds")) for item in sessions)
        unique_visitors = len({item.get("customer_id") for item in sessions if item.get("customer_id")})

        zone_analytics: List[Dict[str, Any]] = []
        poi_analytics: List[Dict[str, Any]] = []

        if session_ids:
            zone_rows = _safe_rows(
                db.client.table("tracking_events")
                .select("zone_name, event_type, dwell_time_ms")
                .in_("session_id", session_ids)
                .execute()
            )
            zone_map: Dict[str, Dict[str, Any]] = {}
            for row in zone_rows:
                zone = row.get("zone_name") or "unknown"
                item = zone_map.setdefault(
                    zone,
                    {
                        "zone_name": zone,
                        "total_visits": 0,
                        "total_dwell_time_ms": 0,
                        "entry_count": 0,
                        "exit_count": 0,
                    },
                )
                item["total_visits"] += 1
                item["total_dwell_time_ms"] += int(row.get("dwell_time_ms") or 0)
                if row.get("event_type") == "zone_enter":
                    item["entry_count"] += 1
                elif row.get("event_type") == "zone_exit":
                    item["exit_count"] += 1

            for item in zone_map.values():
                avg_ms = int(item["total_dwell_time_ms"] / item["total_visits"]) if item["total_visits"] else 0
                zone_analytics.append(
                    {
                        "zone_name": item["zone_name"],
                        "total_visits": item["total_visits"],
                        "total_dwell_time_ms": item["total_dwell_time_ms"],
                        "avg_dwell_time_ms": avg_ms,
                        "entry_count": item["entry_count"],
                        "exit_count": item["exit_count"],
                    }
                )

            poi_rows = _safe_rows(
                db.client.table("poi_visits")
                .select("poi_name, parent_zone, duration_seconds")
                .in_("session_id", session_ids)
                .execute()
            )
            poi_map: Dict[str, Dict[str, Any]] = {}
            for row in poi_rows:
                poi = row.get("poi_name") or "unknown"
                zone = row.get("parent_zone") or "unknown"
                key = f"{zone}::{poi}"
                item = poi_map.setdefault(
                    key,
                    {
                        "poi_name": poi,
                        "parent_zone": zone,
                        "total_visits": 0,
                        "total_duration_seconds": 0,
                    },
                )
                item["total_visits"] += 1
                item["total_duration_seconds"] += _safe_seconds(row.get("duration_seconds"))

            for item in poi_map.values():
                avg_sec = int(item["total_duration_seconds"] / item["total_visits"]) if item["total_visits"] else 0
                poi_analytics.append(
                    {
                        "poi_name": item["poi_name"],
                        "parent_zone": item["parent_zone"],
                        "total_visits": item["total_visits"],
                        "total_duration_seconds": item["total_duration_seconds"],
                        "avg_duration_seconds": avg_sec,
                    }
                )

        property_name = property_id
        if _table_exists(db, "properties"):
            rows = _safe_rows(
                db.client.table("properties")
                .select("name")
                .or_(f"id.eq.{property_id},property_id.eq.{property_id}")
                .limit(1)
                .execute()
            )
            if rows:
                property_name = rows[0].get("name") or property_id

        return _success_response(
            {
                "property_id": property_id,
                "property_name": property_name,
                "total_sessions": total_sessions,
                "unique_visitors": unique_visitors,
                "total_duration_seconds": total_duration,
                "avg_session_duration": int(total_duration / total_sessions) if total_sessions else 0,
                "zone_analytics": sorted(zone_analytics, key=lambda x: x["total_visits"], reverse=True),
                "poi_analytics": sorted(poi_analytics, key=lambda x: x["total_visits"], reverse=True),
            }
        )
    except Exception as e:
        logger.error(f"Failed to fetch property analytics for {property_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to fetch property analytics", "code": "DB_ERROR"},
        )


# -----------------------------
# Follow-ups
# -----------------------------
@router.get("/follow-ups/summary")
async def get_follow_up_summary(
    db: SupabaseDB = Depends(get_database),
    user: Dict[str, Any] = Depends(get_current_user),
):
    del user
    if not _table_exists(db, "follow_ups"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"message": "follow_ups table is missing. Run migration 002.", "code": "MIGRATION_REQUIRED"},
        )

    try:
        now = datetime.now(timezone.utc)
        today = now.date()
        tomorrow = today + timedelta(days=1)
        week_end = today + timedelta(days=7)
        next_week_end = today + timedelta(days=14)

        rows = _safe_rows(
            db.client.table("follow_ups")
            .select("scheduled_at, status")
            .eq("status", "pending")
            .execute()
        )

        result = {"today": 0, "tomorrow": 0, "this_week": 0, "next_week": 0, "total": 0}
        for row in rows:
            stamp = _parse_iso(row.get("scheduled_at"))
            if not stamp:
                continue
            d = stamp.date()
            result["total"] += 1
            if d == today:
                result["today"] += 1
            if d == tomorrow:
                result["tomorrow"] += 1
            if today <= d <= week_end:
                result["this_week"] += 1
            if week_end < d <= next_week_end:
                result["next_week"] += 1

        return _success_response(result)
    except Exception as e:
        logger.error(f"Failed to fetch follow-up summary: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to fetch follow-up summary", "code": "DB_ERROR"},
        )


@router.get("/follow-ups")
async def list_follow_ups(
    status_filter: Optional[str] = Query(default=None, alias="status"),
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: SupabaseDB = Depends(get_database),
    user: Dict[str, Any] = Depends(get_current_user),
):
    del user
    if not _table_exists(db, "follow_ups"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"message": "follow_ups table is missing. Run migration 002.", "code": "MIGRATION_REQUIRED"},
        )

    try:
        query = db.client.table("follow_ups").select("*", count="exact")
        if status_filter:
            query = query.eq("status", status_filter)
        if date_from:
            query = query.gte("scheduled_at", date_from)
        if date_to:
            query = query.lte("scheduled_at", date_to)

        response = query.order("scheduled_at", desc=False).range(offset, offset + limit - 1).execute()
        rows = _safe_rows(response)
        total = int(getattr(response, "count", len(rows)) or len(rows))

        lead_name_by_id: Dict[str, str] = {}
        if _table_exists(db, "customers"):
            lead_ids = [str(r.get("lead_id")) for r in rows if r.get("lead_id")]
            if lead_ids:
                customer_rows = _safe_rows(
                    db.client.table("customers").select("id, name").in_("id", lead_ids).execute()
                )
                lead_name_by_id = {str(r.get("id")): (r.get("name") or "Unknown") for r in customer_rows}

        shaped = [
            _follow_up_api_shape(row, lead_name=lead_name_by_id.get(str(row.get("lead_id"))))
            for row in rows
        ]

        return _list_response(shaped, total=total, limit=limit, offset=offset)
    except Exception as e:
        logger.error(f"Failed to list follow-ups: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to list follow-ups", "code": "DB_ERROR"},
        )


@router.post("/follow-ups", status_code=status.HTTP_201_CREATED)
async def create_follow_up(
    payload: FollowUpCreate,
    db: SupabaseDB = Depends(get_database),
    user: Dict[str, Any] = Depends(get_current_user),
):
    if not _table_exists(db, "follow_ups"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"message": "follow_ups table is missing. Run migration 002.", "code": "MIGRATION_REQUIRED"},
        )

    if not payload.lead_id and not payload.customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "lead_id or customer_id is required", "code": "VALIDATION_ERROR"},
        )

    try:
        record = payload.model_dump(exclude_none=True)
        record["created_by"] = user.get("id")
        response = db.client.table("follow_ups").insert(record).execute()
        rows = _safe_rows(response)
        if not rows:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"message": "Failed to create follow-up", "code": "DB_ERROR"},
            )

        return _success_response(_follow_up_api_shape(rows[0]))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create follow-up: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to create follow-up", "code": "DB_ERROR"},
        )


@router.patch("/follow-ups/{follow_up_id}")
async def update_follow_up(
    follow_up_id: str,
    payload: FollowUpUpdate,
    db: SupabaseDB = Depends(get_database),
    user: Dict[str, Any] = Depends(get_current_user),
):
    del user
    if not _table_exists(db, "follow_ups"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"message": "follow_ups table is missing. Run migration 002.", "code": "MIGRATION_REQUIRED"},
        )

    try:
        updates = payload.model_dump(exclude_none=True)
        if not updates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "No fields to update", "code": "VALIDATION_ERROR"},
            )
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()

        response = db.client.table("follow_ups").update(updates).eq("id", follow_up_id).execute()
        rows = _safe_rows(response)
        if not rows:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "Follow-up not found", "code": "NOT_FOUND"},
            )

        return _success_response(_follow_up_api_shape(rows[0]))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update follow-up {follow_up_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to update follow-up", "code": "DB_ERROR"},
        )


# -----------------------------
# Campaigns
# -----------------------------
@router.get("/campaigns")
async def list_campaigns(
    status_filter: Optional[str] = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: SupabaseDB = Depends(get_database),
    user: Dict[str, Any] = Depends(get_current_user),
):
    del user
    if not _table_exists(db, "campaigns"):
        return _list_response([], total=0, limit=limit, offset=offset)

    try:
        query = db.client.table("campaigns").select("*", count="exact")
        if status_filter:
            query = query.eq("status", status_filter)

        response = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()
        rows = _safe_rows(response)
        total = int(getattr(response, "count", len(rows)) or len(rows))

        shaped = [_campaign_api_shape(row) for row in rows]
        return _list_response(shaped, total=total, limit=limit, offset=offset)
    except Exception as e:
        logger.error(f"Failed to list campaigns: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to list campaigns", "code": "DB_ERROR"},
        )


@router.get("/campaigns/{campaign_id}")
async def get_campaign(
    campaign_id: str,
    db: SupabaseDB = Depends(get_database),
    user: Dict[str, Any] = Depends(get_current_user),
):
    del user
    if not _table_exists(db, "campaigns"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": "Campaign not found", "code": "NOT_FOUND"},
        )

    try:
        rows = _safe_rows(db.client.table("campaigns").select("*").eq("id", campaign_id).limit(1).execute())
        if not rows:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "Campaign not found", "code": "NOT_FOUND"},
            )

        return _success_response(_campaign_api_shape(rows[0]))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch campaign {campaign_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to fetch campaign", "code": "DB_ERROR"},
        )
