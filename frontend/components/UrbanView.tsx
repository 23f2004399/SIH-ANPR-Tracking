'use client';

import React, { useState, useEffect } from 'react';
import {
  UrbanStat,
  Corridor,
  CorridorMix,
  FleetItem,
  EmissionItem,
  SuggestionItem,
  TrafficAggregate,
} from '@/types';
import { getTrafficOverview, getTrafficSegments, getCityTrafficAnalytics } from '@/lib/api';

const DEFAULT_STATS: UrbanStat[] = [
  {
    label: 'Congestion Level',
    value: '64%',
    delta: '+9%',
    note: 'Peak hours vs. last week',
    textColor: '#991B1B',
    bgColor: '#FEF2F2',
    borderColor: '#FECACA',
  },
  {
    label: 'Active Choke Points',
    value: '5',
    delta: '+2',
    note: 'Corridors needing intervention',
    textColor: '#991B1B',
    bgColor: '#FEF2F2',
    borderColor: '#FECACA',
  },
  {
    label: 'Daily Vehicles Tracked',
    value: '524,000',
    delta: '+3.1%',
    note: 'Across 4,812 live nodes',
    textColor: '#334155',
    bgColor: '#F1F4F7',
    borderColor: '#E2E4E8',
  },
  {
    label: 'Est. CO₂ from Idling',
    value: '1,840 T',
    delta: '−4%',
    note: 'Monthly, red corridors only',
    textColor: '#065F46',
    bgColor: '#ECFDF5',
    borderColor: '#A7F3D0',
  },
];

const DEFAULT_CORRIDORS: Corridor[] = [
  {
    name: 'Outer Ring Rd (S)',
    transit: '9.4 min / 2.1 km',
    tag: 'Severe — widen lane',
    textColor: '#991B1B',
    bgColor: '#FEF2F2',
    borderColor: '#FECACA',
  },
  {
    name: 'Madhuban Chowk',
    transit: '5.1 min / 1.4 km',
    tag: 'Slow — retime signal',
    textColor: '#92400E',
    bgColor: '#FFFBEB',
    borderColor: '#FDE68A',
  },
  {
    name: 'NH-44 Corridor',
    transit: '2.2 min / 2.0 km',
    tag: 'Clear — nominal',
    textColor: '#065F46',
    bgColor: '#ECFDF5',
    borderColor: '#A7F3D0',
  },
];

const DEFAULT_CORRIDOR_MIX: CorridorMix[] = [
  { name: 'Outer Ring Rd (S)', total: '84,200 veh', p: [52, 31, 11, 6] },
  { name: 'NH-44 Corridor', total: '61,500 veh', p: [33, 38, 22, 7] },
  { name: 'Madhuban Chowk', total: '47,900 veh', p: [48, 36, 7, 9] },
];

const DEFAULT_FLEET: FleetItem[] = [
  { name: 'Two-Wheelers', pct: '45%', c: '#0891B2' },
  { name: 'Private Cars', pct: '35%', c: '#0F172A' },
  { name: 'Commercial LCV / Trucks', pct: '12%', c: '#D97706' },
  { name: 'City Buses', pct: '8%', c: '#94A3B8' },
];

const DEFAULT_EMISSIONS: EmissionItem[] = [
  { name: 'Outer Ring Rd (S) · 3,120 idle-h', tons: '812 T', w: 100, c: '#DC2626' },
  { name: 'Madhuban Chowk · 2,050 idle-h', tons: '534 T', w: 66, c: '#D97706' },
  { name: 'NH-44 Corridor · 1,180 idle-h', tons: '307 T', w: 38, c: '#059669' },
];

const DEFAULT_SUGGESTIONS: SuggestionItem[] = [
  {
    text: 'Increase green-light duration by 20 s at Pitampura Junction to clear the 18:00–19:30 build-up.',
    impact: '−14% IDLING',
    scope: 'Signal control',
  },
  {
    text: 'Divert heavy multi-axle trucks to the Outer Bypass between 17:00 and 20:00.',
    impact: '−15% CO₂',
    scope: 'Traffic police order',
  },
  {
    text: 'Add a dedicated two-wheeler lane on Ring Rd (S) — 45% of flow occupies 22% of capacity.',
    impact: '+11% THROUGHPUT',
    scope: 'Infrastructure',
  },
];

