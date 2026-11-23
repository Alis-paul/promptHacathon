# backend/services/priority_service.py
"""Dynamic priority service.
Calculates a priority score for a complaint cluster based on complaint volume,
recency, and geographic concentration. Updates the cluster record, syncs the
priority to active complaints, and records history entries.
"""
import os
import math
from datetime import datetime, timedelta
from typing import Dict, Any

from supabase import create_client, Client

# Configuration (defaults, can be overridden via .env)
PRIORITY_LOW_MAX_COMPLAINTS = int(os.getenv('PRIORITY_LOW_MAX_COMPLAINTS', '2'))
PRIORITY_MEDIUM_MAX_COMPLAINTS = int(os.getenv('PRIORITY_MEDIUM_MAX_COMPLAINTS', '5'))
PRIORITY_HIGH_MAX_COMPLAINTS = int(os.getenv('PRIORITY_HIGH_MAX_COMPLAINTS', '15'))

PRIORITY_LOW_SCORE_MAX = float(os.getenv('PRIORITY_LOW_SCORE_MAX', '0.24'))
PRIORITY_MEDIUM_SCORE_MAX = float(os.getenv('PRIORITY_MEDIUM_SCORE_MAX', '0.49'))
PRIORITY_HIGH_SCORE_MAX = float(os.getenv('PRIORITY_HIGH_SCORE_MAX', '0.74'))
# Anything above PRIORITY_HIGH_SCORE_MAX is critical.

PRIORITY_VOLUME_WEIGHT = float(os.getenv('PRIORITY_VOLUME_WEIGHT', '0.7'))
PRIORITY_RECENCY_WEIGHT = float(os.getenv('PRIORITY_RECENCY_WEIGHT', '0.2'))
PRIORITY_CONCENTRATION_WEIGHT = float(os.getenv('PRIORITY_CONCENTRATION_WEIGHT', '0.1'))

PRIORITY_RECENCY_WINDOW_DAYS = int(os.getenv('PRIORITY_RECENCY_WINDOW_DAYS', '30'))
# Max distance (meters) considered "concentrated" for the concentration component
PRIORITY_CONCENTRATION_RADIUS_METERS = float(os.getenv('PRIORITY_CONCENTRATION_RADIUS_METERS', '1000'))

