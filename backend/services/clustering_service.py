# backend/services/clustering_service.py
"""Clustering service for incident management.
Relies on similarity_service to find textually similar complaints and then applies
contextual rules (department, location, recency) to decide whether to join an
existing cluster or create a new one.
"""
import os
import math
from datetime import datetime, timedelta
from typing import List, Dict, Any

from supabase import create_client, Client

# Import similarity helpers
from .similarity_service import find_similar_text, _haversine  # reuse distance function

# Configuration (defaults, can be overridden via .env)
CLUSTER_SIMILARITY_THRESHOLD = float(os.getenv('CLUSTER_SIMILARITY_THRESHOLD', '0.75'))
CLUSTER_RADIUS_METERS = float(os.getenv('CLUSTER_RADIUS_METERS', '1000'))  # 1 km
CLUSTER_LOOKBACK_DAYS = int(os.getenv('CLUSTER_LOOKBACK_DAYS', '30'))

# Supabase client (service role)
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError('Supabase configuration missing')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

def _centroid_coords(complaint_ids: List[str]) -> (float, float):
    """Calculate average latitude/longitude of given complaints (ignoring nulls)."""
    lat_sum = 0.0
    lon_sum = 0.0
    count = 0
    if not complaint_ids:
        return None, None
    resp = supabase.from_('complaints').select('latitude,longitude').in_('id', complaint_ids).execute()
    if resp.error:
        return None, None
    for row in resp.data:
        lat = row.get('latitude')
        lon = row.get('longitude')
        if lat is not None and lon is not None:
            lat_sum += float(lat)
            lon_sum += float(lon)
            count += 1
    if count == 0:
        return None, None
    return lat_sum / count, lon_sum / count

def assign_to_cluster(complaint_id: str) -> None:
    """Assign a complaint to an existing compatible cluster or create a new one.
    This function is idempotent – if the complaint already has a cluster_id it will
    return without making changes.
    """
    # Fetch complaint details
    resp = supabase.from_('complaints').select('id, description, department_id, latitude, longitude, created_at, cluster_id').eq('id', complaint_id).single().execute()
    if resp.error:
        print(f'Clustering: complaint {complaint_id} not found')
        return
    comp = resp.data
    if comp.get('cluster_id'):
        # Already clustered
        return

    # Find similar complaints (Phase 09 service). It already respects lookback and distance.
    similar = find_similar_text(
        text=comp['description'] or '',
        department_id=comp.get('department_id'),
        latitude=comp.get('latitude'),
        longitude=comp.get('longitude'),
    )

    # Filter similar results by our stricter clustering threshold
    similar = [m for m in similar if m['similarity'] >= CLUSTER_SIMILARITY_THRESHOLD]

    # Gather candidate cluster ids from similar complaints
    candidate_clusters = {}
    for match in similar:
        # fetch the cluster_id of the matched complaint
        match_resp = supabase.from_('complaints').select('cluster_id, department_id, latitude, longitude, created_at').eq('id', match['complaint_id']).single().execute()
        if match_resp.error:
            continue
        mdata = match_resp.data
        cid = mdata.get('cluster_id')
        if not cid:
            continue  # similar complaint not yet clustered
        # Verify department compatibility (should already match via similarity filter)
        if mdata.get('department_id') != comp.get('department_id'):
            continue
        # Verify geographic proximity if both have coords
        if comp.get('latitude') is not None and comp.get('longitude') is not None and mdata.get('latitude') is not None and mdata.get('longitude') is not None:
            dist_m = _haversine(comp['latitude'], comp['longitude'], mdata['latitude'], mdata['longitude']) * 1000
            if dist_m > CLUSTER_RADIUS_METERS:
                continue
        # Verify time window (complaint created within lookback days)
        created = datetime.fromisoformat(comp['created_at']) if isinstance(comp['created_at'], str) else comp['created_at']
        now = datetime.utcnow()
        if (now - created).days > CLUSTER_LOOKBACK_DAYS:
            continue
        # Record best similarity per cluster
        prev = candidate_clusters.get(cid)
        if not prev or match['similarity'] > prev['similarity']:
            candidate_clusters[cid] = {'similarity': match['similarity'], 'complaint_id': match['complaint_id']}

    # Choose the best cluster if any
    if candidate_clusters:
        # pick cluster with highest similarity
        best_cid = max(candidate_clusters.items(), key=lambda kv: kv[1]['similarity'])[0]
        # Assign complaint to this cluster and increment count
        supabase.from_('complaints').update({'cluster_id': best_cid}).eq('id', complaint_id).execute()
        # Increment complaint_count safely (read‑modify‑write)
        cnt_resp = supabase.from_('complaint_clusters').select('complaint_count').eq('id', best_cid).single().execute()
        if not cnt_resp.error:
            new_cnt = (cnt_resp.data.get('complaint_count') or 0) + 1
            supabase.from_('complaint_clusters').update({'complaint_count': new_cnt}).eq('id', best_cid).execute()
        # Recompute centroid if coordinates are present
        _update_cluster_location(best_cid)
        return

    # No suitable existing cluster – create a new one
    title = _generate_cluster_title(comp['description'])
    # Use first complaint's location as initial cluster location (if any)
    lat = comp.get('latitude')
    lon = comp.get('longitude')
    new_cluster = {
        'title': title,
        'department_id': comp.get('department_id'),
        'complaint_count': 1,
        'priority': 'low',
        'latitude': lat,
        'longitude': lon,
        'created_at': datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat(),
    }
    insert_resp = supabase.from_('complaint_clusters').insert([new_cluster]).select('id').execute()
    if insert_resp.error:
        print('Cluster creation failed:', insert_resp.error)
        return
    new_cid = insert_resp.data[0]['id']
    # Attach complaint to new cluster
    supabase.from_('complaints').update({'cluster_id': new_cid}).eq('id', complaint_id).execute()
    return

