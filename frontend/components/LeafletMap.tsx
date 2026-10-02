'use client';

import React, { useEffect, useRef } from 'react';
import { RoutePoint } from '@/types';

interface LeafletMapProps {
  route: RoutePoint[];
  selectedRouteIndex: number;
  onSelectRouteIndex: (idx: number) => void;
  selRoute: RoutePoint;
}

export default function LeafletMap({
  route,
  selectedRouteIndex,
  onSelectRouteIndex,
  selRoute,
}: LeafletMapProps) {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<any>(null);
  const routeLayerRef = useRef<any>(null);
  const markersRef = useRef<any[]>([]);
  const leafletLibRef = useRef<any>(null);

  // Initialize Map Engine ONCE on mount
  useEffect(() => {
    if (typeof window === 'undefined' || !mapContainerRef.current) return;

    let isMounted = true;

    import('leaflet').then((L) => {
      if (!isMounted || !mapContainerRef.current) return;
      leafletLibRef.current = L;

      // Clean up any stale container instance
      if (mapInstanceRef.current) {
        try {
          mapInstanceRef.current.stop();
          mapInstanceRef.current.off();
          mapInstanceRef.current.remove();
        } catch (e) {
          // ignore
        }
        mapInstanceRef.current = null;
      }

      // Default center: Chennai OMR Corridor coordinates
      const defaultCenter: [number, number] = [12.985, 80.240];

      // Initialize map with zoomAnimation disabled to eliminate _leaflet_pos crashes
      const map = L.map(mapContainerRef.current, {
        center: defaultCenter,
        zoom: 15,
        zoomControl: false,
        attributionControl: false,
        zoomAnimation: false,
        fadeAnimation: false,
      });
      mapInstanceRef.current = map;

      // Add Zoom Control to top-right
      L.control.zoom({ position: 'topright' }).addTo(map);

      // Tile layer: Check for CartoDB API Key or custom URL in env, fallback to official OpenStreetMap
      const cartoKey = process.env.NEXT_PUBLIC_CARTO_API_KEY;
      const customTileUrl = process.env.NEXT_PUBLIC_MAP_TILE_URL;

      let tileUrl = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png';
      let tileOptions: any = {
        maxZoom: 19,
        attribution: '&copy; OpenStreetMap contributors',
      };

      if (cartoKey) {
        tileUrl = `https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png?api_key=${cartoKey}`;
        tileOptions = { maxZoom: 19, subdomains: 'abcd' };
      } else if (customTileUrl) {
        tileUrl = customTileUrl;
      }

      L.tileLayer(tileUrl, tileOptions).addTo(map);

      // Create persistent LayerGroup for route elements
      const routeLayer = L.layerGroup().addTo(map);
      routeLayerRef.current = routeLayer;

      // Trigger initial render of route
      renderRoute(L, map, routeLayer, route, selectedRouteIndex);
    });

    return () => {
      isMounted = false;
      if (mapInstanceRef.current) {
        try {
          mapInstanceRef.current.stop();
          mapInstanceRef.current.off();
          mapInstanceRef.current.remove();
        } catch (e) {
          // safely ignored
        }
        mapInstanceRef.current = null;
      }
    };
  }, []);

  // Helper to re-render route markers and polylines on existing map
  const renderRoute = (
    L: any,
    map: any,
    layerGroup: any,
    pts: RoutePoint[],
    activeIdx: number
  ) => {
    if (!L || !map || !layerGroup) return;

    layerGroup.clearLayers();
    markersRef.current = [];

    // Parse coordinates
    const coordsWithPoints: { lat: number; lng: number; point: RoutePoint; index: number }[] = [];
    pts.forEach((p, idx) => {
      if (p.geo) {
        const parts = p.geo.split(',');
        if (parts.length === 2) {
          const lat = parseFloat(parts[0].trim());
          const lng = parseFloat(parts[1].trim());
          if (!isNaN(lat) && !isNaN(lng)) {
            coordsWithPoints.push({ lat, lng, point: p, index: idx });
          }
        }
      }
    });

    if (coordsWithPoints.length === 0) return;

    // Glowing + core trajectory polylines
    if (coordsWithPoints.length > 1) {
      const polylineCoords: [number, number][] = coordsWithPoints.map((c) => [c.lat, c.lng]);

      // Glow path
      L.polyline(polylineCoords, {
        color: '#0891B2',
        weight: 6,
        opacity: 0.25,
        lineCap: 'round',
        lineJoin: 'round',
      }).addTo(layerGroup);

      // Core sharp dashed path
      L.polyline(polylineCoords, {
        color: '#0891B2',
        weight: 3,
        opacity: 0.95,
        dashArray: '6, 8',
        lineCap: 'round',
        lineJoin: 'round',
      }).addTo(layerGroup);
    }

    // Pins
    const bounds = L.latLngBounds([]);
    coordsWithPoints.forEach(({ lat, lng, point, index }) => {
      const isSelected = activeIdx === index;

      const customIcon = L.divIcon({
        className: 'custom-map-pin' + (isSelected ? ' active' : ''),
        html: `<div style="width: 100%; height: 100%; display: flex; align-items: center; justify-content: center;">${point.n}</div>`,
        iconSize: [26, 26],
        iconAnchor: [13, 13],
      });

      const marker = L.marker([lat, lng], { icon: customIcon }).addTo(layerGroup);

      const popupContent = `
        <div style="padding: 10px 12px; font-family: 'Instrument Sans', sans-serif;">
          <div style="display: flex; justify-content: space-between; align-items: center; gap: 8px; margin-bottom: 4px;">
            <span style="font-family: 'JetBrains Mono', monospace; font-size: 11px; font-weight: 600; color: #0F172A;">${point.cam}</span>
            <span style="background: #0F172A; color: #FFFFFF; border-radius: 50%; width: 16px; height: 16px; display: flex; align-items: center; justify-content: center; font-size: 9px; font-family: 'JetBrains Mono', monospace;">${point.n}</span>
          </div>
          <div style="font-size: 11.5px; color: #334155; margin-bottom: 6px;">${point.street}</div>
          <div style="font-family: 'JetBrains Mono', monospace; font-size: 10px; color: #64748B; border-top: 1px solid #EEF1F4; padding-top: 5px; display: flex; justify-content: space-between; gap: 10px;">
            <span>TIME: ${point.time} IST</span>
            <span style="color: #0891B2; font-weight: 600;">${point.speed}</span>
          </div>
        </div>
      `;
      marker.bindPopup(popupContent);

      marker.on('click', () => {
        onSelectRouteIndex(index);
        marker.openPopup();
      });

      markersRef.current.push(marker);
      bounds.extend([lat, lng]);
    });

    // Fit view without animation transitions
    try {
      map.fitBounds(bounds, { padding: [50, 50], maxZoom: 16, animate: false });
    } catch (e) {
      // ignore
    }
  };

  // Update Route Layers when route prop changes
  useEffect(() => {
    if (!mapInstanceRef.current || !routeLayerRef.current || !leafletLibRef.current) return;
    renderRoute(
      leafletLibRef.current,
      mapInstanceRef.current,
      routeLayerRef.current,
      route,
      selectedRouteIndex
    );
  }, [route]);

  // Update Active Marker styling & pan when selectedRouteIndex changes
  useEffect(() => {
    if (!mapInstanceRef.current || markersRef.current.length === 0) return;

    markersRef.current.forEach((marker, idx) => {
      const isSelected = selectedRouteIndex === idx;
      const el = marker.getElement();
      if (el) {
        if (isSelected) {
          el.classList.add('active');
          try {
            marker.openPopup();
            mapInstanceRef.current.panTo(marker.getLatLng(), { animate: false });
          } catch (e) {
            // ignore
          }
        } else {
          el.classList.remove('active');
        }
      }
    });
  }, [selectedRouteIndex]);

  const isCartoKeySet = Boolean(process.env.NEXT_PUBLIC_CARTO_API_KEY);

  return (
    <div style={{ position: 'relative', border: '1px solid #E2E4E8', borderRadius: '5px', overflow: 'hidden', aspectRatio: '16/9', minHeight: '340px' }}>
      {/* Real Leaflet Map Canvas */}
      <div ref={mapContainerRef} style={{ position: 'absolute', inset: 0, width: '100%', height: '100%' }} />

      {/* Grid Legend Overlay (Top Left) */}
      <div style={{ position: 'absolute', left: '14px', top: '14px', zIndex: 500, display: 'flex', gap: '12px', fontFamily: "'JetBrains Mono', monospace", fontSize: '9.5px', color: '#64748B', background: 'rgba(255,255,255,.94)', border: '1px solid #E2E4E8', borderRadius: '4px', padding: '5px 9px', whiteSpace: 'nowrap', boxShadow: '0 2px 6px rgba(15,23,42,.06)' }}>
        <span>{isCartoKeySet ? 'CARTO POSITRON' : 'OPENSTREETMAP'} · TRAJECTORY RADAR</span>
        <span style={{ color: '#0891B2', fontWeight: 600 }}>LIVE TILE</span>
      </div>

      {/* Selected Node Card (Bottom Right) */}
      <div style={{ position: 'absolute', right: '14px', bottom: '14px', zIndex: 500, width: '232px', maxWidth: 'calc(100% - 28px)', background: '#FFFFFF', border: '1px solid #E2E4E8', borderRadius: '5px', boxShadow: '0 4px 14px rgba(15,23,42,.12)', overflow: 'hidden' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '10px', padding: '9px 11px', borderBottom: '1px solid #EEF1F4', background: '#FBFCFD' }}>
          <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '11px', color: '#0F172A', fontWeight: 600, letterSpacing: '.04em' }}>
            {selRoute.cam}
          </span>
          <span style={{ width: '18px', height: '18px', borderRadius: '50%', background: '#0F172A', color: '#FFFFFF', fontFamily: "'JetBrains Mono', monospace", fontSize: '9.5px', display: 'flex', alignItems: 'center', justifyContent: 'center', flex: 'none' }}>
            {selRoute.n}
          </span>
        </div>
        <div style={{ padding: '9px 11px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
          <div style={{ fontSize: '12px', color: '#334155', textWrap: 'pretty' }}>{selRoute.street}</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '5px', paddingTop: '7px', borderTop: '1px solid #EEF1F4', fontFamily: "'JetBrains Mono', monospace", fontSize: '10px', color: '#94A3B8' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', gap: '10px' }}>
              <span>SIGHTED</span>
              <span style={{ color: '#334155', whiteSpace: 'nowrap', flex: 'none' }}>{selRoute.time} IST</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', gap: '10px' }}>
              <span>SPEED</span>
              <span style={{ color: '#334155', whiteSpace: 'nowrap', flex: 'none' }}>{selRoute.speed}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', gap: '10px' }}>
              <span>OCR</span>
              <span style={{ color: '#334155', whiteSpace: 'nowrap', flex: 'none' }}>{selRoute.conf}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', gap: '10px' }}>
              <span>GEO</span>
              <span style={{ color: '#334155', whiteSpace: 'nowrap', flex: 'none' }}>{selRoute.geo}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
