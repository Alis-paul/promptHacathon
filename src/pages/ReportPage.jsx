import React, { useState, useEffect } from 'react';
import { useAuth } from '../lib/AuthProvider';
import { supabase } from '../lib/supabase';
import { Navigate, useNavigate } from 'react-router-dom';
import Navigation from '../components/Navigation';
import CameraCapture from '../components/CameraCapture';

const MAX_IMAGE_SIZE = 5 * 1024 * 1024; // 5 MB
const ACCEPTED_TYPES = ['image/jpeg', 'image/png', 'image/webp'];

const ReportPage = () => {
  const { user, sessionLoading } = useAuth();
  const navigate = useNavigate();

  // Auth handling
  if (sessionLoading) return <div className="loading">Checking your session...</div>;
  if (!user) return <Navigate to="/login" replace />;

  // Form state
  const [description, setDescription] = useState('');
  const [address, setAddress] = useState('');
  const [latitude, setLatitude] = useState(null);
  const [longitude, setLongitude] = useState(null);
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [useCamera, setUseCamera] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [submitting, setSubmitting] = useState(false);

  // Geolocation handler
  const handleUseLocation = () => {
    if (!navigator.geolocation) {
      setErrorMsg('Geolocation is not supported by your browser.');
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLatitude(pos.coords.latitude);
        setLongitude(pos.coords.longitude);
        setErrorMsg('');
      },
      (err) => {
        setErrorMsg('We couldn\'t access your location. Please enter the location manually.');
      }
    );
  };

  // Image validation
  const validateImage = (file) => {
    if (!ACCEPTED_TYPES.includes(file.type)) {
      return 'Unsupported image format. Use JPEG, PNG, or WEBP.';
    }
    if (file.size > MAX_IMAGE_SIZE) {
      return `Image exceeds maximum size of ${MAX_IMAGE_SIZE / (1024 * 1024)} MB.`;
    }
    return null;
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      const err = validateImage(file);
      if (err) {
        setErrorMsg(err);
        return;
      }
      setImageFile(file);
      setImagePreview(URL.createObjectURL(file));
    }
  };

  const handleCapture = (blob) => {
    // Convert blob to File
    const file = new File([blob], `capture-${Date.now()}.webp`, { type: blob.type });
    const err = validateImage(file);
    if (err) {
      setErrorMsg(err);
      return;
    }
    setImageFile(file);
    setImagePreview(URL.createObjectURL(file));
    setUseCamera(false);
  };

  const validateForm = () => {
    if (!description.trim()) return 'Description is required.';
    if (!address.trim() && (latitude === null || longitude === null))
      return 'Provide either an address or location coordinates.';
    if (latitude !== null && (latitude < -90 || latitude > 90)) return 'Latitude must be between -90 and 90.';
    if (longitude !== null && (longitude < -180 || longitude > 180)) return 'Longitude must be between -180 and 180.';
    return null;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg('');
    const validationError = validateForm();
    if (validationError) {
      setErrorMsg(validationError);
      return;
    }
    setSubmitting(true);
    let imagePath = null;
    try {
      // 1. Upload image if present
      if (imageFile) {
        const fileExt = imageFile.name.split('.').pop();
        const uniqueName = `${user.id}/${Date.now()}-${Math.random().toString(36).substr(2, 9)}.${fileExt}`;
        const { error: uploadError } = await supabase.storage.from('complaint-images').upload(uniqueName, imageFile);
        if (uploadError) throw new Error('Image upload failed: ' + uploadError.message);
        imagePath = `complaint-images/${uniqueName}`;
      }

      // 2. Insert complaint row
      const { data: complaintData, error: insertError } = await supabase.from('complaints').insert([
        {
          citizen_id: user.id,
          description: description,
          source: 'website',
          latitude: latitude,
          longitude: longitude,
          address: address,
          citizen_image_path: imagePath,
          status: 'submitted',
          priority: 'low',
          priority_score: 0,
        },
      ]).select('id, complaint_number');

      if (insertError) throw insertError;
      const complaint = complaintData[0];

      // 3. Create initial history entry
      await supabase.from('complaint_history').insert([
        {
          complaint_id: complaint.id,
          status: 'submitted',
          message: 'Complaint submitted successfully.',
          changed_by: user.id,
        },
      ]);

      // 4. Navigate to success page
      // 4. Trigger AI routing (server-side)
try {
  await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/complaints/${complaint.id}/route`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${sessionStorage.getItem('supabase.auth.token')}`,
    },
    body: JSON.stringify({ description }),
  });
} catch (routingErr) {
  console.error('Routing error:', routingErr);
}

