'use client';

import React, { useEffect } from 'react';
import dynamic from 'next/dynamic';
import { useTrafficStore } from '@/stores/useTrafficStore';
import { CorridorOverview } from '@/components/traffic/CorridorOverview';
import { TrafficAdvisor } from '@/components/traffic/TrafficAdvisor';
import { SegmentTable } from '@/components/traffic/SegmentTable';
import { HistoryAnalyticsChart } from '@/components/traffic/HistoryAnalyticsChart';

// Dynamic import with SSR disabled for Leaflet congestion heatmap
const CongestionMap = dynamic(
  () =>
    import('@/components/traffic/CongestionMap').then(
      (mod) => mod.CongestionMap
    ),
  {
    ssr: false,
    loading: () => (
      <div className="w-full h-96 bg-tint rounded flex items-center justify-center font-mono text-xs text-slate-400">
        LOADING ARTERIAL CONGESTION HEATMAP...
      </div>
    ),
  }
);

export default function TrafficIntelligencePage() {
  const { fetchTrafficData } = useTrafficStore();

  useEffect(() => {
    fetchTrafficData();
  }, [fetchTrafficData]);

  return (
    <div className="space-y-4">
      {/* City-Wide Corridor KPIs & Time Window Switcher */}
      <CorridorOverview />

      {/* Main Grid: Arterial Heatmap & Smart City AI Advisories */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-start">
        <div className="lg:col-span-7 h-[420px]">
          <CongestionMap />
        </div>

        <div className="lg:col-span-5">
          <TrafficAdvisor />
        </div>
      </div>

      {/* Corridor Segment Bottlenecks Table */}
      <SegmentTable />

      {/* 24-Hour Velocity & Volume Flow Curves */}
      <HistoryAnalyticsChart />
    </div>
  );
}
