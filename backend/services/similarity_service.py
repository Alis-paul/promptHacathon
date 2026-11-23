# services/similarity_service.py
"""Similarity Service for complaints.
Implements TF‑IDF vectorisation, cosine similarity and simple contextual adjustments.
"""
import os
import math
from datetime import datetime, timedelta
from typing import List, Dict, Any

from supabase import create_client, Client
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Environment configuration
SIMILARITY_THRESHOLD = float(os.getenv('SIMILARITY_THRESHOLD', '0.70'))
SIMILARITY_TOP_K = int(os.getenv('SIMILARITY_TOP_K', '5'))
SIMILARITY_LOOKBACK_DAYS = int(os.getenv('SIMILARITY_LOOKBACK_DAYS', '30'))
SIMILARITY_DISTANCE_KM = float(os.getenv('SIMILARITY_DISTANCE_KM', '5'))  # max distance to consider candidates

# Initialise Supabase client (service role)
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError('Supabase configuration missing')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

def _normalize_text(text: str) -> str:
    """Basic preprocessing for similarity.
    Lower‑case, strip whitespace, replace multiple spaces with single space.
    """
    return " ".join(text.lower().split())

def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return distance in kilometres between two lat/lon points.
    Simple Haversine implementation.
    """
    R = 6371.0  # Earth radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def _candidate_query(new_complaint: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Fetch candidate complaints from Supabase.
    Filters:
      - same department (if supplied)
      - created within lookback window
      - optional geographic proximity (if both have coords)
    Returns list of complaint rows.
    """
    base = supabase.from_('complaints').select('id, description, department_id, latitude, longitude, created_at, cluster_id, similar_count')
    # time window
    cutoff = (datetime.utcnow() - timedelta(days=SIMILARITY_LOOKBACK_DAYS)).isoformat()
    base = base.gt('created_at', cutoff)
    # department filter if present
    if new_complaint.get('department_id'):
        base = base.eq('department_id', new_complaint['department_id'])
    # exclude the complaint itself if it already exists (should not happen for new)
    if new_complaint.get('id'):
        base = base.neq('id', new_complaint['id'])
    resp = base.execute()
    if resp.error:
        return []
    candidates = resp.data
    # Apply geographic distance filter where both have coordinates
    if new_complaint.get('latitude') is not None and new_complaint.get('longitude') is not None:
        filtered = []
        for c in candidates:
            if c.get('latitude') is not None and c.get('longitude') is not None:
                dist = _haversine(new_complaint['latitude'], new_complaint['longitude'], c['latitude'], c['longitude'])
                if dist <= SIMILARITY_DISTANCE_KM:
                    filtered.append(c)
            else:
                # keep candidates without coords – they may still be relevant
                filtered.append(c)
        candidates = filtered
    return candidates

def _vectorize_texts(texts: List[str]):
    vectorizer = TfidfVectorizer(lowercase=True, ngram_range=(1, 2), stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(texts)
    return vectorizer, tfidf_matrix

def find_similar_text(text: str, department_id: str = None, latitude: float = None, longitude: float = None) -> List[Dict[str, Any]]:
    """Public helper to find similar existing complaints.
    Returns a list of dicts with complaint_id, similarity, and optionally cluster_id.
    """
    new_complaint = {
        'description': text,
        'department_id': department_id,
        'latitude': latitude,
        'longitude': longitude,
        'id': None,
    }
    candidates = _candidate_query(new_complaint)
    if not candidates:
        return []
    # Prepare corpus texts
    corpus_texts = [_normalize_text(c['description'] or '') for c in candidates]
    new_text_norm = _normalize_text(text)
    # Vectorize
    vectorizer, tfidf_matrix = _vectorize_texts(corpus_texts + [new_text_norm])
    # Compute cosine similarity between new vector (last row) and all others
    sims = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1]).flatten()
    # Pair with candidates
    results = []
    for cand, sim in zip(candidates, sims):
        if sim >= SIMILARITY_THRESHOLD:
            results.append({
                'complaint_id': cand['id'],
                'similarity': float(sim),
                'cluster_id': cand.get('cluster_id'),
            })
    # Sort and top‑k
    results.sort(key=lambda x: x['similarity'], reverse=True)
    return results[:SIMILARITY_TOP_K]

def process_new_complaint(complaint_id: str) -> None:
    """Run similarity detection for a newly stored complaint.
    Updates similar_count on the new complaint and on matched complaints.
    If a matched complaint already belongs to a cluster, assign the same cluster_id to the new one.
    If no cluster exists but matches are found, create a minimal cluster and link them.
    """
    # Retrieve the new complaint details
    resp = supabase.from_('complaints').select('id, description, department_id, latitude, longitude, cluster_id').eq('id', complaint_id).single().execute()
    if resp.error:
        return
    comp = resp.data
    matches = find_similar_text(
        text=comp['description'] or '',
        department_id=comp.get('department_id'),
        latitude=comp.get('latitude'),
        longitude=comp.get('longitude'),
    )
    # Update similar_count for this complaint
    similar_cnt = len(matches)
    supabase.from_('complaints').update({'similar_count': similar_cnt}).eq('id', complaint_id).execute()
    # Increment similar_count on matched complaints
    for m in matches:
        # Fetch current similar_count and increment by 1 safely
        cur_resp = supabase.from_('complaints').select('similar_count').eq('id', m['complaint_id']).single().execute()
        if not cur_resp.error:
            cur_cnt = cur_resp.data.get('similar_count') or 0
            supabase.from_('complaints').update({'similar_count': cur_cnt + 1}).eq('id', m['complaint_id']).execute()
    # Cluster handling – simple approach
    # Find any existing cluster_id among matches
    existing_cluster = None
    for m in matches:
        if m.get('cluster_id'):
            existing_cluster = m['cluster_id']
            break
    if existing_cluster:
        # Assign the same cluster to the new complaint
        supabase.from_('complaints').update({'cluster_id': existing_cluster}).eq('id', complaint_id).execute()
    elif matches:
        # Create a new cluster and link the new complaint and the first match
        cluster_resp = supabase.from_('complaint_clusters').insert([{'created_at': datetime.utcnow().isoformat()}]).select('id').execute()
        if not cluster_resp.error:
            new_cluster_id = cluster_resp.data[0]['id']
            # Update new complaint
            supabase.from_('complaints').update({'cluster_id': new_cluster_id}).eq('id', complaint_id).execute()
            # Update first match (or all matches) to same cluster
            first_match_id = matches[0]['complaint_id']
            supabase.from_('complaints').update({'cluster_id': new_cluster_id}).eq('id', first_match_id).execute()
    # else: no similar complaints – leave cluster_id null
    return
