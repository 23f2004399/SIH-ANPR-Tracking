'use client';

import React from 'react';
import { BarChart3, TrendingUp } from 'lucide-react';

interface HourlyDataPoint {
  hour: string;
  volume: number;
  avgSpeed: number;
}

const HOURLY_FLOW: HourlyDataPoint[] = [
  { hour: '06:00', volume: 6200, avgSpeed: 64 },
  { hour: '07:00', volume: 11400, avgSpeed: 52 },
  { hour: '08:00', volume: 22800, avgSpeed: 28 },
  { hour: '09:00', volume: 28400, avgSpeed: 19 },
  { hour: '10:00', volume: 26100, avgSpeed: 22 },
  { hour: '11:00', volume: 19800, avgSpeed: 38 },
  { hour: '12:00', volume: 17200, avgSpeed: 44 },
  { hour: '13:00', volume: 16500, avgSpeed: 46 },
  { hour: '14:00', volume: 18900, avgSpeed: 41 },
  { hour: '15:00', volume: 21300, avgSpeed: 35 },
  { hour: '16:00', volume: 24900, avgSpeed: 27 },
  { hour: '17:00', volume: 29800, avgSpeed: 18 },
  { hour: '18:00', volume: 31200, avgSpeed: 16 },
  { hour: '19:00', volume: 27500, avgSpeed: 21 },
  { hour: '20:00', volume: 21000, avgSpeed: 34 },
  { hour: '21:00', volume: 14200, avgSpeed: 51 },
];

export function HistoryAnalyticsChart() {
  const maxVolume = Math.max(...HOURLY_FLOW.map((d) => d.volume));

  return (
    <div className="bg-surface border border-border-warm rounded-[4px] p-4 shadow-gov-sm flex flex-col">
      <div className="flex items-center justify-between pb-3 mb-3 border-b border-border-warm">
        <div className="flex items-center gap-2">
          <BarChart3 className="w-4 h-4 text-navy-900" />
          <h4 className="font-heading font-bold text-xs uppercase tracking-wider text-navy-950">
            Corridor Hourly Inflow & Velocity Curve (24h Trend)
          </h4>
        </div>
        <div className="flex items-center gap-3 text-xs font-mono">
          <span className="flex items-center gap-1.5 text-navy-900 font-semibold">
            <span className="w-2.5 h-2.5 bg-navy-900 rounded-[1px]" /> Vehicle Volume
          </span>
          <span className="flex items-center gap-1.5 text-saffron-600 font-semibold">
            <span className="w-2.5 h-2.5 bg-saffron-600 rounded-full" /> Speed (km/h)
          </span>
        </div>
      </div>

      {/* High-Density Bar & Trend Chart */}
      <div className="h-44 flex items-end gap-1.5 pt-4 pb-2 px-1">
        {HOURLY_FLOW.map((item) => {
          const heightPct = Math.round((item.volume / maxVolume) * 100);
          const isPeak = item.avgSpeed < 20;

          return (
            <div
              key={item.hour}
              className="flex-1 flex flex-col items-center h-full justify-end group relative"
            >
              {/* Tooltip Hover */}
              <div className="absolute -top-12 opacity-0 group-hover:opacity-100 transition-opacity bg-navy-950 text-white text-[10px] font-mono px-2 py-1 rounded shadow-md pointer-events-none z-20 whitespace-nowrap">
                <div>{item.hour} IST</div>
                <div>Vol: {item.volume.toLocaleString()}</div>
                <div>Avg: {item.avgSpeed} km/h</div>
              </div>

              {/* Speed Marker Dot */}
              <div
                className="w-1.5 h-1.5 rounded-full bg-saffron-600 mb-1 z-10 transition-transform group-hover:scale-150"
                style={{ marginBottom: `${Math.round((item.avgSpeed / 70) * 80)}px` }}
              />

              {/* Volume Bar */}
              <div
                className={`w-full rounded-t-[2px] transition-all ${
                  isPeak ? 'bg-crimson-700/80 group-hover:bg-crimson-700' : 'bg-navy-900/80 group-hover:bg-navy-900'
                }`}
                style={{ height: `${heightPct}%` }}
              />

              {/* X Axis Label */}
              <span className="text-[9px] font-mono text-slate-400 mt-1 truncate">
                {item.hour.slice(0, 2)}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
