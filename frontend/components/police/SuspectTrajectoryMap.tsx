'use client';

import React, { useEffect, useRef } from 'react';
import { useVehicleStore } from '@/stores/useVehicleStore';
import { MapPin, Navigation, Compass } from 'lucide-react';
import 'leaflet/dist/leaflet.css';

export function SuspectTrajectoryMap() {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<any>(null);
  const layersGroupRef = useRef<any>(null);

  const { history, selectedTrack, selectedObservation, selectObservation } =
    useVehicleStore();

  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    let isMounted = true;

    import('leaflet').then((L) => {
      if (!isMounted || !mapContainerRef.current) return;

      const map = L.map(mapContainerRef.current, {
        center: [28.76, 77.15],
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

  // Update Waypoints & Trajectory Line when history changes
  useEffect(() => {
    if (!mapInstanceRef.current || !layersGroupRef.current) return;

    import('leaflet').then((L) => {
      const map = mapInstanceRef.current;
      const group = layersGroupRef.current;
      group.clearLayers();

      const validSightings = history.filter(
        (h) => typeof h.latitude === 'number' && typeof h.longitude === 'number'
      );

      if (validSightings.length === 0) return;

      const latlngs: [number, number][] = validSightings.map((h) => [
        h.latitude!,
        h.longitude!,
      ]);

      // 1. Draw Saffron Animated Dashed Vector Trajectory
      const polyline = L.polyline(latlngs, {
        color: '#D97706',
        weight: 3.5,
        opacity: 0.9,
        dashArray: '8, 8',
      }).addTo(group);

      // 2. Sequential Waypoint Numbered Markers
      validSightings.forEach((obs, index) => {
        const isCurrent =
          selectedObservation?.id === obs.id ||
          (!selectedObservation && index === validSightings.length - 1);

        const speedColor =
          (obs.speed_kmh || 0) > 80
            ? '#B91C1C'
            : (obs.speed_kmh || 0) >= 50
            ? '#D97706'
            : '#047857';

        const customHtml = `
          <div style="
            position: relative;
            display: flex;
            align-items: center;
            justify-content: center;
            width: 32px;
            height: 32px;
            cursor: pointer;
          ">
            <div style="
              width: ${isCurrent ? '30px' : '24px'};
              height: ${isCurrent ? '30px' : '24px'};
              border-radius: 50%;
              background-color: ${isCurrent ? '#D97706' : '#0A192F'};
              color: white;
              display: flex;
              align-items: center;
              justify-content: center;
              font-family: 'JetBrains Mono', monospace;
              font-weight: 800;
              font-size: ${isCurrent ? '13px' : '11px'};
              border: 2px solid white;
              box-shadow: 0 2px 6px rgba(0,0,0,0.35);
              transition: all 0.2s ease;
            ">
              ${index + 1}
            </div>
            <div style="
              position: absolute;
              bottom: -4px;
              right: -4px;
              width: 10px;
              height: 10px;
              border-radius: 50%;
              background-color: ${speedColor};
              border: 1.5px solid white;
            "></div>
          </div>
        `;

        const icon = L.divIcon({
          html: customHtml,
          className: 'custom-trajectory-pin',
          iconSize: [32, 32],
          iconAnchor: [16, 16],
        });

        const marker = L.marker([obs.latitude!, obs.longitude!], { icon })
          .addTo(group)
          .on('click', () => {
            selectObservation(obs);
          });

        const popupContent = `
          <div style="font-family: 'Plus Jakarta Sans', sans-serif; min-width: 180px;">
            <div style="font-weight: 800; font-size: 11px; text-transform: uppercase; color: #0A192F; font-family: 'Rajdhani', sans-serif;">
              WAYPOINT ${index + 1} // ${obs.camera_id}
            </div>
            <div style="font-size: 11px; color: #475569; margin-top: 2px;">
              ${obs.camera_name || 'Highway Junction'}
            </div>
            <div style="margin-top: 6px; padding: 4px; background: #F4F4F0; border-radius: 3px; font-family: 'JetBrains Mono', monospace; font-size: 10px;">
              <div>SPEED: <b style="color: ${speedColor}">${obs.speed_kmh || 0} KM/H</b></div>
              <div>CONF: <b>${Math.round((obs.confidence || 0.95) * 100)}%</b></div>
            </div>
          </div>
        `;
        marker.bindPopup(popupContent);
      });

      // Fit bounds to trajectory
      if (latlngs.length > 0) {
        map.fitBounds(polyline.getBounds(), { padding: [40, 40] });
      }
    });
  }, [history, selectedObservation, selectObservation]);

  return (
    <div className="bg-surface border border-border-warm rounded-[4px] overflow-hidden shadow-gov-sm flex flex-col h-full">
      {/* Map Control Bar */}
      <div className="bg-tint border-b border-border-warm px-3.5 py-2 flex items-center justify-between text-xs">
        <div className="flex items-center gap-2">
          <Navigation className="w-3.5 h-3.5 text-saffron-600" />
          <span className="font-heading font-bold text-navy-950 uppercase tracking-wider">
            Sequential Journey Trajectory // NH-44 Corridor
          </span>
          <span className="font-mono text-[10px] text-slate-500">
            ({history.length} SIGHTINGS)
          </span>
        </div>

        <div className="flex items-center gap-2 text-[10px] font-mono">
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-emerald-600" /> &lt;50 km/h
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-saffron-600" /> 50-80
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-crimson-700" /> &gt;80
          </span>
        </div>
      </div>

      {/* Map Canvas */}
      <div className="relative flex-1 min-h-[300px] w-full">
        <div ref={mapContainerRef} className="absolute inset-0 z-0" />
      </div>
    </div>
  );
}
