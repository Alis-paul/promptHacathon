// backend/app.py
import os
from flask import Flask, request, jsonify
from supabase import create_client, Client
import joblib

from .services.clustering_service import assign_to_cluster

# Supabase client using service role (backend privileged)
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError('Supabase configuration missing in environment')

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# Confidence threshold (default 0.70)
CONF_THRESHOLD = float(os.getenv('ML_ROUTING_CONFIDENCE_THRESHOLD', '0.70'))

# Load ML model (placeholder if not available)
MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'ml', 'models', 'complaint_classifier.joblib')
if os.path.exists(MODEL_PATH):
    model = joblib.load(MODEL_PATH)
else:
    model = None  # fallback mock classifier

def classify_description(description: str):
    """Return a classification result.
    Expected dict keys: department (str or None), confidence (float), top (list of str).
    """
    if model:
        # Real inference would go here – omitted for brevity
        raise NotImplementedError('Real model inference not implemented in this placeholder')
    # Simple keyword‑based mock for demonstration
    lowered = description.lower()
    mapping = {
        'road': 'Roads',
        'pothole': 'Roads',
        'street': 'Roads',
        'water': 'Water Supply',
        'leak': 'Water Supply',
        'drain': 'Drainage',
        'sewer': 'Drainage',
        'garbage': 'Sanitation',
        'trash': 'Sanitation',
        'light': 'Electrical / Streetlights',
        'streetlight': 'Electrical / Streetlights',
    }
    for keyword, dept in mapping.items():
        if keyword in lowered:
            return {'department': dept, 'confidence': 0.92, 'top': [dept]}
    return {'department': None, 'confidence': 0.48, 'top': []}

@app.route('/api/complaints/<complaint_id>/route', methods=['POST'])
def route_complaint(complaint_id):
    # Simple auth check – in production verify JWT from Supabase
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Missing or invalid Authorization header'}), 401

    # Fetch complaint details
    resp = supabase.from_('complaints').select('id, description, predicted_department_id, prediction_confidence').eq('id', complaint_id).single().execute()
    if resp.error:
        return jsonify({'error': 'Complaint not found'}), 404
    complaint = resp.data

    # Idempotency: if already processed, skip
    if complaint.get('predicted_department_id') is not None:
        return jsonify({'status': 'already processed'}), 200

    # Classify description
    try:
        result = classify_description(complaint['description'])
    except Exception as e:
        return jsonify({'error': f'Classification failed: {str(e)}'}), 500

    dept_name = result.get('department')
    confidence = result.get('confidence', 0.0)

    # Prepare update payload
    update_data = {'prediction_confidence': confidence}
    if dept_name:
        # Resolve department UUID
        dept_resp = supabase.from_('departments').select('id').eq('name', dept_name).single().execute()
        if not dept_resp.error:
            update_data['predicted_department_id'] = dept_resp.data['id']
        else:
            dept_name = None  # treat as low confidence if dept missing

    supabase.from_('complaints').update(update_data).eq('id', complaint_id).execute()

    # Record classification history
    supabase.from_('complaint_history').insert([
        {
            'complaint_id': complaint_id,
            'status': 'ai_classified',
            'message': f'AI classified as {dept_name or "unknown"} (confidence {confidence:.2f})',
            'changed_by': 'system',
        }
    ]).execute()

    if dept_name and confidence >= CONF_THRESHOLD:
        # Auto‑assign department and move to ASSIGNED status
        supabase.from_('complaints').update({
            'assigned_department_id': update_data.get('predicted_department_id'),
            'status': 'assigned'
        }).eq('id', complaint_id).execute()
        # History entry for auto‑assignment
        supabase.from_('complaint_history').insert([
            {
                'complaint_id': complaint_id,
                'status': 'assigned',
                'message': f'Complaint auto‑assigned to {dept_name}',
                'changed_by': 'system',
            }
        ]).execute()
        # Notification for the department (placeholder – actual user mapping handled elsewhere)
        supabase.from_('notifications').insert([
            {
                'user_id': None,
                'title': 'New complaint assigned',
                'message': f'Complaint #{complaint_id} assigned to your department ({dept_name})',
                'metadata': {'complaint_id': complaint_id},
            }
        ]).execute()
        # Run clustering (Phase 10)
        try:
            from .services.clustering_service import assign_to_cluster
            assign_to_cluster(complaint_id)
        except Exception as e:
            print('Clustering error:', e)
        return jsonify({'status': 'assigned', 'department': dept_name}), 200
    else:
        # Low confidence – flag for admin review
        supabase.from_('notifications').insert([
            {
                'user_id': None,
                'title': 'Complaint requires routing review',
                'message': f'Complaint #{complaint_id} needs manual routing (confidence {confidence:.2f})',
                'metadata': {'complaint_id': complaint_id},
            }
        ]).execute()
        # Run clustering even if low confidence
        try:
            from .services.clustering_service import assign_to_cluster
            assign_to_cluster(complaint_id)
        except Exception as e:
            print('Clustering error:', e)
        return jsonify({'status': 'awaiting_review', 'confidence': confidence}), 200

if __name__ == '__main__':
    # Run on a non‑conflicting port (5002) for local development
    app.run(host='0.0.0.0', port=5002, debug=True)