export default function UrbanView() {
  const [urbanGen, setUrbanGen] = useState<boolean>(true);
  const [city, setCity] = useState<string>('New Delhi — NCR');
  const [stats, setStats] = useState<UrbanStat[]>(DEFAULT_STATS);
  const [corridors, setCorridors] = useState<Corridor[]>(DEFAULT_CORRIDORS);
  const [corridorMix, setCorridorMix] = useState<CorridorMix[]>(DEFAULT_CORRIDOR_MIX);
  const [fleet, setFleet] = useState<FleetItem[]>(DEFAULT_FLEET);
  const [emissions, setEmissions] = useState<EmissionItem[]>(DEFAULT_EMISSIONS);
  const [suggestions, setSuggestions] = useState<SuggestionItem[]>(DEFAULT_SUGGESTIONS);
  const [totalVehicles, setTotalVehicles] = useState<string>('524K');
  const [totalIdleHours, setTotalIdleHours] = useState<string>('7,420 h');
  const [totalCo2Tons, setTotalCo2Tons] = useState<string>('1,840 T');
  const [nodeCount, setNodeCount] = useState<number>(4812);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  useEffect(() => {
    setIsLoading(true);
    const cityName = city.split(' — ')[0];
    getCityTrafficAnalytics(cityName)
      .then((data) => {
        if (data) {
          if (data.stats && data.stats.length > 0) setStats(data.stats);
          if (data.corridors && data.corridors.length > 0) setCorridors(data.corridors);
          if (data.corridor_mix && data.corridor_mix.length > 0) setCorridorMix(data.corridor_mix);
          if (data.fleet && data.fleet.length > 0) setFleet(data.fleet);
          if (data.emissions && data.emissions.length > 0) setEmissions(data.emissions);
          if (data.suggestions && data.suggestions.length > 0) setSuggestions(data.suggestions);
          if (data.total_vehicles_formatted) setTotalVehicles(data.total_vehicles_formatted);
          if (data.total_idle_hours_formatted) setTotalIdleHours(data.total_idle_hours_formatted);
          if (data.total_co2_formatted) setTotalCo2Tons(data.total_co2_formatted);
          if (data.node_count) setNodeCount(data.node_count);
        }
      })
      .catch((err) => {
        console.warn('Backend city traffic analytics fallback:', err);
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, [city]);

  const A = '#0891B2';
  const cs = [A, '#0F172A', '#D97706', '#94A3B8'];

  // Compute donut gradient angles from dynamic fleet percentages
  const p0 = parseInt(fleet[0]?.pct || '45', 10);
  const p1 = parseInt(fleet[1]?.pct || '35', 10);
  const p2 = parseInt(fleet[2]?.pct || '12', 10);
  const c0 = fleet[0]?.c || '#0891B2';
  const c1 = fleet[1]?.c || '#0F172A';
  const c2 = fleet[2]?.c || '#D97706';
  const c3 = fleet[3]?.c || '#94A3B8';
  const donutGradient = `conic-gradient(${c0} 0 ${p0}%, ${c1} ${p0}% ${p0 + p1}%, ${c2} ${p0 + p1}% ${p0 + p1 + p2}%, ${c3} ${p0 + p1 + p2}% 100%)`;

  if (!urbanGen) {
    return (
      <div style={{ padding: '18px 22px 32px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
        <div style={{ background: '#FFFFFF', border: '1px solid #E2E4E8', borderRadius: '6px', padding: '92px 24px', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '22px', textAlign: 'center' }}>
          <svg width="176" height="104" viewBox="0 0 176 104" fill="none">
            <g stroke="#E2E4E8" strokeWidth="1">
              <path d="M0 30h176M0 56h176M0 82h176M36 4v96M84 4v96M130 4v96" />
            </g>
            <g stroke="#0891B2" strokeWidth="1.6">
              <path d="M8 56h160" />
              <path d="M84 10v88" />
            </g>
            <g fill="#0F172A">
              <circle cx="84" cy="56" r="3.4" />
              <circle cx="36" cy="30" r="2.2" />
              <circle cx="130" cy="82" r="2.2" />
              <circle cx="130" cy="30" r="2.2" />
              <circle cx="36" cy="82" r="2.2" />
            </g>
          </svg>
          <div style={{ maxWidth: '420px' }}>
            <div style={{ fontSize: '14.5px', fontWeight: 600, color: '#0F172A' }}>No city selected</div>
            <div style={{ fontSize: '12.5px', color: '#64748B', lineHeight: 1.6, marginTop: '6px', textWrap: 'pretty' }}>
              Choose a city to generate macro congestion, corridor transit, fleet-mix and emission statistics across all active camera nodes.
            </div>
          </div>
          <div style={{ display: 'flex', gap: '9px', flexWrap: 'wrap', justifyContent: 'center' }}>
            <select
              value={city}
              onChange={(e) => setCity(e.target.value)}
              style={{ appearance: 'none', background: '#FFFFFF', border: '1px solid #D8DDE4', color: '#0F172A', borderRadius: '5px', padding: '10px 15px', fontSize: '13px', outline: 'none', cursor: 'pointer' }}
            >
              <option>Chennai — OMR Corridor</option>
              <option>New Delhi — NCR</option>
              <option>Mumbai — MMR</option>
              <option>Bengaluru — BBMP</option>
            </select>
            <button
              onClick={() => setUrbanGen(true)}
              style={{ background: '#0F172A', color: '#FFFFFF', border: 'none', borderRadius: '5px', padding: '10px 18px', fontSize: '13px', fontWeight: 500, cursor: 'pointer' }}
              onMouseEnter={(e) => (e.currentTarget.style.background = '#1E293B')}
              onMouseLeave={(e) => (e.currentTarget.style.background = '#0F172A')}
            >
              Generate statistics
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ padding: '18px 22px 32px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
      {/* Title & Filter Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', gap: '14px', flexWrap: 'wrap' }}>
        <div>
          <div style={{ fontSize: '15.5px', fontWeight: 600, letterSpacing: '-.015em' }}>
            Urban Traffic Intelligence · {city.split(' — ')[0]}
          </div>
          <div style={{ fontSize: '12px', color: '#64748B', marginTop: '3px' }}>
            Macro congestion, fleet mix and emissions · rolling 24-hour window
          </div>
        </div>
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', alignItems: 'center', fontFamily: "'JetBrains Mono', monospace", fontSize: '10px', color: '#64748B' }}>
          <span style={{ background: '#FFFFFF', border: '1px solid #E2E4E8', borderRadius: '4px', padding: '6px 9px', whiteSpace: 'nowrap' }}>
            WINDOW 24H
          </span>
          <span style={{ background: '#FFFFFF', border: '1px solid #E2E4E8', borderRadius: '4px', padding: '6px 9px', whiteSpace: 'nowrap' }}>
            NODES {nodeCount.toLocaleString()}
          </span>
          <button
            onClick={() => setUrbanGen(false)}
            style={{ background: '#FFFFFF', border: '1px solid #E2E4E8', color: '#64748B', borderRadius: '4px', padding: '6px 9px', fontFamily: "'JetBrains Mono', monospace", fontSize: '10px', cursor: 'pointer', whiteSpace: 'nowrap' }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = '#EEF2F6';
              e.currentTarget.style.color = '#0F172A';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = '#FFFFFF';
              e.currentTarget.style.color = '#64748B';
            }}
          >
            CHANGE CITY
          </button>
        </div>
      </div>

      {/* 4 Metric KPI Cards */}
      <section style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(198px, 1fr))', gap: '12px' }}>
        {stats.map((k, i) => (
          <div key={i} style={{ background: '#FFFFFF', border: '1px solid #E2E4E8', borderRadius: '6px', padding: '14px 15px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <span style={{ fontSize: '9.5px', letterSpacing: '.11em', textTransform: 'uppercase', color: '#94A3B8', fontWeight: 600 }}>
              {k.label}
            </span>
            <span style={{ display: 'flex', alignItems: 'baseline', gap: '8px', flexWrap: 'wrap' }}>
              <span style={{ fontSize: '26px', fontWeight: 600, letterSpacing: '-.03em', color: '#0F172A', lineHeight: 1 }}>
                {k.value}
              </span>
              <span
                style={{
                  fontFamily: "'JetBrains Mono', monospace",
                  fontSize: '9.5px',
                  fontWeight: 600,
                  color: k.textColor,
                  background: k.bgColor,
                  border: `1px solid ${k.borderColor}`,
                  borderRadius: '3px',
                  padding: '2px 5px',
                  whiteSpace: 'nowrap',
                }}
              >
                {k.delta}
              </span>
            </span>
            <span style={{ fontSize: '11.5px', color: '#64748B', textWrap: 'pretty' }}>
              {k.note}
            </span>
          </div>
        ))}
      </section>

      {/* 2 Column Section: Heatmap (6fr) & Analytics Breakdown (4fr) */}
      <section style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 6fr) minmax(300px, 4fr)', gap: '12px', alignItems: 'start' }}>
        {/* Left Column */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', minWidth: 0 }}>
          {/* Heatmap Card */}
          <div style={{ background: '#FFFFFF', border: '1px solid #E2E4E8', borderRadius: '6px', overflow: 'hidden' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '12px', flexWrap: 'wrap', padding: '12px 15px', borderBottom: '1px solid #EEF1F4' }}>
              <span style={{ fontSize: '13.5px', fontWeight: 600 }}>Congestion Heatmap & Flow Dynamics</span>
              <div style={{ display: 'flex', gap: '13px', fontSize: '11px', color: '#64748B' }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span style={{ width: '12px', height: '3px', background: '#059669' }} />
                  Clear
                </span>
                <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span style={{ width: '12px', height: '3px', background: '#D97706' }} />
                  Slow
                </span>
                <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span style={{ width: '12px', height: '3px', background: '#DC2626' }} />
                  Bottleneck
                </span>
              </div>
            </div>

            <div style={{ padding: '15px' }}>
              <div style={{ position: 'relative', border: '1px solid #E2E4E8', borderRadius: '5px', overflow: 'hidden', background: '#EDF0F3', aspectRatio: '16/10', minHeight: '320px' }}>
                <svg viewBox="0 0 160 100" style={{ position: 'absolute', inset: 0, width: '100%', height: '100%' }}>
                  <rect x="0" y="0" width="160" height="100" fill="#EDF0F3" />
                  <g fill="#E4E8ED">
                    <rect x="4" y="6" width="26" height="20" />
                    <rect x="36" y="4" width="30" height="14" />
                    <rect x="96" y="8" width="26" height="18" />
                    <rect x="132" y="30" width="26" height="24" />
                    <rect x="6" y="60" width="22" height="18" />
                    <rect x="40" y="80" width="34" height="16" />
                    <rect x="104" y="76" width="30" height="20" />
                  </g>
                  <rect x="112" y="56" width="22" height="16" fill="#E1EBE4" />
                  <path d="M0 96 C 38 90, 74 98, 118 90 S 148 82, 160 84" stroke="#DBE6EF" strokeWidth="4" fill="none" />
                  <g stroke="#DDE2E8" strokeWidth="5.6" fill="none" strokeLinecap="round">
                    <path d="M70 14 C 104 16, 122 34, 118 52 S 96 82, 66 80 S 30 62, 34 42 S 44 14, 70 14" />
                    <path d="M0 34 H160" />
                    <path d="M0 70 H160" />
                    <path d="M46 0 V100" />
                    <path d="M124 0 V100" />
                  </g>
                  <g stroke="#FFFFFF" strokeWidth="4" fill="none" strokeLinecap="round">
                    <path d="M70 14 C 104 16, 122 34, 118 52 S 96 82, 66 80 S 30 62, 34 42 S 44 14, 70 14" />
                    <path d="M0 34 H160" />
                    <path d="M0 70 H160" />
                    <path d="M46 0 V100" />
                    <path d="M124 0 V100" />
                  </g>
                  <g stroke="#FFFFFF" strokeWidth="1.8" fill="none">
                    <path d="M0 18 H160" />
                    <path d="M0 88 H160" />
                    <path d="M20 0 V100" />
                    <path d="M84 0 V100" />
                    <path d="M148 0 V100" />
                  </g>
                  <g fill="none" strokeLinecap="round" strokeWidth="2.6">
                    <path d="M118 52 C 114 68, 96 81, 66 80" stroke="#DC2626" />
                    <path d="M66 80 C 44 78, 33 66, 34 52" stroke="#D97706" />
                    <path d="M34 42 C 36 24, 48 14, 70 14 C 92 15, 108 22, 115 36" stroke="#059669" />
                    <path d="M124 0 V 34" stroke="#D97706" />
                    <path d="M124 70 V 100" stroke="#DC2626" />
                    <path d="M0 70 H 66" stroke="#059669" />
                    <path d="M84 80 V 100" stroke="#059669" />
                    <path d="M118 34 H 160" stroke="#DC2626" />
                  </g>
                  <g fill="#DC2626" opacity="0.10">
                    <circle cx="118" cy="52" r="11" />
                    <circle cx="124" cy="82" r="9" />
                    <circle cx="140" cy="34" r="7" />
                  </g>
                  <g fill="#0F172A">
                    <circle cx="118" cy="52" r="2.4" />
                    <circle cx="66" cy="80" r="2.4" />
                    <circle cx="34" cy="42" r="2.4" />
                  </g>
                </svg>

                <div style={{ position: 'absolute', left: '14px', top: '14px', background: 'rgba(255,255,255,.95)', border: '1px solid #E2E4E8', borderRadius: '5px', padding: '9px 11px', fontFamily: "'JetBrains Mono', monospace", fontSize: '9.5px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  {corridors.slice(0, 3).map((c, i) => (
                    <span key={i} style={{ display: 'flex', gap: '7px', alignItems: 'center' }}>
                      <span style={{ width: '6px', height: '6px', background: c.textColor, flex: 'none' }} />
                      <span style={{ color: '#334155' }}>{c.name.toUpperCase()} · {c.transit.split(' / ')[0]}</span>
                    </span>
                  ))}
                </div>
              </div>
            </div>

            <div style={{ borderTop: '1px solid #EEF1F4', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(168px, 1fr))' }}>
              {corridors.map((c, idx) => (
                <div key={idx} style={{ padding: '12px 15px', borderRight: '1px solid #EEF1F4', display: 'flex', flexDirection: 'column', gap: '6px', minWidth: 0 }}>
                  <span style={{ fontSize: '12.5px', color: '#0F172A', fontWeight: 500, textWrap: 'pretty' }}>{c.name}</span>
                  <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '10px', color: '#94A3B8' }}>TRANSIT {c.transit}</span>
                  <span
                    style={{
                      display: 'inline-block',
                      alignSelf: 'flex-start',
                      maxWidth: '100%',
                      fontSize: '10.5px',
                      lineHeight: 1.4,
                      color: c.textColor,
                      background: c.bgColor,
                      border: `1px solid ${c.borderColor}`,
                      borderRadius: '3px',
                      padding: '3px 6px',
                      textWrap: 'pretty',
                    }}
                  >
                    {c.tag}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Fleet Mix per Corridor */}
          <div style={{ background: '#FFFFFF', border: '1px solid #E2E4E8', borderRadius: '6px', overflow: 'hidden' }}>
            <div style={{ padding: '12px 15px', borderBottom: '1px solid #EEF1F4', display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', gap: '10px', flexWrap: 'wrap' }}>
              <span style={{ fontSize: '13.5px', fontWeight: 600 }}>Fleet Mix per Corridor</span>
              <span style={{ fontSize: '11px', color: '#94A3B8' }}>Share of classified detections</span>
            </div>
            <div style={{ padding: '14px 15px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
              {corridorMix.map((m, idx) => (
                <div key={idx} style={{ display: 'flex', flexDirection: 'column', gap: '7px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', gap: '10px' }}>
                    <span style={{ fontSize: '12.5px', color: '#334155', minWidth: 0 }}>{m.name}</span>
                    <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '10.5px', color: '#94A3B8', whiteSpace: 'nowrap', flex: 'none' }}>{m.total}</span>
                  </div>
                  <div style={{ display: 'flex', height: '8px', overflow: 'hidden', background: '#F1F4F7', borderRadius: '2px' }}>
                    <span style={{ display: 'block', height: '100%', width: `${m.p[0]}%`, background: cs[0] }} />
                    <span style={{ display: 'block', height: '100%', width: `${m.p[1]}%`, background: cs[1] }} />
                    <span style={{ display: 'block', height: '100%', width: `${m.p[2]}%`, background: cs[2] }} />
                    <span style={{ display: 'block', height: '100%', width: `${m.p[3]}%`, background: cs[3] }} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {/* Vehicle Classification Donut */}
          <div style={{ background: '#FFFFFF', border: '1px solid #E2E4E8', borderRadius: '6px', overflow: 'hidden' }}>
            <div style={{ padding: '12px 15px', borderBottom: '1px solid #EEF1F4', fontSize: '13.5px', fontWeight: 600 }}>
              Vehicle Classification
            </div>
            <div style={{ padding: '15px', display: 'flex', gap: '18px', alignItems: 'center', flexWrap: 'wrap' }}>
              <div style={{ position: 'relative', width: '118px', height: '118px', borderRadius: '50%', background: donutGradient, flex: 'none' }}>
                <div style={{ position: 'absolute', inset: '23px', borderRadius: '50%', background: '#FFFFFF', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                  <span style={{ fontSize: '16px', fontWeight: 600, letterSpacing: '-.02em' }}>{totalVehicles}</span>
                  <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '8.5px', color: '#94A3B8', letterSpacing: '.08em' }}>VEHICLES</span>
                </div>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', flex: '1 1 140px', minWidth: '140px' }}>
                {fleet.map((f, idx) => (
                  <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: '9px' }}>
                    <span style={{ flex: 'none', width: '8px', height: '8px', borderRadius: '2px', background: f.c }} />
                    <span style={{ fontSize: '12px', color: '#334155', flex: 1, minWidth: 0 }}>{f.name}</span>
                    <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '11.5px', color: '#0F172A', flex: 'none' }}>{f.pct}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Carbon Footprint from Idling */}
          <div style={{ background: '#FFFFFF', border: '1px solid #E2E4E8', borderRadius: '6px', overflow: 'hidden' }}>
            <div style={{ padding: '12px 15px', borderBottom: '1px solid #EEF1F4', fontSize: '13.5px', fontWeight: 600 }}>
              Carbon Footprint from Idling
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', borderBottom: '1px solid #EEF1F4' }}>
              <div style={{ padding: '12px 15px', borderRight: '1px solid #EEF1F4' }}>
                <div style={{ fontSize: '9.5px', letterSpacing: '.11em', textTransform: 'uppercase', color: '#94A3B8', fontWeight: 600 }}>Total idle time</div>
                <div style={{ fontSize: '20px', fontWeight: 600, letterSpacing: '-.02em', marginTop: '6px' }}>{totalIdleHours}</div>
              </div>
              <div style={{ padding: '12px 15px' }}>
                <div style={{ fontSize: '9.5px', letterSpacing: '.11em', textTransform: 'uppercase', color: '#94A3B8', fontWeight: 600 }}>CO₂ equivalent</div>
                <div style={{ fontSize: '20px', fontWeight: 600, letterSpacing: '-.02em', marginTop: '6px' }}>{totalCo2Tons}</div>
              </div>
            </div>
            <div style={{ padding: '14px 15px', display: 'flex', flexDirection: 'column', gap: '11px' }}>
              {emissions.map((e, idx) => (
                <div key={idx} style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', gap: '10px' }}>
                    <span style={{ fontSize: '11.5px', color: '#334155', minWidth: 0, textWrap: 'pretty' }}>{e.name}</span>
                    <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '10.5px', color: '#0F172A', whiteSpace: 'nowrap', flex: 'none' }}>{e.tons}</span>
                  </div>
                  <div style={{ height: '5px', background: '#F1F4F7', borderRadius: '2px', overflow: 'hidden' }}>
                    <span style={{ display: 'block', height: '100%', width: `${e.w}%`, background: e.c }} />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* AI Policy Recommendations */}
          <div style={{ background: '#FFFFFF', border: '1px solid #E2E4E8', borderRadius: '6px', overflow: 'hidden' }}>
            <div style={{ padding: '12px 15px', borderBottom: '1px solid #EEF1F4', display: 'flex', alignItems: 'center', gap: '9px' }}>
              <span style={{ width: '5px', height: '5px', borderRadius: '50%', background: '#0891B2' }} />
              <span style={{ fontSize: '13.5px', fontWeight: 600 }}>AI Policy Recommendations</span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              {suggestions.map((g, idx) => (
                <div key={idx} style={{ padding: '12px 15px', borderBottom: '1px solid #EEF1F4', display: 'flex', flexDirection: 'column', gap: '7px' }}>
                  <span style={{ fontSize: '12.5px', color: '#0F172A', lineHeight: 1.55, textWrap: 'pretty' }}>{g.text}</span>
                  <span style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
                    <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '9.5px', fontWeight: 600, color: '#065F46', background: '#ECFDF5', border: '1px solid #A7F3D0', borderRadius: '3px', padding: '3px 6px', whiteSpace: 'nowrap' }}>
                      {g.impact}
                    </span>
                    <span style={{ fontSize: '11px', color: '#94A3B8' }}>{g.scope}</span>
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
