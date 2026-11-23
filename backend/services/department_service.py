// backend/services/department_service.py
"""Department service utilities for Phase 15.

Provides data‑retrieval functions for the department workspace.  All
functions rely on the global ``supabase`` client created in ``backend/app.py``.
Authorization (role == 'department' and a valid department_id) is enforced
by the Flask routes that call these helpers – the service itself assumes a
trusted ``user_profile`` dictionary.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

# Import the Supabase client instantiated in backend/app.py
from backend.app import supabase  # noqa: E402


def _department_id_from_profile(user_profile: Dict[str, Any]) -> Optional[str]:
    """Return the department UUID for a department‑role user or ``None``.

    ``user_profile`` is expected to contain the fields loaded from the
    ``profiles`` table (id, role, department_id, ...).
    """
    if user_profile.get("role") != "department":
        return None
    return user_profile.get("department_id")


def _apply_time_filter(query, period: str):
    now = datetime.utcnow()
    if period == "today":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        query = query.gte("created_at", start.isoformat())
    elif period == "last_7_days":
        start = now - timedelta(days=7)
        query = query.gte("created_at", start.isoformat())
    elif period == "last_30_days":
        start = now - timedelta(days=30)
        query = query.gte("created_at", start.isoformat())
    return query


def get_department_overview(user_profile: Dict[str, Any]) -> Dict[str, int]:
    """Return operational metrics for the logged‑in department.

    Only complaints where ``assigned_department_id`` matches the user's
    department are considered.
    """
    dept_id = _department_id_from_profile(user_profile)
    if not dept_id:
        return {}
    base = supabase.from_("complaints").eq("assigned_department_id", dept_id)
    # No period filter here – overview is for all time (could be extended)
    resp = base.select(
        "id,status,priority,deadline,assigned_department_id"
    ).execute()
    if resp.error:
        return {}
    rows: List[Dict[str, Any]] = resp.data or []
    now = datetime.utcnow()
    warning_hours = int(os.getenv("SLA_WARNING_HOURS", "24"))
    warning_delta = timedelta(hours=warning_hours)
    total = len(rows)
    active = sum(1 for r in rows if r["status"] not in ("resolved", "rejected"))
    new_assigned = sum(1 for r in rows if r["status"] == "assigned")
    acknowledged = sum(1 for r in rows if r["status"] == "acknowledged")
    in_progress = sum(1 for r in rows if r["status"] == "in_progress")
    overdue = sum(
        1
        for r in rows
        if r["deadline"]
        and datetime.fromisoformat(r["deadline"][:-1]) < now
        and r["status"] not in ("resolved", "rejected")
    )
    due_soon = sum(
        1
        for r in rows
        if r["deadline"]
        and now <= datetime.fromisoformat(r["deadline"][:-1]) <= now + warning_delta
        and r["status"] not in ("resolved", "rejected")
    )
    high_critical = sum(1 for r in rows if r["priority"] in ("high", "critical") and r["status"] not in ("resolved", "rejected"))
    resolved = sum(1 for r in rows if r["status"] == "resolved")
    return {
        "total_complaints": total,
        "active_complaints": active,
        "new_assigned": new_assigned,
        "acknowledged": acknowledged,
        "in_progress": in_progress,
        "overdue": overdue,
        "due_soon": due_soon,
        "high_critical": high_critical,
        "resolved": resolved,
    }


def list_department_complaints(
    *,
    user_profile: Dict[str, Any],
    search: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    sla_state: Optional[str] = None,
    cluster_id: Optional[str] = None,
    sort: str = "urgency",
    page: int = 1,
    page_size: int = 25,
) -> Dict[str, Any]:
    """Paginated, filtered list of complaints belonging to the user's department.
    """
    dept_id = _department_id_from_profile(user_profile)
    if not dept_id:
        return {"total": 0, "complaints": []}
    query = supabase.from_("complaints").eq("assigned_department_id", dept_id)
    if search:
        pattern = f"%{search}%"
        query = query.or_(f"complaint_number.ilike.{pattern},description.ilike.{pattern},address.ilike.{pattern}")
    if status:
        query = query.eq("status", status)
    if priority:
        query = query.eq("priority", priority)
    if cluster_id:
        query = query.eq("cluster_id", cluster_id)
    now = datetime.utcnow()
    if sla_state == "overdue":
        query = query.lte("deadline", now.isoformat())
    elif sla_state == "due_soon":
        warning = now + timedelta(hours=int(os.getenv("SLA_WARNING_HOURS", "24")))
        query = query.gte("deadline", now.isoformat()).lte("deadline", warning.isoformat())
    elif sla_state == "on_track":
        warning = now + timedelta(hours=int(os.getenv("SLA_WARNING_HOURS", "24")))
        query = query.gte("deadline", warning.isoformat())
    # Sorting – default "urgency" mimics the recommended ordering
    if sort == "urgency" or sort == "default":
        # critical/high priority first, then overdue, then due soon, then older created_at
        query = (
            query.order("priority", desc=True)
            .order("deadline", asc=True)  # earlier deadlines (overdue) first
            .order("created_at", desc=False)
        )
    elif sort == "newest":
        query = query.order("created_at", desc=True)
    elif sort == "oldest":
        query = query.order("created_at", desc=False)
    # Pagination (inclusive range)
    offset = (page - 1) * page_size
    query = query.range(offset, offset + page_size - 1)
    resp = query.select(
        "id,complaint_number,description,address,priority,status,deadline,created_at,updated_at,similar_count,cluster_id"
    ).execute()
    if resp.error:
        return {"total": 0, "complaints": []}
    data = resp.data or []
    # Total count via separate exact count query (Supabase supports count="exact")
    total_resp = (
        supabase.from_("complaints")
        .eq("assigned_department_id", dept_id)
        .select("id", count="exact")
        .execute()
    )
    total = getattr(total_resp, "count", len(data))
    return {"total": total, "complaints": data}


def get_department_complaint_detail(user_profile: Dict[str, Any], complaint_id: str) -> Optional[Dict[str, Any]]:
    """Fetch detailed complaint data only if it belongs to the user's department.
    """
    dept_id = _department_id_from_profile(user_profile)
    if not dept_id:
        return None
    resp = (
        supabase.from_("complaints")
        .select(
            "*,assigned_department:departments!inner(name),predicted_department:departments!inner(name),citizen:profiles!inner(name,phone)"
        )
        .eq("id", complaint_id)
        .eq("assigned_department_id", dept_id)
        .single()
        .execute()
    )
    if resp.error:
        return None
    return resp.data
