import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../lib/AuthProvider';
import { fetchComplaint, updateComplaintStatus } from '../lib/complaintService';
import { STATUS, nextStatusOptions } from '../lib/statusService';
import Navigation from '../components/Navigation';

const ComplaintDetail = () => {
  const { user, profile, sessionLoading } = useAuth();
  const { id } = useParams();
  const navigate = useNavigate();

  const [complaint, setComplaint] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [updating, setUpdating] = useState(false);

  // Fetch complaint and its history
  useEffect(() => {
    const load = async () => {
      try {
        const comp = await fetchComplaint(id);
        setComplaint(comp);
        const { data: hist, error: histErr } = await fetchComplaintHistory(id);
        if (histErr) throw histErr;
        setHistory(hist);
      } catch (e) {
        console.error(e);
        setError('Failed to load complaint.');
      } finally {
        setLoading(false);
      }
    };
    if (!sessionLoading && user) load();
  }, [id, sessionLoading, user]);

  // Helper to fetch history (separate function to avoid circular import)
  const fetchComplaintHistory = async (complaintId) => {
    const { data, error } = await supabase
      .from('complaint_history')
      .select('*')
      .eq('complaint_id', complaintId)
      .order('created_at', { ascending: true });
    return { data, error };
  };

  if (sessionLoading) return <div className="loading">Checking your session...</div>;
  if (!user) return <Navigate to="/login" replace />;

  if (loading) return <div className="loading">Loading complaint...</div>;
  if (error) return <p style={{ color: 'var(--color-danger)' }}>{error}</p>;

  const isCitizen = profile?.role === 'citizen';
  const isDepartment = profile?.role === 'department';
  const isAdmin = profile?.role === 'admin';

  // Determine allowed next statuses based on role and current status
  let allowedNext = [];
  if (isAdmin) {
    allowedNext = nextStatusOptions(complaint.status);
  } else if (isDepartment) {
    // Departments can only act on complaints assigned to their department
    if (profile?.department_id && complaint.assigned_department_id === profile.department_id) {
      allowedNext = nextStatusOptions(complaint.status).filter((s) => {
        // Departments cannot move to reassigned or assigned directly unless it's part of flow
        // For simplicity allow any transition that is defined; RLS will block unauthorized updates
        return true;
      });
    }
  } else if (isCitizen) {
    // Citizens cannot change status (except maybe view)
    allowedNext = [];
  }

  const handleStatusChange = async (e) => {
    const newStatus = e.target.value;
    if (!newStatus) return;
    setUpdating(true);
    try {
      await updateComplaintStatus(complaint.id, newStatus, user.id);
      // Refresh complaint and history
      const refreshed = await fetchComplaint(id);
      setComplaint(refreshed);
      const { data: hist } = await fetchComplaintHistory(id);
      setHistory(hist);
    } catch (err) {
      console.error(err);
      setError(err.message);
    } finally {
      setUpdating(false);
    }
  };

  return (
    <div>
      <Navigation />
      <section style={{ padding: 'var(--space-12) var(--space-4)', maxWidth: '800px', margin: '0 auto' }}>
        <h2 style={{ fontFamily: 'var(--font-display)' }}>Complaint Details</h2>
        <p><strong>Number:</strong> {complaint.complaint_number}</p>
        <p><strong>Status:</strong> {complaint.status}</p>
        <p><strong>Description:</strong></p>
        <p>{complaint.description}</p>
        {complaint.citizen_image_path && (
          <div>
            <p><strong>Photo:</strong></p>
            <img src={supabase.storage.from('complaint-images').getPublicUrl(complaint.citizen_image_path).publicURL}
                 alt="Complaint evidence"
                 style={{ maxWidth: '100%', maxHeight: '300px' }} />
          </div>
        )}
        <p><strong>Location:</strong> {complaint.address || 'N/A'}</p>
        {complaint.latitude && complaint.longitude && (
          <p>Coordinates: {complaint.latitude.toFixed(6)}, {complaint.longitude.toFixed(6)}</p>
        )}

        {/* Status transition UI */}
        {allowedNext.length > 0 && (
          <div style={{ marginTop: 'var(--space-6)' }}>
            <label htmlFor="statusSelect" style={{ marginRight: 'var(--space-2)' }}>Change status:</label>
            <select id="statusSelect" onChange={handleStatusChange} disabled={updating}>
              <option value="">Select new status</option>
              {allowedNext.map((s) => (
                <option key={s} value={s}>{s.replace('_', ' ')}</option>
              ))}
            </select>
          </div>
        )}

        {/* History */}
        <h3 style={{ marginTop: 'var(--space-8)', fontFamily: 'var(--font-display)' }}>History</h3>
        <ul style={{ listStyle: 'none', padding: 0 }}>
          {history.map((h) => (
            <li key={h.id} style={{ borderBottom: `1px solid var(--color-border)`, padding: 'var(--space-4) 0' }}>
              <p><strong>Status:</strong> {h.status}</p>
              <p>{h.message}</p>
              <p style={{ fontSize: '0.8rem', color: 'var(--color-secondary-text)' }}>{new Date(h.created_at).toLocaleString()}</p>
            </li>
          ))}
        </ul>
        <button onClick={() => navigate('/')} style={{ marginTop: 'var(--space-6)', background: 'var(--color-muted-blue)', color: 'var(--color-white)', border: 'none', padding: 'var(--space-3) var(--space-6)' }}>
          Back to Home
        </button>
      </section>
    </div>
  );
};

export default ComplaintDetail;
