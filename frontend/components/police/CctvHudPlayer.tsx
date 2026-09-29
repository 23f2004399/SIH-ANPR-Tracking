'use client';

import React, { useState, useEffect } from 'react';
import { useVehicleStore } from '@/stores/useVehicleStore';
import { Maximize2, Play, Pause, Camera, Crosshair, AlertCircle } from 'lucide-react';
import { formatIST } from '@/lib/utils';

export function CctvHudPlayer() {
  const { selectedObservation, selectedTrack, history } = useVehicleStore();
  const [isPlaying, setIsPlaying] = useState(true);
  const [msTime, setMsTime] = useState('');

  useEffect(() => {
    const updateClock = () => {
      const d = new Date();
      const base = d.toISOString().replace('T', ' ').slice(0, 19);
      const ms = String(d.getMilliseconds()).padStart(3, '0');
      setMsTime(`${base}.${ms} IST`);
    };
    updateClock();
    const timer = setInterval(updateClock, 120);
    return () => clearInterval(timer);
  }, []);

  const camName =
    selectedObservation?.camera_name || 'CAM-26 // GT KARNAL RD NH-44 (KM 14.2)';
  const plateText =
    selectedObservation?.plate_text || selectedTrack?.primary_plate || 'HR 26 CX 9021';
  const confidence = selectedObservation?.confidence
    ? Math.round(selectedObservation.confidence * 100)
    : 99;
  const speed = selectedObservation?.speed_kmh || 94;

  return (
    <div className="bg-navy-950 border border-border-warm rounded-[4px] overflow-hidden shadow-gov-md flex flex-col">
      {/* CCTV HUD Header Bar */}
      <div className="bg-navy-900 border-b border-navy-800 px-3.5 py-2 flex items-center justify-between text-xs font-mono text-slate-300">
        <div className="flex items-center gap-2">
          <Camera className="w-3.5 h-3.5 text-saffron-500" />
          <span className="font-bold text-white uppercase tracking-wider">
            {camName}
          </span>
          <span className="hidden sm:inline bg-navy-800 text-slate-400 px-1.5 py-0.2 rounded text-[10px]">
            NODE: {selectedObservation?.camera_id || 'CAM-26'}
          </span>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 text-rose-400 text-[11px] font-bold">
            <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping" />
            <span>REC // 1080p 30FPS</span>
          </div>
          <button
            onClick={() => setIsPlaying(!isPlaying)}
            className="text-slate-400 hover:text-white transition-colors"
            title={isPlaying ? 'Pause Feed' : 'Play Feed'}
          >
            {isPlaying ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {/* Optical Reticle Viewport */}
      <div className="relative w-full aspect-video bg-navy-950 overflow-hidden select-none">
        {/* Synthetic CCTV Optical Feed Simulation */}
        <div
          className="absolute inset-0 bg-cover bg-center filter grayscale-[30%] contrast-[115%]"
          style={{
            backgroundImage:
              'url("https://images.unsplash.com/photo-1506521781263-d8422e82f27a?auto=format&fit=crop&w=1200&q=80")',
          }}
        />

        {/* Tactical Scanlines & Vignette */}
        <div
          className="absolute inset-0 pointer-events-none opacity-25"
          style={{
            backgroundImage:
              'repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,0,0,0.5) 2px, rgba(0,0,0,0.5) 4px)',
          }}
        />
        <div className="absolute inset-0 bg-radial-gradient pointer-events-none opacity-40" />

        {/* Optical Reticle Corner Brackets */}
        <div className="absolute top-4 left-4 w-6 h-6 reticle-corner-tl pointer-events-none" />
        <div className="absolute top-4 right-4 w-6 h-6 reticle-corner-tr pointer-events-none" />
        <div className="absolute bottom-4 left-4 w-6 h-6 reticle-corner-bl pointer-events-none" />
        <div className="absolute bottom-4 right-4 w-6 h-6 reticle-corner-br pointer-events-none" />

        {/* Center Crosshairs */}
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none opacity-30">
          <Crosshair className="w-12 h-12 text-saffron-500" strokeWidth={1} />
        </div>

        {/* Optical AI Detection Bounding Box */}
        <div
          className="absolute border-2 border-saffron-600 rounded-[2px] shadow-sm pointer-events-none transition-all duration-300"
          style={{
            top: '32%',
            left: '30%',
            width: '42%',
            height: '48%',
          }}
        >
          {/* Anchored Detection HUD Chip */}
          <div className="absolute -top-7 left-0 bg-navy-950/90 text-white border border-saffron-600 px-2 py-0.5 rounded-[2px] font-mono text-[10px] tracking-wider whitespace-nowrap flex items-center gap-1.5 shadow-md">
            <span className="w-1.5 h-1.5 rounded-full bg-saffron-500 animate-pulse" />
            <span className="font-bold text-saffron-400">{plateText}</span>
            <span className="text-slate-400">|</span>
            <span>{confidence}% CONF</span>
            <span className="text-slate-400">|</span>
            <span className="text-amber-300 font-bold">{speed} KM/H</span>
          </div>

          {/* Plate reticle sub-box */}
          <div
            className="absolute border border-emerald-400 bg-emerald-500/10"
            style={{
              bottom: '12%',
              left: '35%',
              width: '30%',
              height: '14%',
            }}
          >
            <span className="absolute -bottom-4 left-0 text-[8px] font-mono text-emerald-400 font-bold tracking-tight">
              HSRP DETECTED
            </span>
          </div>
        </div>

        {/* Live Millisecond Watermark & Telemetry Footer */}
        <div className="absolute bottom-3 left-4 right-4 flex items-center justify-between text-[11px] font-mono text-white/90 pointer-events-none drop-shadow">
          <div className="bg-navy-950/80 px-2 py-0.5 rounded-[2px] border border-slate-700/60 flex items-center gap-2">
            <span className="text-emerald-400">GPS: 28.7845° N, 77.1352° E</span>
            <span className="text-slate-500">|</span>
            <span>ALT: 216m</span>
          </div>

          <div className="bg-navy-950/80 px-2 py-0.5 rounded-[2px] border border-slate-700/60 tabular-nums">
            {msTime}
          </div>
        </div>
      </div>
    </div>
  );
}
