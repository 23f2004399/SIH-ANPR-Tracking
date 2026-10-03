'use client';

import React, { useEffect } from 'react';
import { SightingItem } from '@/types';

interface VehiclePhotoModalProps {
  sighting: SightingItem | null;
  onClose: () => void;
}

export default function VehiclePhotoModal({ sighting, onClose }: VehiclePhotoModalProps) {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  if (!sighting) return null;

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 100,
        backgroundColor: 'rgba(15, 23, 42, 0.75)',
        backdropFilter: 'blur(4px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '20px',
      }}
      onClick={onClose}
    >
      <div
        style={{
          background: '#FFFFFF',
          borderRadius: '8px',
          border: '1px solid #E2E4E8',
          boxShadow: '0 20px 40px rgba(15, 23, 42, 0.25)',
          maxWidth: '720px',
          width: '100%',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '14px 18px', borderBottom: '1px solid #EEF1F4', background: '#FBFCFD' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '13px', fontWeight: 600, color: '#0F172A', background: '#F1F4F7', border: '1px solid #E2E4E8', borderRadius: '4px', padding: '2px 8px' }}>
              {sighting.plateTag}
            </span>
            <span style={{ fontSize: '13px', fontWeight: 600, color: '#334155' }}>
              {sighting.cam} · {sighting.street}
            </span>
          </div>
          <button
            onClick={onClose}
            style={{
              background: '#F1F4F7',
              border: '1px solid #E2E4E8',
              borderRadius: '5px',
              width: '28px',
              height: '28px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              color: '#64748B',
              fontSize: '14px',
              fontWeight: 600,
            }}
            onMouseEnter={(e) => (e.currentTarget.style.color = '#0F172A')}
            onMouseLeave={(e) => (e.currentTarget.style.color = '#64748B')}
          >
            ✕
          </button>
        </div>

        {/* Modal Content: Photos Display */}
        <div style={{ padding: '18px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* Main Vehicle Crop */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <span style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '.08em', color: '#64748B', fontWeight: 600 }}>
                Vehicle Frame Crop
              </span>
              <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '10px', color: '#94A3B8' }}>
                {sighting.best_crop_key || 'crops/vehicles/...'}
              </span>
            </div>
            <div
              style={{
                position: 'relative',
                borderRadius: '6px',
                overflow: 'hidden',
                background: '#EDF0F4',
                border: '1px solid #E2E4E8',
                aspectRatio: '16/10',
                maxHeight: '340px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              {sighting.best_crop_key ? (
                <img
                  src={sighting.best_crop_key.startsWith('http') || sighting.best_crop_key.startsWith('/') ? sighting.best_crop_key : `/${sighting.best_crop_key}`}
                  alt={sighting.plateTag}
                  style={{ width: '100%', height: '100%', objectFit: 'contain' }}
                  onError={(e) => {
                    e.currentTarget.style.display = 'none';
                    const fallback = e.currentTarget.parentElement?.querySelector('.modal-fallback');
                    if (fallback) (fallback as HTMLElement).style.display = 'flex';
                  }}
                />
              ) : null}

              <div
                className="modal-fallback"
                style={{
                  display: sighting.best_crop_key ? 'none' : 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: '8px',
                  color: '#64748B',
                  fontSize: '12px',
                }}
              >
                <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '12px', color: '#0F172A', fontWeight: 600 }}>
                  [Crop Preview]
                </span>
                <span>{sighting.best_crop_key || 'crops/vehicles/...'}</span>
              </div>
            </div>
          </div>

          {/* License Plate Crop (if available) */}
          {sighting.plate_crop_key && (
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <span style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '.08em', color: '#64748B', fontWeight: 600 }}>
                  HSRP License Plate Crop
                </span>
                <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '10px', color: '#94A3B8' }}>
                  {sighting.plate_crop_key}
                </span>
              </div>
              <div
                style={{
                  position: 'relative',
                  borderRadius: '5px',
                  overflow: 'hidden',
                  background: '#F1F4F7',
                  border: '1px solid #E2E4E8',
                  padding: '12px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  maxHeight: '120px',
                }}
              >
                <img
                  src={sighting.plate_crop_key.startsWith('http') || sighting.plate_crop_key.startsWith('/') ? sighting.plate_crop_key : `/${sighting.plate_crop_key}`}
                  alt="Plate Crop"
                  style={{ maxHeight: '90px', objectFit: 'contain' }}
                  onError={(e) => {
                    e.currentTarget.style.display = 'none';
                  }}
                />
              </div>
            </div>
          )}

          {/* Sighting Metadata Matrix */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
              gap: '10px',
              padding: '12px 14px',
              background: '#F8FAFC',
              borderRadius: '6px',
              border: '1px solid #E2E4E8',
            }}
          >
            <div>
              <span style={{ fontSize: '9.5px', textTransform: 'uppercase', color: '#94A3B8', fontWeight: 600 }}>Observed Time</span>
              <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '12px', color: '#0F172A', marginTop: '2px' }}>
                {sighting.time} IST
              </div>
            </div>
            <div>
              <span style={{ fontSize: '9.5px', textTransform: 'uppercase', color: '#94A3B8', fontWeight: 600 }}>Confidence</span>
              <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '12px', color: '#065F46', marginTop: '2px', fontWeight: 600 }}>
                {sighting.conf}
              </div>
            </div>
            <div>
              <span style={{ fontSize: '9.5px', textTransform: 'uppercase', color: '#94A3B8', fontWeight: 600 }}>Coordinates</span>
              <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '11px', color: '#334155', marginTop: '2px' }}>
                {sighting.geo}
              </div>
            </div>
            <div>
              <span style={{ fontSize: '9.5px', textTransform: 'uppercase', color: '#94A3B8', fontWeight: 600 }}>Vehicle Type</span>
              <div style={{ fontSize: '12px', color: '#0F172A', marginTop: '2px', textTransform: 'capitalize', fontWeight: 500 }}>
                {sighting.vehicle_type || 'Car'}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
