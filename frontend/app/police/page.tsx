'use client';

import React, { useEffect } from 'react';
import dynamic from 'next/dynamic';
import { useVehicleStore } from '@/stores/useVehicleStore';
import { PlateSearchBar } from '@/components/police/PlateSearchBar';
import { HotlistAlertBanner } from '@/components/police/HotlistAlertBanner';
import { CctvHudPlayer } from '@/components/police/CctvHudPlayer';
import { EvidenceDossier } from '@/components/police/EvidenceDossier';
import { HistoryTable } from '@/components/police/HistoryTable';
import { SimilarVehiclesModal } from '@/components/police/SimilarVehiclesModal';

// Dynamic import with SSR disabled for Leaflet map
const SuspectTrajectoryMap = dynamic(
  () =>
    import('@/components/police/SuspectTrajectoryMap').then(
      (mod) => mod.SuspectTrajectoryMap
    ),
  {
    ssr: false,
    loading: () => (
      <div className="w-full h-80 bg-tint rounded flex items-center justify-center font-mono text-xs text-slate-400">
        INITIALIZING CARTO-TRACE ENGINE...
      </div>
    ),
  }
);

export default function PoliceSurveillancePage() {
  const { initDefaultTrack } = useVehicleStore();

  useEffect(() => {
    initDefaultTrack('HR 26 CX 9021');
  }, [initDefaultTrack]);

  return (
    <div className="space-y-4">
      {/* Search Input Bar */}
      <PlateSearchBar />

      {/* Hotlist Intercept Alert Banner */}
      <HotlistAlertBanner />

      {/* Main Operational 2-Column Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-start">
        {/* Left Column: Tactical CCTV Reticle Player + Leaflet Trajectory Cartography */}
        <div className="lg:col-span-8 space-y-4">
          <CctvHudPlayer />
          <div className="h-[360px]">
            <SuspectTrajectoryMap />
          </div>
        </div>

        {/* Right Rail: Forensic Evidence Dossier + VAHAN 4.0 Sync */}
        <div className="lg:col-span-4">
          <EvidenceDossier />
        </div>
      </div>

      {/* Chronological Multi-Camera Observations TanStack Table */}
      <div className="mt-4">
        <HistoryTable />
      </div>

      {/* Re-ID Vector Similarity Modal */}
      <SimilarVehiclesModal />
    </div>
  );
}
