import React, { useRef, useState, useEffect } from 'react';

export default function CameraCapture({ onCapture, onCancel }) {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [stream, setStream] = useState(null);
  const [capturedPhoto, setCapturedPhoto] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let activeStream = null;

    async function initCamera() {
      try {
        activeStream = await navigator.mediaDevices.getUserMedia({
          video: {
            width: { ideal: 640 },
            height: { ideal: 480 },
            facingMode: 'environment'
          },
          audio: false
        });
        setStream(activeStream);
        if (videoRef.current) {
          videoRef.current.srcObject = activeStream;
        }
      } catch (err) {
        console.error('Camera access error:', err);
        setError('No camera found or permission denied');
      }
    }

    initCamera();

    return () => {
      if (activeStream) {
        activeStream.getTracks().forEach((track) => track.stop());
      }
    };
  }, []);

  const handleSnap = () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas) return;

    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    const dataUrl = canvas.toDataURL('image/jpeg', 0.85);
    setCapturedPhoto(dataUrl);
  };

  const handleRetake = () => {
    setCapturedPhoto(null);
  };

  const handleConfirm = () => {
    if (capturedPhoto && onCapture) {
      onCapture(capturedPhoto);
    }
  };

  return (
    <div style={containerStyle}>
      {/* Top Header Bar */}
      <div style={headerStyle}>
        <span style={{ fontWeight: 'bold' }}>Camera Capture</span>
        <button type="button" onClick={onCancel} style={closeBtnStyle}>
          ✕
        </button>
      </div>

      {/* Main Viewfinder Area */}
      <div style={viewfinderStyle}>
        {error ? (
          <div style={{ color: '#ff6b6b', fontSize: '11px', padding: '10px', textAlign: 'center' }}>
            {error}
          </div>
        ) : !capturedPhoto ? (
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            style={mediaStyle}
          />
        ) : (
          <img src={capturedPhoto} alt="Snapshot" style={mediaStyle} />
        )}
        <canvas ref={canvasRef} style={{ display: 'none' }} />
      </div>

      {/* Action Bar (Always visible within the 240px screen height) */}
      <div style={actionBarStyle}>
        {!capturedPhoto ? (
          <>
            <button type="button" onClick={onCancel} style={btnSecondary}>
              Cancel
            </button>
            <button
              type="button"
              onClick={handleSnap}
              disabled={!stream || !!error}
              style={btnPrimary}
            >
              Take Photo
            </button>
          </>
        ) : (
          <>
            <button type="button" onClick={handleRetake} style={btnSecondary}>
              Retake
            </button>
            <button type="button" onClick={handleConfirm} style={btnPrimary}>
              Use Photo
            </button>
          </>
        )}
      </div>
    </div>
  );
}

// Fixed dimensions ensuring visibility within 320x240 LCD container
const containerStyle = {
  position: 'absolute',
  inset: 0,
  width: '320px',
  height: '240px',
  backgroundColor: '#111',
  color: '#fff',
  display: 'flex',
  flexDirection: 'column',
  justifyContent: 'space-between',
  zIndex: 100,
  boxSizing: 'border-box',
  padding: '6px'
};

const headerStyle = {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  fontSize: '12px',
  height: '20px',
  padding: '0 4px'
};

const closeBtnStyle = {
  background: 'none',
  border: 'none',
  color: '#aaa',
  cursor: 'pointer',
  fontSize: '14px',
  lineHeight: 1
};

const viewfinderStyle = {
  flex: 1,
  width: '100%',
  maxHeight: '160px',
  backgroundColor: '#000',
  borderRadius: '4px',
  overflow: 'hidden',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center'
};

// 'contain' ensures the full sensor aspect ratio is shown without cropping
const mediaStyle = {
  width: '100%',
  height: '100%',
  objectFit: 'contain'
};

const actionBarStyle = {
  height: '36px',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'flex-end',
  gap: '8px',
  padding: '4px 0'
};

const btnPrimary = {
  padding: '6px 14px',
  backgroundColor: '#2563eb',
  color: '#fff',
  border: 'none',
  borderRadius: '4px',
  fontSize: '11px',
  fontWeight: 'bold',
  cursor: 'pointer'
};

const btnSecondary = {
  padding: '6px 10px',
  backgroundColor: '#374151',
  color: '#e5e7eb',
  border: 'none',
  borderRadius: '4px',
  fontSize: '11px',
  cursor: 'pointer'
};