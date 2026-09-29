'use client';

import React from 'react';
import { useTrafficStore } from '@/stores/useTrafficStore';
import { MetricCard } from '@/components/ui/MetricCard';
import { Car, Gauge, AlertOctagon, CloudRain, Clock } from 'lucide-react';

export function CorridorOverview() {
  const { overview, windowMinutes, setWindowMinutes } = useTrafficStore();

  const windows = [
    { label: '15 MIN', val: 15 },
    { label: '1 HOUR', val: 60 },
    { label: '24 HOURS', val: 1440 },
  ];

  return (
    <div className="space-y-3">
      {/* Time Window Selector Bar */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-1.5 text-xs font-mono text-slate-500">
          <Clock className="w-3.5 h-3.5 text-navy-900" />
          <span className="font-heading font-bold uppercase tracking-wider text-navy-950">
            Arterial Corridors Telemetry Window:
          </span>
        </div>

        <div className="flex items-center gap-1 bg-tint p-1 rounded-[3px] border border-border-warm">
          {windows.map((w) => (
            <button
              key={w.val}
              onClick={() => setWindowMinutes(w.val)}
              className={`px-3 py-1 text-xs font-mono font-bold rounded-[2px] transition-colors ${
                windowMinutes === w.val
                  ? 'bg-navy-900 text-white shadow-sm'
                  : 'text-slate-600 hover:text-navy-900 hover:bg-surface'
              }`}
            >
              {w.label}
            </button>
          ))}
        </div>
      </div>

      {/* 4 Primary KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        <MetricCard
          title="Monitored Vehicle Volume"
          value={overview?.distinct_tracks?.toLocaleString() || '524,000'}
          unit="Vehicles"
          subtitle="Estimated flow rate: 21,833 / hr"
          delta={{ value: '+3.4% FLOW', isPositive: true }}
          icon={Car}
        />

        <MetricCard
          title="Average Arterial Velocity"
          value={overview?.avg_speed_kmh?.toFixed(1) || '38.2'}
          unit="km/h"
          subtitle="Target city speed: 50.0 km/h"
          delta={{ value: '-5.1% PEAK SLOW', isPositive: false }}
          icon={Gauge}
          variant="saffron"
        />

        <MetricCard
          title="Critical Bottlenecks"
          value="3"
          unit="Corridors"
          subtitle="Ashram, Mukarba, DND Flyway"
          delta={{ value: 'GRIDLOCK FLAGGED', isPositive: false }}
          icon={AlertOctagon}
          variant="alert"
        />

        <MetricCard
          title="Estimated CO₂ Footprint"
          value={(overview?.estimated_co2_kg ? overview.estimated_co2_kg / 1000 : 142.5).toFixed(1)}
          unit="Metric Tons"
          subtitle="Excess fuel idling emissions"
          delta={{ value: 'POTENTIAL -18% VIA AI', isPositive: true }}
          icon={CloudRain}
          variant="clearance"
        />
      </div>
    </div>
  );
}
