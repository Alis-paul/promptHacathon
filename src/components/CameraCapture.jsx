import React, { useEffect, useRef, useState } from 'react';

/**
 * CameraCapture component uses the MediaDevices API to capture a photo.
 * Props:
 *   onCapture(blob) - called with the captured image blob (webp/jpeg/png).
 *   onCancel() - called when the user cancels the capture.
 */
const CameraCapture = ({ onCapture, onCancel }) => {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [error, setError] = useState(null);
  const [stream, setStream] = useState(null);

  useEffect(() => {
    // Request camera access
    const getCamera = async () => {
      try {
        const mediaStream = await navigator.mediaDevices.getUserMedia({ video: true });
        setStream(mediaStream);
        if (videoRef.current) {
          videoRef.current.srcObject = mediaStream;
        }
      } catch (e) {
        console.error(e);
        setError('Camera access was denied or unavailable.');
      }
    };
    getCamera();
    return () => {
      if (stream) {
        stream.getTracks().forEach((track) => track.stop());
      }
    };
  }, []);

  const handleCapture = () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas) return;
    const ctx = canvas.getContext('2d');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    canvas.toBlob((blob) => {
      if (blob) {
        onCapture(blob);
      } else {
        setError('Failed to capture image.');
      }
    }, 'image/webp');
  };

  if (error) {
    return (
      <div>
        <p>{error}</p>
        <button type="button" onClick={onCancel}>Back to upload</button>
      </div>
    );
  }

  return (
    <div style={{ marginBottom: 'var(--space-6)' }}>
      <video ref={videoRef} autoPlay playsInline style={{ width: '100%', maxHeight: '400px' }} />
      <canvas ref={canvasRef} style={{ display: 'none' }} />
      <div style={{ marginTop: 'var(--space-2)' }}>
        <button type="button" onClick={handleCapture} style={{ marginRight: 'var(--space-2)', background: 'var(--color-primary-navy)', color: 'var(--color-white)', border: 'none', padding: 'var(--space-2) var(--space-4)' }}>
          Capture
        </button>
        <button type="button" onClick={onCancel} style={{ background: 'var(--color-muted-blue)', color: 'var(--color-white)', border: 'none', padding: 'var(--space-2) var(--space-4)' }}>
          Cancel
        </button>
      </div>
    </div>
  );
};

export default CameraCapture;
