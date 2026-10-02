'use client';

import React, { useState, useEffect, useRef } from 'react';
import { AppMode, AlertNotification } from '@/types';

interface HeaderProps {
  mode: AppMode;
  onModeChange: (mode: AppMode) => void;
  onSelectAlert: (alert: AlertNotification, index: number) => void;
  activeNodeLabel?: string;
}

export const NOTIFICATIONS: AlertNotification[] = [
  {
    kind: 'CLONED PLATE',
    plate: 'DL 01 AB 1234',
    time: '14:46',
    detail: 'Duplicate scan at Cam 01 and Cam 500, 50 km apart, within 58 s.',
    c: '#DC2626',
  },
  {
    kind: 'MISSING PLATE',
    plate: 'RE-ID #8842',
    time: '14:39',
    detail: 'Silver hatchback with no plate at Node 26, Pitampura. Re-ID match 92%.',
    c: '#D97706',
  },
  {
    kind: 'BLACKLIST HIT',
    plate: 'HR 26 CX 9021',
    time: '14:12',
    detail: 'Hotlist vehicle crossed Cam 14, Shalimar Bagh. Jurisdiction alerted.',
    c: '#DC2626',
  },
];

export default function Header({
  mode,
  onModeChange,
  onSelectAlert,
  activeNodeLabel,
}: HeaderProps) {
  const [clock, setClock] = useState<string>('--:--:-- IST');
  const [notifOpen, setNotifOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const updateTime = () => {
      setClock(new Date().toLocaleTimeString('en-GB', { hour12: false }) + ' IST');
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setNotifOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const tabPolice =
    'background:transparent;border:none;border-bottom:2px solid ' +
    (mode === 'police' ? '#0F172A' : 'transparent') +
    ';color:' +
    (mode === 'police' ? '#0F172A' : '#64748B') +
    ';padding:11px 2px;margin-right:20px;font-size:13px;font-weight:' +
    (mode === 'police' ? '600' : '500') +
    ';cursor:pointer;white-space:nowrap;transition:.15s';

  const tabUrban =
    'background:transparent;border:none;border-bottom:2px solid ' +
    (mode === 'urban' ? '#0F172A' : 'transparent') +
    ';color:' +
    (mode === 'urban' ? '#0F172A' : '#64748B') +
    ';padding:11px 2px;margin-right:20px;font-size:13px;font-weight:' +
    (mode === 'urban' ? '600' : '500') +
    ';cursor:pointer;white-space:nowrap;transition:.15s';

  const bellStyle: React.CSSProperties = {
    position: 'relative',
    display: 'flex',
    width: '30px',
    height: '30px',
    alignItems: 'center',
    justifyContent: 'center',
    border: `1px solid ${notifOpen ? '#94A3B8' : '#E2E4E8'}`,
    borderRadius: '5px',
    background: notifOpen ? '#EEF2F6' : '#FFFFFF',
    cursor: 'pointer',
    padding: 0,
  };

  const contextLabel =
    mode === 'police'
      ? (activeNodeLabel || 'NODE 26 · OUTER RING RD · NEW DELHI')
      : 'NEW DELHI · NCR · 24H WINDOW';

  return (
    <header style={{ background: '#FFFFFF', borderBottom: '1px solid #E2E4E8', position: 'sticky', top: 0, zIndex: 40 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '20px 28px', padding: '11px 22px', flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', minWidth: 0 }}>
          <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '26px', height: '26px', borderRadius: '5px', background: '#0F172A', flex: 'none' }}>
            <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="#FFFFFF" strokeWidth="1.5">
              <circle cx="8" cy="8" r="2.2" />
              <path d="M8 1v2M8 13v2M1 8h2M13 8h2" />
              <circle cx="8" cy="8" r="6" strokeOpacity=".45" />
            </svg>
          </span>
          <span style={{ display: 'flex', flexDirection: 'column', lineHeight: 1.2, minWidth: 0 }}>
            <span style={{ fontSize: '14.5px', fontWeight: 600, letterSpacing: '-.015em', whiteSpace: 'nowrap' }}>ZyroTrace AI</span>
            <span style={{ fontSize: '10.5px', color: '#64748B', whiteSpace: 'nowrap' }}>Zyrodev · Bharat Electronics Ltd · PS-26127</span>
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '18px', fontSize: '12px', color: '#64748B', flexWrap: 'wrap' }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '8px', whiteSpace: 'nowrap' }}>
            <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#059669', animation: 'zbreathe 2.4s ease-in-out infinite' }} />
            <span style={{ fontFamily: "'JetBrains Mono', monospace", color: '#0F172A', fontSize: '11.5px' }}>4,812</span>
            <span>of 4,850 nodes online</span>
          </span>
          <span
            suppressHydrationWarning
            style={{ fontFamily: "'JetBrains Mono', monospace", color: '#334155', fontSize: '11.5px', whiteSpace: 'nowrap', paddingLeft: '18px', borderLeft: '1px solid #E2E4E8' }}
          >
            {clock}
          </span>
          <div ref={dropdownRef} style={{ position: 'relative' }}>
            <button
              onClick={() => setNotifOpen((prev) => !prev)}
              style={bellStyle}
              aria-label="Toggle notifications"
            >
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#334155" strokeWidth="1.7">
                <path d="M18 8a6 6 0 1 0-12 0c0 7-3 9-3 9h18s-3-2-3-9" />
                <path d="M13.7 21a2 2 0 0 1-3.4 0" />
              </svg>
              <span style={{ position: 'absolute', top: '-6px', right: '-6px', minWidth: '15px', height: '15px', padding: '0 4px', borderRadius: '4px', background: '#DC2626', color: '#FFFFFF', fontFamily: "'JetBrains Mono', monospace", fontSize: '9.5px', fontWeight: 600, display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1.5px solid #FFFFFF' }}>
                3
              </span>
            </button>

            {notifOpen && (
              <div style={{ position: 'absolute', right: 0, top: '38px', width: '352px', maxWidth: '80vw', background: '#FFFFFF', border: '1px solid #E2E4E8', borderRadius: '6px', boxShadow: '0 8px 24px rgba(15,23,42,.10)', zIndex: 60, overflow: 'hidden' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 14px', borderBottom: '1px solid #E2E4E8', background: '#FBFCFD' }}>
                  <span style={{ fontSize: '11px', fontWeight: 600, letterSpacing: '.08em', textTransform: 'uppercase', color: '#334155' }}>Alert Center</span>
                  <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '10px', color: '#64748B' }}>3 unread</span>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', maxHeight: '352px', overflow: 'auto' }}>
                  {NOTIFICATIONS.map((a, i) => (
                    <button
                      key={i}
                      onClick={() => {
                        onSelectAlert(a, i);
                        setNotifOpen(false);
                      }}
                      style={{
                        display: 'grid',
                        gridTemplateColumns: 'auto minmax(0,1fr)',
                        gap: '4px 11px',
                        textAlign: 'left',
                        width: '100%',
                        background: 'transparent',
                        border: 'none',
                        borderBottom: '1px solid #EEF1F4',
                        padding: '12px 14px',
                        cursor: 'pointer',
                      }}
                      onMouseEnter={(e) => (e.currentTarget.style.background = '#F7F9FB')}
                      onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
                    >
                      <span style={{ flex: 'none', width: '7px', height: '7px', borderRadius: '50%', marginTop: '5px', background: a.c }} />
                      <span style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', gap: '10px' }}>
                        <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '9.5px', fontWeight: 600, letterSpacing: '.08em', color: a.c }}>{a.kind}</span>
                        <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '10px', color: '#94A3B8', flex: 'none' }}>{a.time}</span>
                      </span>
                      <span />
                      <span style={{ display: 'flex', flexDirection: 'column', gap: '4px', minWidth: 0 }}>
                        <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '12px', color: '#0F172A', fontWeight: 500, letterSpacing: '.04em' }}>{a.plate}</span>
                        <span style={{ fontSize: '11.5px', color: '#64748B', lineHeight: 1.5, textWrap: 'pretty' }}>{a.detail}</span>
                        <span style={{ fontSize: '11px', color: '#0891B2', fontWeight: 500 }}>Open movement log →</span>
                      </span>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          <span style={{ display: 'flex', alignItems: 'center', gap: '9px', paddingLeft: '18px', borderLeft: '1px solid #E2E4E8' }}>
            <span style={{ width: '26px', height: '26px', borderRadius: '50%', background: '#EEF2F6', border: '1px solid #E2E4E8', color: '#334155', fontSize: '10.5px', fontWeight: 600, display: 'flex', alignItems: 'center', justifyContent: 'center', letterSpacing: '.02em' }}>RK</span>
            <span style={{ display: 'flex', flexDirection: 'column', lineHeight: 1.25 }}>
              <span style={{ color: '#0F172A', fontSize: '11.5px', fontWeight: 500 }}>Insp. R. Kumar</span>
              <span style={{ fontSize: '10px', color: '#94A3B8' }}>Control Room · Delhi</span>
            </span>
          </span>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', gap: '16px', padding: '0 22px', borderTop: '1px solid #EEF1F4', flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', gap: '2px' }}>
          <button
            onClick={() => onModeChange('police')}
            style={{ ...inlineToObj(tabPolice) }}
          >
            Police Surveillance
          </button>
          <button
            onClick={() => onModeChange('urban')}
            style={{ ...inlineToObj(tabUrban) }}
          >
            City Traffic Analytics
          </button>
        </div>
        <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '10px', letterSpacing: '.06em', color: '#94A3B8', padding: '11px 0', whiteSpace: 'nowrap' }}>
          {contextLabel}
        </span>
      </div>
    </header>
  );
}

function inlineToObj(css: string): React.CSSProperties {
  const style: Record<string, string> = {};
  css.split(';').forEach((rule) => {
    const colonIdx = rule.indexOf(':');
    if (colonIdx !== -1) {
      const k = rule.slice(0, colonIdx).trim();
      const v = rule.slice(colonIdx + 1).trim();
      if (k && v) {
        const camel = k.replace(/-([a-z])/g, (_, l) => l.toUpperCase());
        style[camel] = v;
      }
    }
  });
  return style as React.CSSProperties;
}
