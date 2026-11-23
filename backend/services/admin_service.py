// backend/services/admin_service.py
"""Admin service utilities for Phase 14.

Provides data‑retrieval functions for the admin control centre.  The Flask
routes in ``backend/app.py`` call these helpers.  All queries are performed
server‑side using the global Supabase client defined in ``backend/app.py``.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

# Import the Supabase client that is instantiated in ``backend/app.py``.
# Using an absolute import keeps the module independent of package layout.
from backend.app import supabase  # noqa: E402


def _apply_time_filter(query, period: str):
    """Apply a creation‑time filter to a Supabase query.

    ``period`` may be ``today``, ``last_7_days``, ``last_30_days`` or ``all``.
    The function returns the mutated query.
    """
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
    # ``all`` applies no filter.
    return query


def get_overview_metrics(period: str = "all") -> Dict[str, int]:
    """Return high‑level operational metrics for the admin dashboard.
    
    The metrics are derived from the ``complaints`` table.  All calculations are
    performed in Python to keep the implementation simple and portable.
    """
    base = supabase.from_("complaints")
    base = _apply_time_filter(base, period)

    resp = base.select(
        "id,status,priority,deadline,assigned_department_id,prediction_confidence"
    ).execute()
    if resp.error:
        return {k: 0 for k in (
            "total_complaints",
            "active_complaints",
            "unassigned_review",
            "high_critical",
            "overdue",
            "due_soon",
            "resolved",
        )}

    rows: List[Dict[str, Any]] = resp.data or []
    now = datetime.utcnow()
    sla_warning_hours = int(os.getenv("SLA_WARNING_HOURS", "24"))
    warning_delta = timedelta(hours=sla_warning_hours)

    total = len(rows)
    active = sum(1 for r in rows if r["status"] not in ("resolved", "rejected"))
    unassigned_review = sum(
        1 for r in rows if r["assigned_department_id"] is None and r["status"] == "ai_classified"
    )
    high_critical = sum(1 for r in rows if r["priority"] in ("high", "critical"))
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
    resolved = sum(1 for r in rows if r["status"] == "resolved")

    return {
        "total_complaints": total,
        "active_complaints": active,
        "unassigned_review": unassigned_review,
        "high_critical": high_critical,
        "overdue": overdue,
        "due_soon": due_soon,
        "resolved": resolved,
    }


def get_departments_overview() -> List[Dict[str, Any]]:
    """Return a per‑department operational summary for the admin UI."""
    dept_resp = supabase.from_("departments").select("id,name,helpline,email,sla_hours").execute()
    if dept_resp.error:
        return []
    departments = {d["id"]: d for d in dept_resp.data or []}

    comp_resp = (
        supabase.from_("complaints")
        .select("id,status,priority,deadline,assigned_department_id")
        .execute()
    )
    if comp_resp.error:
        return []
    complaints = comp_resp.data or []

    summary: Dict[str, Dict[str, Any]] = {}
    for dept_id, dept in departments.items():
        summary[dept_id] = {
            "department_id": dept_id,
            "name": dept["name"],
            "helpline": dept.get("helpline"),
            "email": dept.get("email"),
            "sla_hours": dept.get("sla_hours"),
            "active": 0,
            "assigned": 0,
            "high_critical": 0,
            "overdue": 0,
            "due_soon": 0,
            "resolved": 0,
        }
    now = datetime.utcnow()
    sla_warning_hours = int(os.getenv("SLA_WARNING_HOURS", "24"))
    warning_delta = timedelta(hours=sla_warning_hours)
    for c in complaints:
        dept_id = c["assigned_department_id"]
        if not dept_id:
            continue
        dept_sum = summary.get(dept_id)
        if not dept_sum:
            continue
        status = c["status"]
        if status not in ("resolved", "rejected"):
            dept_sum["active"] += 1
        if status == "assigned":
            dept_sum["assigned"] += 1
        if c["priority"] in ("high", "critical") and status not in ("resolved", "rejected"):
            dept_sum["high_critical"] += 1
        deadline = c.get("deadline")
        if deadline:
            deadline_dt = datetime.fromisoformat(deadline[:-1])
            if status not in ("resolved", "rejected"):
                if deadline_dt < now:
                    dept_sum["overdue"] += 1
                elif now <= deadline_dt <= now + warning_delta:
                    dept_sum["due_soon"] += 1
        if status == "resolved":
            dept_sum["resolved"] += 1
    return list(summary.values())


def get_complaints(
    *,
    search: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    department_id: Optional[str] = None,
    sla_state: Optional[str] = None,
    source: Optional[str] = None,
    review_required: Optional[bool] = None,
    sort: str = "newest",
    page: int = 1,
    page_size: int = 25,
) -> Dict[str, Any]:
    """Paginated, filtered list of complaints for the admin UI."""
    query = supabase.from_("complaints")
    if search:
        pattern = f"%{search}%"
        query = query.or_(f"complaint_number.ilike.{pattern},description.ilike.{pattern}")
    if status:
        query = query.eq("status", status)
    if priority:
        query = query.eq("priority", priority)
    if department_id:
        query = query.eq("assigned_department_id", department_id)
    if source:
        query = query.eq("source", source)
    if review_required:
        query = query.eq("status", "ai_classified").is_("assigned_department_id", None)
    now = datetime.utcnow()
    if sla_state == "overdue":
        query = query.lte("deadline", now.isoformat())
    elif sla_state == "due_soon":
        warning = now + timedelta(hours=int(os.getenv("SLA_WARNING_HOURS", "24")))
        query = query.gte("deadline", now.isoformat()).lte("deadline", warning.isoformat())
    elif sla_state == "on_track":
        warning = now + timedelta(hours=int(os.getenv("SLA_WARNING_HOURS", "24")))
        query = query.gte("deadline", warning.isoformat())
    # Sorting
    if sort == "newest":
        query = query.order("created_at", desc=True)
    elif sort == "oldest":
        query = query.order("created_at", desc=False)
    elif sort == "priority_high":
        query = query.order("priority", desc=True)
    elif sort == "deadline_soon":
        query = query.order("deadline", asc=True)
    # Pagination (Supabase range is inclusive)
    offset = (page - 1) * page_size
    query = query.range(offset, offset + page_size - 1)
    resp = query.select(
        "id,complaint_number,description,source,priority,status,assigned_department_id,deadline,created_at,updated_at,similar_count,cluster_id"
    ).execute()
    if resp.error:
        return {"total": 0, "complaints": []}
    data = resp.data or []
    # Total count – separate query for exact count.
    total_resp = supabase.from_("complaints").select("id", count="exact").execute()
    total = getattr(total_resp, "count", len(data))
    return {"total": total, "complaints": data}


def get_review_queue() -> List[Dict[str, Any]]:
    """Complaints that need admin attention (low confidence or rejected)."""
    resp = (
        supabase.from_("complaints")
        .or_("status.eq.ai_classified,assigned_department_id.is.null,status.eq.rejected")
        .select(
            "id,complaint_number,description,status,assigned_department_id,deadline,priority,created_at"
        )
        .execute()
    )
    if resp.error:
        return []
    return resp.data or []


def get_complaint_detail(complaint_id: str) -> Optional[Dict[str, Any]]:
    """Fetch a detailed view of a single complaint for admin inspection."""
    resp = (
        supabase.from_("complaints")
        .select(
            "*,assigned_department:departments!inner(name),predicted_department:departments!inner(name),citizen:profiles!inner(name,phone)"
        )
        .eq("id", complaint_id)
        .single()
        .execute()
    )
    if resp.error:
        return None
    return resp.data