def _generate_cluster_title(description: str) -> str:
    """Very naive title generation – use first 6 words of description with capitalisation."""
    words = description.split()
    snippet = ' '.join(words[:6])
    return snippet.title()

def _update_cluster_location(cluster_id: str) -> None:
    """Recalculate centroid of all complaints belonging to a cluster and update the cluster row."""
    # Get all complaint ids for the cluster
    resp = supabase.from_('complaints').select('id').eq('cluster_id', cluster_id).execute()
    if resp.error:
        return
    ids = [c['id'] for c in resp.data]
    lat, lon = _centroid_coords(ids)
    update_data = {'updated_at': datetime.utcnow().isoformat()}
    if lat is not None and lon is not None:
        update_data['latitude'] = lat
        update_data['longitude'] = lon
    supabase.from_('complaint_clusters').update(update_data).eq('id', cluster_id).execute()

def merge_clusters(source_cluster_id: str, target_cluster_id: str, user_role: str) -> bool:
    """Merge source cluster into target cluster.
    Only allowed for admin role (or other privileged caller).
    Returns True on success.
    """
    if user_role != 'admin':
        return False
    # Reassign all complaints from source to target
    supabase.from_('complaints').update({'cluster_id': target_cluster_id}).eq('cluster_id', source_cluster_id).execute()
    # Update complaint counts
    tgt_resp = supabase.from_('complaint_clusters').select('complaint_count').eq('id', target_cluster_id).single().execute()
    src_resp = supabase.from_('complaint_clusters').select('complaint_count').eq('id', source_cluster_id).single().execute()
    if not tgt_resp.error and not src_resp.error:
        new_count = (tgt_resp.data.get('complaint_count') or 0) + (src_resp.data.get('complaint_count') or 0)
        supabase.from_('complaint_clusters').update({'complaint_count': new_count}).eq('id', target_cluster_id).execute()
    # Delete source cluster
    supabase.from_('complaint_clusters').delete().eq('id', source_cluster_id).execute()
    # Re‑compute centroid for target cluster
    _update_cluster_location(target_cluster_id)
    return True