# Supabase client (service role)
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError('Supabase configuration missing')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return distance in meters between two points."""
    R = 6371000.0  # meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def _volume_score(total_count: int) -> float:
    """Logarithmic volume score, normalized to [0,1]."""
    # reference count is the critical threshold + 1 to keep it <1
    ref = PRIORITY_HIGH_MAX_COMPLAINTS + 1
    return min(math.log1p(total_count) / math.log1p(ref), 1.0)

def _recency_score(active_complaints: list[Dict[str, Any]]) -> float:
    """Score based on how recent the active complaints are.
    Returns 1.0 if all active complaints are within the window, 0.0 if none.
    """
    if not active_complaints:
        return 0.0
    now = datetime.utcnow()
    ages = []
    for c in active_complaints:
        created = c.get('created_at')
        if isinstance(created, str):
            created = datetime.fromisoformat(created)
        ages.append((now - created).total_seconds() / 86400.0)  # days
    avg_age = sum(ages) / len(ages)
    # linear decay within window
    score = max(0.0, (PRIORITY_RECENCY_WINDOW_DAYS - avg_age) / PRIORITY_RECENCY_WINDOW_DAYS)
    return min(score, 1.0)

def _concentration_score(cluster_id: str, active_complaints: list[Dict[str, Any]]) -> float:
    """Score based on geographic concentration.
    If the average distance of active complaints to the cluster centroid is
    within PRIORITY_CONCENTRATION_RADIUS_METERS, score = 1.0, otherwise decays.
    """
    if not active_complaints:
        return 0.0
    # fetch centroid
    resp = supabase.from_('complaint_clusters').select('latitude,longitude').eq('id', cluster_id).single().execute()
    if resp.error:
        return 0.0
    centroid = resp.data
    lat_c = centroid.get('latitude')
    lon_c = centroid.get('longitude')
    if lat_c is None or lon_c is None:
        return 0.0
    distances = []
    for c in active_complaints:
        lat = c.get('latitude')
        lon = c.get('longitude')
        if lat is None or lon is None:
            continue
        distances.append(_haversine(lat_c, lon_c, lat, lon))
    if not distances:
        return 0.0
    avg_dist = sum(distances) / len(distances)
    if avg_dist <= PRIORITY_CONCENTRATION_RADIUS_METERS:
        return 1.0
    # decay linearly up to 5*radius, then 0
    max_dist = PRIORITY_CONCENTRATION_RADIUS_METERS * 5
    score = max(0.0, (max_dist - avg_dist) / max_dist)
    return min(score, 1.0)

def _map_score_to_level(score: float) -> str:
    if score <= PRIORITY_LOW_SCORE_MAX:
        return 'low'
    if score <= PRIORITY_MEDIUM_SCORE_MAX:
        return 'medium'
    if score <= PRIORITY_HIGH_SCORE_MAX:
        return 'high'
    return 'critical'

def _insert_history(cluster_id: str, old_level: str, new_level: str, score: float) -> None:
    if old_level == new_level:
        return
    message = f"Priority changed from {old_level} to {new_level} (score {score:.2f})"
    supabase.from_('complaint_history').insert([
        {
            'complaint_id': None,  # cluster‑level entry; we store null and reference cluster via metadata
            'status': 'priority_update',
            'message': message,
            'changed_by': 'system',
            'metadata': {'cluster_id': cluster_id},
        }
    ]).execute()

def calculate_cluster_priority(cluster_id: str) -> Dict[str, Any]:
    """Calculate and persist priority for a cluster.
    Returns a dict with the new priority data.
    """
    # Fetch cluster data + all complaints belonging to it
    cluster_resp = supabase.from_('complaint_clusters').select('id, priority, priority_score, complaint_count').eq('id', cluster_id).single().execute()
    if cluster_resp.error:
        raise RuntimeError(f'Cluster {cluster_id} not found')
    cluster = cluster_resp.data
    # Fetch complaints (only need fields for scoring)
    complaints_resp = supabase.from_('complaints').select('id, status, created_at, latitude, longitude').eq('cluster_id', cluster_id).execute()
    if complaints_resp.error:
        raise RuntimeError('Failed to fetch complaints for priority')
    complaints = complaints_resp.data
    total_count = len(complaints)
    # Determine active (unresolved) complaints
    unresolved_statuses = [
        'submitted', 'ai_classified', 'assigned', 'acknowledged',
        'in_progress', 'resolution_submitted', 'verification',
        'rejected', 'reassigned'
    ]
    active = [c for c in complaints if c.get('status') in unresolved_statuses]
    active_count = len(active)

    # Component scores
    volume = _volume_score(active_count)
    recency = _recency_score(active)
    concentration = _concentration_score(cluster_id, active)
    # Weighted total score (ensure sum of weights == 1)
    total_score = (
        PRIORITY_VOLUME_WEIGHT * volume +
        PRIORITY_RECENCY_WEIGHT * recency +
        PRIORITY_CONCENTRATION_WEIGHT * concentration
    )
    # Map to level
    new_level = _map_score_to_level(total_score)
    old_level = cluster.get('priority') or 'low'
    # Persist changes if needed
    updates = {
        'priority': new_level,
        'priority_score': round(total_score, 4),
        'updated_at': datetime.utcnow().isoformat(),
    }
    supabase.from_('complaint_clusters').update(updates).eq('id', cluster_id).execute()
    # Sync active complaints' priority fields
    if active:
        supabase.from_('complaints').update({
            'priority': new_level,
            'priority_score': round(total_score, 4)
        }).eq('cluster_id', cluster_id).in_('status', unresolved_statuses).execute()
    # History entry
    _insert_history(cluster_id, old_level, new_level, total_score)
    return {
        'cluster_id': cluster_id,
        'priority': new_level,
        'priority_score': total_score,
        'total_complaint_count': total_count,
        'active_complaint_count': active_count,
    }

# Helper for external callers (e.g., after cluster merge or complaint resolution)
def recalculate_for_cluster(cluster_id: str) -> None:
    try:
        calculate_cluster_priority(cluster_id)
    except Exception as e:
        print('Priority recalculation error:', e)
