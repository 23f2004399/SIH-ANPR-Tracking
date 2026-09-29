'use client';

import React, { useEffect, useRef } from 'react';
import { useTrafficStore } from '@/stores/useTrafficStore';
import { Layers, Activity } from 'lucide-react';
import 'leaflet/dist/leaflet.css';

export function CongestionMap() {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<any>(null);
  const layersGroupRef = useRef<any>(null);

  const { segments, selectedSegmentId, selectSegment } = useTrafficStore();

  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    let isMounted = true;

    import('leaflet').then((L) => {
      if (!isMounted || !mapContainerRef.current) return;

      const map = L.map(mapContainerRef.current, {
        center: [28.67, 77.21],
        zoom: 11,
        zoomControl: false,
      });

      L.control.zoom({ position: 'topright' }).addTo(map);

      // OpenStreetMap Tiles (Zero API Key Requirement)
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution:
          '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">OpenStreetMap</a> contributors',
        maxZoom: 19,
        className: 'osm-govtech-tiles',
      }).addTo(map);

      const layersGroup = L.layerGroup().addTo(map);
      layersGroupRef.current = layersGroup;
      mapInstanceRef.current = map;
    });

    return () => {
      isMounted = false;
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  // Draw Segment Polylines & Nodes
  useEffect(() => {
    if (!mapInstanceRef.current || !layersGroupRef.current) return;

    import('leaflet').then((L) => {
      const map = mapInstanceRef.current;
      const group = layersGroupRef.current;
      group.clearLayers();

      const statusColors = {
        fluid: '#047857',
        heavy: '#D97706',
        gridlock: '#B91C1C',
      };

      segments.forEach((seg) => {
        if (!seg.coordinates || seg.coordinates.length === 0) return;

        const isSelected = selectedSegmentId === seg.road_segment_id;
        const color = statusColors[seg.congestion_status];

        const line = L.polyline(seg.coordinates, {
          color,
          weight: isSelected ? 8 : 5,
          opacity: isSelected ? 1 : 0.8,
        }).addTo(group);

        line.on('click', () => {
          selectSegment(seg.road_segment_id);
        });

        // Add segment label popup
        line.bindPopup(`
          <div style="font-family: 'Plus Jakarta Sans', sans-serif;">
            <div style="font-weight: bold; font-size: 12px; color: #0A192F;">
              ${seg.segment_name}
            </div>
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 11px; margin-top: 4px;">
              AVG SPEED: <b>${seg.avg_speed_kmh} KM/H</b><br/>
              VOLUME: <b>${seg.total_vehicles.toLocaleString()}</b><br/>
              STATUS: <b style="color: ${color}; text-transform: uppercase;">${seg.congestion_status}</b>
            </div>
          </div>
        `);

        // Draw camera points along the segment
        seg.cameras.forEach((cam) => {
          const camMarker = L.circleMarker([cam.latitude, cam.longitude], {
            radius: 5,
            fillColor: '#0A192F',
            color: '#FFFFFF',
            weight: 2,
            fillOpacity: 1,
          }).addTo(group);

          camMarker.bindPopup(`
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 11px;">
              <b>${cam.id}</b> - ${cam.name}
            </div>
          `);
        });
      });
    });
  }, [segments, selectedSegmentId, selectSegment]);

  return (
    <div className="bg-surface border border-border-warm rounded-[4px] overflow-hidden shadow-gov-sm flex flex-col h-full">
      <div className="bg-tint border-b border-border-warm px-3.5 py-2 flex items-center justify-between text-xs">
        <div className="flex items-center gap-2">
          <Activity className="w-3.5 h-3.5 text-navy-900" />
          <span className="font-heading font-bold text-navy-950 uppercase tracking-wider">
            City-Wide Arterial Congestion & Velocity Heatmap
          </span>
        </div>

        <div className="flex items-center gap-3 text-[10px] font-mono">
          <span className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-700" /> Fluid (&gt;50 km/h)
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded-full bg-saffron-600" /> Congested (25–50)
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded-full bg-crimson-700" /> Gridlock (&lt;25)
          </span>
        </div>
      </div>

      <div className="relative flex-1 min-h-[360px] w-full">
        <div ref={mapContainerRef} className="absolute inset-0 z-0" />
      </div>
    </div>
  );
}
