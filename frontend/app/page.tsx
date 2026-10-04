'use client';

import React, { useState } from 'react';
import Header from '@/components/Header';
import PoliceView from '@/components/PoliceView';
import UrbanView from '@/components/UrbanView';
import PrintDossier from '@/components/PrintDossier';
import { AppMode, PoliceViewMode, AlertNotification, RoutePoint } from '@/types';

const DEFAULT_ROUTE: RoutePoint[] = [
  { n: 1, cam: 'CAM-02', street: 'Wazirpur Industrial Area', time: '14:08', speed: '45 km/h', conf: '98.2%', geo: '28.691, 77.158', x: 18, y: 72 },
  { n: 2, cam: 'CAM-14', street: 'Shalimar Bagh Metro', time: '14:20', speed: '52 km/h', conf: '96.5%', geo: '28.701, 77.164', x: 38, y: 52 },
  { n: 3, cam: 'CAM-26', street: 'Outer Ring Rd, Pitampura', time: '14:32', speed: '38 km/h', conf: '98.9%', geo: '28.703, 77.131', x: 58, y: 44 },
  { n: 4, cam: 'CAM-41', street: 'Rohini Sector 8', time: '14:45', speed: 'Stopped · 12 min', conf: '94.1%', geo: '28.718, 77.112', x: 80, y: 22 },
];

export default function Home() {
  const [mode, setMode] = useState<AppMode>('police');
  const [plate, setPlate] = useState<string>('');
  const [selectedRouteIndex, setSelectedRouteIndex] = useState<number>(2);
  const [policeViewMode, setPoliceViewMode] = useState<PoliceViewMode>('empty');

  const handleSelectAlert = (alert: AlertNotification, index: number) => {
    setMode('police');
    setPlate(alert.plate);
    setPoliceViewMode('grid');
    setSelectedRouteIndex(index % DEFAULT_ROUTE.length);
  };

  const handleExportPdf = () => {
    if (typeof window !== 'undefined') {
      window.print();
    }
  };

  return (
    <div className="min-h-screen bg-[#F4F5F7] flex flex-col">
      {/* Screen Interactive App Container */}
      <div className="flex flex-col flex-1">
        <Header
          mode={mode}
          onModeChange={setMode}
          onSelectAlert={handleSelectAlert}
        />

        {mode === 'police' ? (
          <PoliceView
            currentPlate={plate}
            onPlateChange={setPlate}
            onExportPdf={handleExportPdf}
            selectedRouteIndex={selectedRouteIndex}
            onSelectRouteIndex={setSelectedRouteIndex}
            viewMode={policeViewMode}
            onViewModeChange={setPoliceViewMode}
          />
        ) : (
          <UrbanView />
        )}
      </div>

    </div>
  );
}
