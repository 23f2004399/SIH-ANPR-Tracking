'use client';

import React, { useState, useEffect } from 'react';
import { RoutePoint } from '@/types';

interface PrintDossierProps {
  plate: string;
  route: RoutePoint[];
  detectionsCount: number;
}

export default function PrintDossier({ plate, route, detectionsCount }: PrintDossierProps) {
  const [docRef, setDocRef] = useState<string>('ZT-DEL-261270');
  const [timestamp, setTimestamp] = useState<string>('09 SEP 2026 · 15:30 IST');

  useEffect(() => {
    setDocRef(`ZT-DEL-${Date.now().toString().slice(-6)}`);
    setTimestamp(new Date().toISOString());
  }, []);

  return (
    <div className="print-only p-8 text-black bg-white" style={{ fontFamily: "'Instrument Sans', sans-serif" }}>
      {/* Official Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', borderBottom: '2px solid #0F172A', paddingBottom: '16px', marginBottom: '24px' }}>
        <div>
          <h1 style={{ fontSize: '20px', fontWeight: 700, margin: 0, textTransform: 'uppercase', letterSpacing: '-0.02em' }}>
            ZyroTrace AI · Electronic Movement Dossier
          </h1>
          <p style={{ fontSize: '12px', color: '#475569', margin: '4px 0 0 0' }}>
            Bharat Electronics Ltd · National ANPR & Re-ID Tracking Network · PS-26127
          </p>
        </div>
        <div style={{ textAlign: 'right', fontFamily: "'JetBrains Mono', monospace", fontSize: '11px', color: '#475569' }}>
          <div suppressHydrationWarning>DOC REF: {docRef}</div>
          <div suppressHydrationWarning>GENERATED: {timestamp}</div>
          <div>STATUS: CERTIFIED AUDIT LOG</div>
        </div>
      </div>

      {/* Target Vehicle Summary Matrix */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', border: '1px solid #CBD5E1', borderRadius: '4px', padding: '16px', marginBottom: '24px', background: '#F8FAFC' }}>
        <div>
          <div style={{ fontSize: '10px', textTransform: 'uppercase', color: '#64748B', fontWeight: 600 }}>Target Plate / ID</div>
          <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '15px', fontWeight: 700, color: '#0F172A', marginTop: '2px' }}>
            {plate}
          </div>
        </div>
        <div>
          <div style={{ fontSize: '10px', textTransform: 'uppercase', color: '#64748B', fontWeight: 600 }}>Jurisdiction</div>
          <div style={{ fontSize: '13px', fontWeight: 600, color: '#0F172A', marginTop: '2px' }}>
            Delhi NCR · Outer Ring Rd
          </div>
        </div>
        <div>
          <div style={{ fontSize: '10px', textTransform: 'uppercase', color: '#64748B', fontWeight: 600 }}>Verified Sightings</div>
          <div style={{ fontSize: '13px', fontWeight: 600, color: '#0F172A', marginTop: '2px' }}>
            {detectionsCount} Detections / 4 Key Nodes
          </div>
        </div>
        <div>
          <div style={{ fontSize: '10px', textTransform: 'uppercase', color: '#64748B', fontWeight: 600 }}>Average Velocity</div>
          <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '13px', fontWeight: 600, color: '#0F172A', marginTop: '2px' }}>
            45 km/h (Dwell: 12 min)
          </div>
        </div>
      </div>

      {/* Movement Chronology Table */}
      <h2 style={{ fontSize: '14px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '12px', borderBottom: '1px solid #E2E8F0', paddingBottom: '6px' }}>
        Verified Sighting Trajectory
      </h2>

      <table style={{ width: '100%', borderCollapse: 'collapse', marginBottom: '32px', fontSize: '12px' }}>
        <thead>
          <tr style={{ background: '#F1F5F9', borderBottom: '1px solid #CBD5E1', textAlign: 'left' }}>
            <th style={{ padding: '8px 10px', fontWeight: 600, width: '40px' }}>#</th>
            <th style={{ padding: '8px 10px', fontWeight: 600, width: '90px' }}>Timestamp</th>
            <th style={{ padding: '8px 10px', fontWeight: 600, width: '90px' }}>Node ID</th>
            <th style={{ padding: '8px 10px', fontWeight: 600 }}>Camera Location</th>
            <th style={{ padding: '8px 10px', fontWeight: 600, width: '120px' }}>Speed / Status</th>
            <th style={{ padding: '8px 10px', fontWeight: 600, width: '80px' }}>Confidence</th>
            <th style={{ padding: '8px 10px', fontWeight: 600, width: '120px' }}>Geo Coordinates</th>
          </tr>
        </thead>
        <tbody>
          {route.map((p, i) => (
            <tr key={i} style={{ borderBottom: '1px solid #E2E8F0' }}>
              <td style={{ padding: '8px 10px', fontFamily: "'JetBrains Mono', monospace", fontWeight: 600 }}>{p.n}</td>
              <td style={{ padding: '8px 10px', fontFamily: "'JetBrains Mono', monospace" }}>{p.time} IST</td>
              <td style={{ padding: '8px 10px', fontFamily: "'JetBrains Mono', monospace", fontWeight: 600 }}>{p.cam}</td>
              <td style={{ padding: '8px 10px' }}>{p.street}</td>
              <td style={{ padding: '8px 10px', fontFamily: "'JetBrains Mono', monospace" }}>{p.speed}</td>
              <td style={{ padding: '8px 10px', fontFamily: "'JetBrains Mono', monospace" }}>{p.conf}</td>
              <td style={{ padding: '8px 10px', fontFamily: "'JetBrains Mono', monospace", color: '#475569' }}>{p.geo}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* Signature & Authentication Line */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginTop: '64px', paddingTop: '20px', borderTop: '1px dashed #CBD5E1' }}>
        <div>
          <div style={{ fontSize: '11px', color: '#64748B' }}>VERIFIED BY DISPATCH OFFICER:</div>
          <div style={{ fontSize: '13px', fontWeight: 700, color: '#0F172A', marginTop: '4px' }}>Insp. R. Kumar</div>
          <div style={{ fontSize: '11px', color: '#475569' }}>Control Room · Delhi Police Headquarters</div>
        </div>
        <div style={{ textAlign: 'center', width: '220px' }}>
          <div style={{ height: '40px', borderBottom: '1px solid #0F172A', marginBottom: '6px' }} />
          <div style={{ fontSize: '11px', color: '#64748B', textTransform: 'uppercase' }}>Officer Signature & Seal</div>
        </div>
      </div>
    </div>
  );
}