// 5. Navigate to success page
navigate(`/complaint/${complaint.id}`);
    } catch (err) {
      console.error(err);
      if (err.message.includes('Image upload')) {
        setErrorMsg('We couldn\'t upload your photo. Please try again or submit without the photo.');
      } else {
        setErrorMsg('We couldn\'t submit your complaint. Please try again.');
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div>
      <Navigation />
      <section style={{ padding: 'var(--space-12) var(--space-4)', maxWidth: '800px', margin: '0 auto' }}>
        <h2 style={{ fontFamily: 'var(--font-display)', marginBottom: 'var(--space-6)' }}>Report an Issue</h2>
        {errorMsg && <p style={{ color: 'var(--color-danger)' }}>{errorMsg}</p>}
        <form onSubmit={handleSubmit}>
          {/* Description */}
          <div style={{ marginBottom: 'var(--space-6)' }}>
            <label htmlFor="description" style={{ display: 'block', marginBottom: 'var(--space-2)' }}>What happened?</label>
            <textarea
              id="description"
              rows={5}
              required
              placeholder="Describe the problem in your own words..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              style={{ width: '100%', padding: 'var(--space-2)', border: '1px solid var(--color-border)' }}
            />
            <small>Tell us what you noticed, where it happened, and anything that may help the municipality understand the issue.</small>
          </div>

          {/* Location */}
          <div style={{ marginBottom: 'var(--space-6)' }}>
            <label htmlFor="address" style={{ display: 'block', marginBottom: 'var(--space-2)' }}>Address / Location</label>
            <input
              id="address"
              type="text"
              placeholder="Enter address or description"
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              style={{ width: '100%', padding: 'var(--space-2)', border: '1px solid var(--color-border)' }}
            />
            <button type="button" onClick={handleUseLocation} style={{ marginTop: 'var(--space-2)', background: 'var(--color-primary-navy)', color: 'var(--color-white)', border: 'none', padding: 'var(--space-2) var(--space-4)' }}>
              Use my current location
            </button>
            {latitude !== null && longitude !== null && (
              <p>Coordinates: {latitude.toFixed(6)}, {longitude.toFixed(6)}</p>
            )}
          </div>

          {/* Photo */}
          <div style={{ marginBottom: 'var(--space-6)' }}>
            <label style={{ display: 'block', marginBottom: 'var(--space-2)' }}>Photo evidence (optional)</label>
            {imagePreview && (
              <div style={{ marginBottom: 'var(--space-2)' }}>
                <img src={imagePreview} alt="Selected preview" style={{ maxWidth: '100%', maxHeight: '300px' }} />
                <div style={{ marginTop: 'var(--space-2)' }}>
                  <button type="button" onClick={() => { setImageFile(null); setImagePreview(null); }} style={{ marginRight: 'var(--space-2)' }}>Remove</button>
                </div>
              </div>
            )}
            {!imagePreview && (
              <div style={{ display: 'flex', gap: 'var(--space-4)' }}>
                <button type="button" onClick={() => setUseCamera(true)} style={{ background: 'var(--color-primary-navy)', color: 'var(--color-white)', border: 'none', padding: 'var(--space-2) var(--space-4)' }}>
                  Take a Photo
                </button>
                <input type="file" accept="image/*" onChange={handleFileChange} />
              </div>
            )}
            {useCamera && (
              <CameraCapture onCapture={handleCapture} onCancel={() => setUseCamera(false)} />
            )}
          </div>

          <button type="submit" disabled={submitting} style={{ background: 'var(--color-primary-navy)', color: 'var(--color-white)', border: 'none', padding: 'var(--space-3) var(--space-6)' }}>
            {submitting ? 'Submitting…' : 'Submit Complaint'}
          </button>
        </form>
      </section>
    </div>
  );
};

export default ReportPage;
