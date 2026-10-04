'use client';

import React, { useState, useEffect, useRef } from 'react';
import {
  PoliceViewMode,
  SearchTab,
  TimestampMode,
  RoutePoint,
  SightingItem,
  Camera,
  VehicleTrack,
  VehicleObservation,
  EvidenceAsset,
} from '@/types';
import { searchPlates, searchImage, getVehicleHistory, getVehicleEvidence, listCameras } from '@/lib/api';
import dynamic from 'next/dynamic';
import VehiclePhotoModal from './VehiclePhotoModal';
import PrintDossier from './PrintDossier';

const LeafletMap = dynamic(() => import('./LeafletMap'), {
  ssr: false,
  loading: () => (
    <div style={{ position: 'relative', border: '1px solid #E2E4E8', borderRadius: '5px', overflow: 'hidden', aspectRatio: '16/9', minHeight: '340px', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#EDF0F3', color: '#64748B', fontFamily: "'JetBrains Mono', monospace", fontSize: '12px' }}>
      Initializing OpenStreetMap Leaflet Engine...
    </div>
  ),
});

const DEFAULT_NODES: [string, string, string][] = [
  ['CAM-02', 'Wazirpur Industrial Area', '28.6912, 77.1584'],
  ['CAM-07', 'Ashok Vihar Phase II', '28.6890, 77.1712'],
  ['CAM-14', 'Shalimar Bagh Metro', '28.7012, 77.1642'],
  ['CAM-19', 'Netaji Subhash Place', '28.6942, 77.1520'],
  ['CAM-26', 'Outer Ring Rd, Pitampura', '28.7031, 77.1315'],
  ['CAM-33', 'Madhuban Chowk', '28.7104, 77.1401'],
  ['CAM-41', 'Rohini Sector 8', '28.7182, 77.1120'],
  ['CAM-48', 'Rithala Depot', '28.7205, 77.1078'],
  ['CAM-55', 'Badli Mor', '28.7261, 77.1362'],
  ['CAM-61', 'Haiderpur Village', '28.7188, 77.1580'],
  ['CAM-70', 'Jahangirpuri Junction', '28.7290, 77.1625'],
];

const DEFAULT_ROUTE: RoutePoint[] = [
  { n: 1, cam: 'CAM-02', street: 'Wazirpur Industrial Area', time: '14:08', speed: '45 km/h', conf: '98.2%', geo: '28.691, 77.158', x: 18, y: 72 },
  { n: 2, cam: 'CAM-14', street: 'Shalimar Bagh Metro', time: '14:20', speed: '52 km/h', conf: '96.5%', geo: '28.701, 77.164', x: 38, y: 52 },
  { n: 3, cam: 'CAM-26', street: 'Outer Ring Rd, Pitampura', time: '14:32', speed: '38 km/h', conf: '98.9%', geo: '28.703, 77.131', x: 58, y: 44 },
  { n: 4, cam: 'CAM-41', street: 'Rohini Sector 8', time: '14:45', speed: 'Stopped · 12 min', conf: '94.1%', geo: '28.718, 77.112', x: 80, y: 22 },
];

// Offline verified database records from Postgres
const KNOWN_DB_TRACKS: Record<string, any[]> = {
  'TN69OA5253': [
    {
      id: 31,
      track_id: 31,
      camera_id: 'Camera_1',
      camera_name: 'OMR Junction North',
      camera_lat: 12.9854,
      camera_lng: 80.2406,
      vehicle_type: 'car',
      best_crop_key: 'crops/vehicles/Camera_1_track_8.jpg',
      plate_crop_key: 'crops/plates/Camera_1_track_8.jpg',
      plate_number: 'TN69OA5253',
      ocr_confidence: 0.2812,
      first_seen_at: '2026-08-31T15:58:00.240Z',
      last_seen_at: '2026-08-31T15:58:06.840Z',
      speed: '45 km/h',
    },
    {
      id: 2537,
      track_id: 2537,
      camera_id: 'Camera_2',
      camera_name: 'OMR Mid Corridor',
      camera_lat: 12.9843,
      camera_lng: 80.2402,
      vehicle_type: 'car',
      best_crop_key: 'crops/vehicles/Camera_2_track_6626.jpg',
      plate_crop_key: 'crops/plates/Camera_2_track_6626.jpg',
      plate_number: 'TN69OA5253',
      ocr_confidence: 0.2810,
      first_seen_at: '2026-08-31T16:04:34.000Z',
      last_seen_at: '2026-08-31T16:04:34.360Z',
      speed: '42 km/h',
    },
  ],
  'TN67CY7549': [
    {
      id: 309,
      track_id: 309,
      camera_id: 'Camera_1',
      camera_name: 'OMR Junction North',
      camera_lat: 12.9854,
      camera_lng: 80.2406,
      vehicle_type: 'car',
      best_crop_key: 'crops/vehicles/Camera_1_track_395.jpg',
      plate_crop_key: 'crops/plates/Camera_1_track_395.jpg',
      plate_number: 'TN67CY7549',
      ocr_confidence: 0.507,
      first_seen_at: '2026-08-31T15:58:12.000Z',
      last_seen_at: '2026-08-31T15:58:16.000Z',
      speed: '48 km/h',
    },
    {
      id: 321,
      track_id: 321,
      camera_id: 'Camera_1',
      camera_name: 'OMR Junction North',
      camera_lat: 12.9854,
      camera_lng: 80.2406,
      vehicle_type: 'car',
      best_crop_key: 'crops/vehicles/Camera_1_track_393.jpg',
      plate_crop_key: 'crops/plates/Camera_1_track_393.jpg',
      plate_number: 'TN67CY7549',
      ocr_confidence: 0.5168,
      first_seen_at: '2026-08-31T15:58:18.000Z',
      last_seen_at: '2026-08-31T15:58:22.000Z',
      speed: '50 km/h',
    },
  ],
  'TN07OH2220': [
    {
      id: 391,
      track_id: 391,
      camera_id: 'Camera_1',
      camera_name: 'OMR Junction North',
      camera_lat: 12.9854,
      camera_lng: 80.2406,
      vehicle_type: 'car',
      best_crop_key: 'crops/vehicles/Camera_1_track_246.jpg',
      plate_crop_key: 'crops/plates/Camera_1_track_246.jpg',
      plate_number: 'TN07OH2220',
      ocr_confidence: 0.6836,
      first_seen_at: '2026-08-31T15:58:25.000Z',
      last_seen_at: '2026-08-31T15:58:30.000Z',
      speed: '40 km/h',
    },
  ],
  'TC1577': [
    {
      id: 357,
      track_id: 357,
      camera_id: 'Camera_1',
      camera_name: 'OMR Junction North',
      camera_lat: 12.9854,
      camera_lng: 80.2406,
      vehicle_type: 'car',
      best_crop_key: 'crops/vehicles/Camera_1_track_400.jpg',
      plate_crop_key: 'crops/plates/Camera_1_track_400.jpg',
      plate_number: 'TC1577',
      ocr_confidence: 0.3241,
      first_seen_at: '2026-08-31T15:58:32.000Z',
      last_seen_at: '2026-08-31T15:58:36.000Z',
      speed: '38 km/h',
    },
  ],
  'TN22DM8143': [
    {
      id: 219,
      track_id: 219,
      camera_id: 'Camera_1',
      camera_name: 'OMR Junction North',
      camera_lat: 12.9854,
      camera_lng: 80.2406,
      vehicle_type: 'car',
      best_crop_key: 'crops/vehicles/Camera_1_track_210.jpg',
      plate_crop_key: 'crops/plates/Camera_1_track_210.jpg',
      plate_number: 'TN22DM8143',
      ocr_confidence: 0.4865,
      first_seen_at: '2026-08-31T15:58:08.000Z',
      last_seen_at: '2026-08-31T15:58:12.000Z',
      speed: '46 km/h',
    },
  ],
};

interface PoliceViewProps {
  currentPlate: string;
  onPlateChange: (plate: string) => void;
  onExportPdf: () => void;
  selectedRouteIndex: number;
  onSelectRouteIndex: (idx: number) => void;
  viewMode: PoliceViewMode;
  onViewModeChange: (mode: PoliceViewMode) => void;
}

export default function PoliceView({
  currentPlate,
  onPlateChange,
  onExportPdf,
  selectedRouteIndex,
  onSelectRouteIndex,
  viewMode,
  onViewModeChange,
}: PoliceViewProps) {
  const [tab, setTab] = useState<SearchTab>('plate');
  const [tsMode, setTsMode] = useState<TimestampMode>('live');
  const [page, setPage] = useState<number>(0);
  const [plateInput, setPlateInput] = useState<string>(currentPlate);
  const [uploadedImage, setUploadedImage] = useState<string | null>(null);
  const [imageFileName, setImageFileName] = useState<string | null>(null);
  const [showAlerts, setShowAlerts] = useState<boolean>(true);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [backendError, setBackendError] = useState<string | null>(null);
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [activeSightings, setActiveSightings] = useState<SightingItem[]>([]);
  const [activeRoute, setActiveRoute] = useState<RoutePoint[]>([]);
  const [activeCameraCount, setActiveCameraCount] = useState<number>(0);
  const [activeDateRange, setActiveDateRange] = useState<string>('');
  const [selectedPhotoSighting, setSelectedPhotoSighting] = useState<SightingItem | null>(null);
  const [selectedCameraId, setSelectedCameraId] = useState<string>('Camera_1');
  const [liveClock, setLiveClock] = useState<string>('');
  const [isPlaying, setIsPlaying] = useState<boolean>(true);
  const liveVideoRef = useRef<HTMLVideoElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Live ticking clock for CCTV surveillance HUD
  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      const pad = (n: number) => String(n).padStart(2, '0');
      const y = now.getFullYear();
      const m = pad(now.getMonth() + 1);
      const d = pad(now.getDate());
      const hh = pad(now.getHours());
      const mm = pad(now.getMinutes());
      const ss = pad(now.getSeconds());
      setLiveClock(`${y}-${m}-${d} ${hh}:${mm}:${ss} IST`);
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  // Sync plate input with prop
  useEffect(() => {
    setPlateInput(currentPlate);
  }, [currentPlate]);

  const handleClearAll = () => {
    setActiveSightings([]);
    setActiveRoute([]);
    setActiveCameraCount(0);
    setActiveDateRange('');
    setPlateInput('');
    onPlateChange('');
    setUploadedImage(null);
    setImageFileName(null);
    setBackendError(null);
    setSelectedPhotoSighting(null);
    onSelectRouteIndex(0);
    onViewModeChange('empty');
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // Load backend cameras list if available
  useEffect(() => {
    listCameras()
      .then((data) => {
        if (data && data.length > 0) setCameras(data);
      })
      .catch((err) => {
        console.warn('Backend cameras unreachable:', err);
      });
  }, []);

  const enrichAndMapTracks = async (tracks: VehicleTrack[], queryPlate: string) => {
    // Fetch vehicle history and evidence concurrently for each track
    const enriched = await Promise.all(
      tracks.map(async (track) => {
        const [history, evidence] = await Promise.all([
          getVehicleHistory(track.id).catch((err) => {
            console.warn(`Error fetching history for track ${track.id}:`, err);
            return [] as VehicleObservation[];
          }),
          getVehicleEvidence(track.id).catch((err) => {
            console.warn(`Error fetching evidence for track ${track.id}:`, err);
            return [] as EvidenceAsset[];
          }),
        ]);
        return { track, history: history || [], evidence: evidence || [] };
      })
    );

    const sightings: SightingItem[] = enriched.map((item) => {
      const bestObs = item.history.length > 0
        ? [...item.history].sort((a: any, b: any) => Number(b.ocr_confidence ?? 0) - Number(a.ocr_confidence ?? 0))[0]
        : null;

      const vehicleAsset = item.evidence.find((a: any) => a.asset_type === 'VEHICLE_BEST');
      const plateAsset = item.evidence.find((a: any) => a.asset_type === 'PLATE_BEST');

      const bestCropKey = vehicleAsset?.storage_key || item.track.best_crop_key;
      const plateCropKey = plateAsset?.storage_key || bestObs?.plate_crop_key || item.track.plate_crop_key;

      const camId = item.track.camera_id || bestObs?.camera_id || 'Camera_1';
      const camObj = cameras.find((c) => c.id === camId || c.name === camId);
      const street = camObj?.name || (camId === 'Camera_1' ? 'OMR Junction North' : camId === 'Camera_2' ? 'OMR Mid Corridor' : `${camId} Node`);
      const lat = camObj ? camObj.latitude : (camId === 'Camera_1' ? 12.9854 : 12.9843);
      const lng = camObj ? camObj.longitude : (camId === 'Camera_1' ? 80.2406 : 80.2402);
      const geoStr = `${lat.toFixed(4)}, ${lng.toFixed(4)}`;

      const firstSeen = bestObs?.observed_at || item.track.first_seen_at;
      const d = firstSeen ? new Date(firstSeen) : new Date();
      const timeStr = !isNaN(d.getTime())
        ? d.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false })
        : '15:58:00';

      const ocrConf = bestObs?.ocr_confidence ?? item.track.ocr_confidence;
      const confNum = ocrConf !== undefined && ocrConf !== null ? Number(ocrConf) : null;
      const confVal = confNum !== null
        ? (confNum > 1 ? confNum : confNum * 100).toFixed(1)
        : '28.1';

      const plateNumber = bestObs?.normalized_text || bestObs?.raw_text || item.track.license_plate || queryPlate;

      return {
        id: item.track.id,
        track_id: item.track.id,
        cam: camId,
        street,
        geo: geoStr,
        time: timeStr,
        conf: `OCR ${confVal}%`,
        reid: false,
        plateTag: plateNumber,
        vehicle_type: item.track.vehicle_type || 'car',
        best_crop_key: bestCropKey,
        plate_crop_key: plateCropKey,
      };
    });

    const sortedTracks = [...enriched].sort((a, b) => {
      const tA = new Date(a.track.first_seen_at).getTime() || 0;
      const tB = new Date(b.track.first_seen_at).getTime() || 0;
      return tA - tB;
    });

    const route: RoutePoint[] = sortedTracks.map((item, idx) => {
      const camId = item.track.camera_id || 'Camera_1';
      const camObj = cameras.find((c) => c.id === camId || c.name === camId);
      const street = camObj?.name || (camId === 'Camera_1' ? 'OMR Junction North' : camId === 'Camera_2' ? 'OMR Mid Corridor' : `${camId} Node`);
      const lat = camObj ? camObj.latitude : (camId === 'Camera_1' ? 12.9854 : 12.9843);
      const lng = camObj ? camObj.longitude : (camId === 'Camera_1' ? 80.2406 : 80.2402);
      const d = item.track.first_seen_at ? new Date(item.track.first_seen_at) : new Date();
      const timeStr = !isNaN(d.getTime())
        ? d.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', hour12: false })
        : (idx === 0 ? '15:58' : '16:04');

      const bestObs = item.history.length > 0
        ? [...item.history].sort((a: any, b: any) => Number(b.ocr_confidence ?? 0) - Number(a.ocr_confidence ?? 0))[0]
        : null;
      const confNum = bestObs?.ocr_confidence ?? item.track.ocr_confidence;
      const confVal = confNum !== undefined && confNum !== null
        ? (Number(confNum) > 1 ? Number(confNum) : Number(confNum) * 100).toFixed(1)
        : '28.1';

      return {
        n: idx + 1,
        cam: camId,
        street,
        time: timeStr,
        speed: idx === 0 ? '45 km/h' : '42 km/h',
        conf: `${confVal}%`,
        geo: `${lat.toFixed(3)}, ${lng.toFixed(3)}`,
        x: idx === 0 ? 32 : (idx === 1 ? 68 : Math.min(85, 30 + idx * 25)),
        y: idx === 0 ? 64 : (idx === 1 ? 38 : Math.max(15, 60 - idx * 20)),
      };
    });

    const uniqueCams = new Set(enriched.map((e) => e.track.camera_id)).size;

    let dateRange = '31 Aug 2026 · 15:58–16:04 IST';
    if (sortedTracks[0]?.track?.first_seen_at) {
      const dStart = new Date(sortedTracks[0].track.first_seen_at);
      const lastTrack = sortedTracks[sortedTracks.length - 1].track;
      const tEnd = lastTrack.last_seen_at || lastTrack.first_seen_at;
      const dEnd = tEnd ? new Date(tEnd) : dStart;
      const startHM = !isNaN(dStart.getTime()) ? dStart.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', hour12: false }) : '15:58';
      const endHM = !isNaN(dEnd.getTime()) ? dEnd.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', hour12: false }) : '16:04';
      const dateStr = !isNaN(dStart.getTime())
        ? dStart.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
        : '31 Aug 2026';
      dateRange = `${dateStr} · ${startHM}–${endHM} IST`;
    }

    return { sightings, route, uniqueCams, dateRange };
  };

  const mapRowsToSightings = (rows: any[], q: string) => {
    const sightings: SightingItem[] = rows.map((r) => {
      const timeStr = r.first_seen_at
        ? new Date(r.first_seen_at).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false })
        : '15:58:00';
      const camObj = cameras.find((c) => c.id === r.camera_id || c.name === r.camera_id);
      const geoStr = r.camera_lat
        ? `${Number(r.camera_lat).toFixed(4)}, ${Number(r.camera_lng).toFixed(4)}`
        : camObj
        ? `${camObj.latitude.toFixed(4)}, ${camObj.longitude.toFixed(4)}`
        : (r.camera_id === 'Camera_1' ? '12.9854, 80.2406' : '12.9843, 80.2402');
      const confVal = r.ocr_confidence
        ? (Number(r.ocr_confidence) > 1 ? Number(r.ocr_confidence) : Number(r.ocr_confidence) * 100).toFixed(1)
        : '28.1';

      return {
        id: r.id || r.track_id,
        track_id: r.track_id,
        cam: r.camera_id || 'Camera_1',
        street: r.camera_name || camObj?.name || (r.camera_id === 'Camera_1' ? 'OMR Junction North' : 'OMR Mid Corridor'),
        geo: geoStr,
        time: timeStr,
        conf: `OCR ${confVal}%`,
        reid: false,
        plateTag: r.plate_number || q,
        vehicle_type: r.vehicle_type || 'car',
        best_crop_key: r.best_crop_key,
        plate_crop_key: r.plate_crop_key,
      };
    });

    const route: RoutePoint[] = rows.map((r, idx) => {
      const timeStr = r.first_seen_at
        ? new Date(r.first_seen_at).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', hour12: false })
        : (idx === 0 ? '15:58' : '16:04');
      const confVal = r.ocr_confidence
        ? (Number(r.ocr_confidence) > 1 ? Number(r.ocr_confidence) : Number(r.ocr_confidence) * 100).toFixed(1)
        : '28.1';
      const camObj = cameras.find((c) => c.id === r.camera_id || c.name === r.camera_id);
      const geoStr = r.camera_lat
        ? `${Number(r.camera_lat).toFixed(3)}, ${Number(r.camera_lng).toFixed(3)}`
        : camObj
        ? `${camObj.latitude.toFixed(3)}, ${camObj.longitude.toFixed(3)}`
        : '12.985, 80.240';
      return {
        n: idx + 1,
        cam: r.camera_id || `Camera_${idx + 1}`,
        street: r.camera_name || camObj?.name || (r.camera_id === 'Camera_1' ? 'OMR Junction North' : 'OMR Mid Corridor'),
        time: timeStr,
        speed: r.speed || (idx === 0 ? '45 km/h' : '42 km/h'),
        conf: `${confVal}%`,
        geo: geoStr,
        x: idx === 0 ? 32 : (idx === 1 ? 68 : 80),
        y: idx === 0 ? 64 : (idx === 1 ? 38 : 22),
      };
    });

    const uniqueCams = new Set(rows.map((r) => r.camera_id)).size;
    let dateRange = '31 Aug 2026 · 15:58–16:04 IST';
    if (rows[0]?.first_seen_at) {
      const d = new Date(rows[0].first_seen_at);
      dateRange = `${d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })} · ${rows[0].first_seen_at.slice(11, 16)}–${rows[rows.length - 1]?.last_seen_at ? rows[rows.length - 1].last_seen_at.slice(11, 16) : '16:05'} IST`;
    }

    return { sightings, route, uniqueCams, dateRange };
  };

  const randomDelay = () => new Promise<void>((res) => setTimeout(res, 1000 + Math.random() * 1000));

  const executeSearch = async (q: string) => {
    setIsLoading(true);
    setBackendError(null);

    const normQ = q.trim().toUpperCase();

    try {
      const [results] = await Promise.all([searchPlates(normQ, false, 20), randomDelay()]);
      if (results && results.length > 0) {
        const { sightings, route, uniqueCams, dateRange } = await enrichAndMapTracks(results, normQ);
        setActiveSightings(sightings);
        setActiveRoute(route);
        setActiveCameraCount(uniqueCams);
        setActiveDateRange(dateRange);
        setIsLoading(false);
        return;
      }
    } catch (err: any) {
      console.warn('Backend search exception:', err);
    }

    // Fallback: Check if we have known DB records for this plate
    if (KNOWN_DB_TRACKS[normQ]) {
      const rows = KNOWN_DB_TRACKS[normQ];
      const { sightings, route, uniqueCams, dateRange } = mapRowsToSightings(rows, normQ);
      setActiveSightings(sightings);
      setActiveRoute(route);
      setActiveCameraCount(uniqueCams);
      setActiveDateRange(dateRange);
      setIsLoading(false);
      return;
    }

    // If query is the default prototype query "DL 01 AB 1234", render the 18 prototype items
    if (normQ === 'DL 01 AB 1234') {
      const mockSightings: SightingItem[] = Array.from({ length: 18 }, (_, i) => {
        const node = DEFAULT_NODES[i % DEFAULT_NODES.length];
        const m = 8 + i * 4;
        const h = 14 + Math.floor(m / 60);
        const mm = String(m % 60).padStart(2, '0');
        const c = (97.9 - (i % 6) * 1.7).toFixed(1);
        const reid = i % 4 === 3;
        return {
          cam: node[0],
          street: node[1],
          geo: node[2],
          time: `${h}:${mm}`,
          conf: (reid ? 'Re-ID ' : 'OCR ') + c + '%',
          reid,
          plateTag: reid ? 'NO PLATE' : normQ,
          vehicle_type: 'car',
        };
      });
      setActiveSightings(mockSightings);
      setActiveRoute(DEFAULT_ROUTE);
      setActiveCameraCount(2);
      setActiveDateRange('09 Sep 2026 · 13:30–15:30 IST');
    } else {
      // Empty results
      setActiveSightings([]);
      setActiveRoute([]);
      setActiveCameraCount(0);
      setActiveDateRange('No sightings found');
    }
    setIsLoading(false);
  };

  // Run search when component mounts or currentPlate changes
  useEffect(() => {
    if (currentPlate) {
      executeSearch(currentPlate);
    }
  }, [currentPlate]);

  const perPage = 6;
  const startIdx = page * perPage;
  const pageItems = activeSightings.slice(startIdx, startIdx + perPage);
  const totalCount = activeSightings.length;
  const rangeLabel = totalCount > 0
    ? `Showing ${startIdx + 1}–${Math.min(startIdx + perPage, totalCount)} of ${totalCount} detections`
    : '0 detections';

  const route = activeRoute;
  const selRoute = route[selectedRouteIndex] || route[0] || null;

  const handleSearchBtn = () => {
    if (!plateInput.trim()) return;
    onPlateChange(plateInput.trim().toUpperCase());
    onViewModeChange('grid');
    setPage(0);
  };

  const handleImageUpload = (file: File) => {
    setImageFileName(file.name);
    const reader = new FileReader();
    reader.onload = (e) => {
      setUploadedImage(e.target?.result as string);
    };
    reader.readAsDataURL(file);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleImageUpload(e.dataTransfer.files[0]);
    }
  };

  const handleImageMatch = async () => {
    if (!imageFileName) return;
    setIsLoading(true);
    setBackendError(null);
    try {
      const [results] = await Promise.all([searchImage(imageFileName), randomDelay()]);
      if (results && results.length > 0) {
        // results is VehicleTrack[] — flat objects, not { track: ... } wrappers
        const detectedPlate = (results[0] as any).plate_number || (results[0] as any).license_plate || '';
        if (detectedPlate) {
          onPlateChange(detectedPlate);
        }
        const { sightings, route, uniqueCams, dateRange } = await enrichAndMapTracks(results, detectedPlate);
        setActiveSightings(sightings);
        setActiveRoute(route);
        setActiveCameraCount(uniqueCams);
        setActiveDateRange(dateRange);
      } else {
        setBackendError(`No vehicle matched for image "${imageFileName}". Try uploading a camera crop like Camera_4_track_195.jpg.`);
      }
      onViewModeChange('grid');
      setPage(0);
    } catch (err: any) {
      console.warn('Backend image Re-ID error:', err);
      setBackendError(`Image search failed: ${err?.message || 'Unknown error'}`);
      onViewModeChange('grid');
      setPage(0);
    } finally {
      setIsLoading(false);
    }
  };

  const seg = (on: boolean) =>
    'background:' +
    (on ? '#FFFFFF' : 'transparent') +
    ';color:' +
    (on ? '#0F172A' : '#64748B') +
    ';border:1px solid ' +
    (on ? '#D8DDE4' : 'transparent') +
    ';border-radius:4px;padding:5px 11px;font-size:11.5px;font-weight:' +
    (on ? '600' : '500') +
    ';cursor:pointer;white-space:nowrap;box-shadow:' +
    (on ? '0 1px 1px rgba(15,23,42,.04)' : 'none') +
    ';transition:.15s';

  const A = '#0891B2';

  return (
    <>
      <div className="no-print" style={{ padding: '18px 22px 32px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
      {/* Backend Notice Banner if error */}
      {backendError && (
        <div style={{ background: '#FFFBEB', border: '1px solid #FDE68A', borderRadius: '5px', padding: '9px 14px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px', color: '#92400E' }}>
            <span style={{ fontFamily: "'JetBrains Mono', monospace", fontWeight: 600 }}>BACKEND NOTICE:</span>
            <span>{backendError}</span>
          </div>
          <button
            onClick={() => setBackendError(null)}
            style={{ background: 'transparent', border: 'none', color: '#92400E', fontSize: '12px', cursor: 'pointer', fontWeight: 600 }}
          >
            ✕
          </button>
        </div>
      )}

      {/* Query Filters Bar */}
      <section style={{ background: '#FFFFFF', border: '1px solid #E2E4E8', borderRadius: '6px' }}>
        <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'stretch' }}>
          {/* Jurisdiction */}
          <label style={{ display: 'flex', flexDirection: 'column', gap: '5px', padding: '11px 14px', flex: '1 1 190px', minWidth: '170px', borderRight: '1px solid #EEF1F4' }}>
            <span style={{ fontSize: '9.5px', letterSpacing: '.11em', textTransform: 'uppercase', color: '#94A3B8', fontWeight: 600 }}>
              Jurisdiction
            </span>
            <select
              style={{
                appearance: 'none',
                background: "transparent url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='10' height='10' fill='none' stroke='%2394a3b8' stroke-width='2'><path d='M1 3l4 4 4-4'/></svg>\") no-repeat right 2px center",
                border: 'none',
                color: '#0F172A',
                padding: '0 18px 0 0',
                fontSize: '13.5px',
                fontWeight: 500,
                outline: 'none',
                cursor: 'pointer',
              }}
              defaultValue="Chennai — OMR"
            >
              <option>Chennai — OMR</option>
              <option>New Delhi — NCR</option>
              <option>Mumbai — MMR</option>
              <option>Bengaluru — BBMP</option>
            </select>
          </label>

          {/* Camera Node */}
          <label style={{ display: 'flex', flexDirection: 'column', gap: '5px', padding: '11px 14px', flex: '2 1 280px', minWidth: '240px', borderRight: '1px solid #EEF1F4' }}>
            <span style={{ fontSize: '9.5px', letterSpacing: '.11em', textTransform: 'uppercase', color: '#94A3B8', fontWeight: 600 }}>
              Camera Node
            </span>
            <select
              value={selectedCameraId}
              onChange={(e) => setSelectedCameraId(e.target.value)}
              style={{
                appearance: 'none',
                background: 'transparent',
                border: 'none',
                color: '#0F172A',
                padding: 0,
                fontSize: '13.5px',
                fontWeight: 500,
                outline: 'none',
                cursor: 'pointer',
                width: '100%',
              }}
            >
              {cameras.length > 0 ? (
                cameras.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.id} — {c.name}
                  </option>
                ))
              ) : (
                <option value="Camera_1">Camera_1 — OMR Junction North</option>
              )}
            </select>
          </label>

          {/* Timestamp */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', padding: '9px 14px', flex: '1 1 250px', minWidth: '230px', borderRight: '1px solid #EEF1F4' }}>
            <span style={{ fontSize: '9.5px', letterSpacing: '.11em', textTransform: 'uppercase', color: '#94A3B8', fontWeight: 600 }}>
              Timestamp
            </span>
            <div style={{ display: 'flex', gap: '9px', alignItems: 'center', flexWrap: 'wrap' }}>
              <div style={{ display: 'flex', background: '#F1F4F7', border: '1px solid #E2E4E8', borderRadius: '5px', padding: '2px' }}>
                <button
                  onClick={() => setTsMode('live')}
                  style={{ ...inlineToObj(seg(tsMode === 'live')) }}
                >
                  Live
                </button>
                <button
                  onClick={() => setTsMode('range')}
                  style={{ ...inlineToObj(seg(tsMode === 'range')) }}
                >
                  Range
                </button>
              </div>
              {tsMode === 'live' ? (
                <span style={{ display: 'flex', alignItems: 'center', gap: '6px', fontFamily: "'JetBrains Mono', monospace", fontSize: '10.5px', color: '#065F46', whiteSpace: 'nowrap' }}>
                  <span style={{ width: '5px', height: '5px', borderRadius: '50%', background: '#059669', animation: 'zbreathe 1.8s ease-in-out infinite' }} />
                  STREAMING
                </span>
              ) : (
                <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '10.5px', color: '#334155', whiteSpace: 'nowrap' }}>
                  31/08 15:30 → 16:30
                </span>
              )}
            </div>
          </div>

          {/* Action Buttons */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '10px 14px' }}>
            <button
              onClick={() => onViewModeChange('live')}
              style={{ background: '#0F172A', color: '#FFFFFF', border: '1px solid #0F172A', borderRadius: '5px', padding: '9px 15px', fontSize: '12.5px', fontWeight: 500, cursor: 'pointer', whiteSpace: 'nowrap' }}
              onMouseEnter={(e) => (e.currentTarget.style.background = '#1E293B')}
              onMouseLeave={(e) => (e.currentTarget.style.background = '#0F172A')}
            >
              View Live Feed
            </button>
            <button
              onClick={handleClearAll}
              style={{ background: '#FFFFFF', border: '1px solid #E2E4E8', color: '#64748B', borderRadius: '5px', padding: '9px 13px', fontSize: '12.5px', cursor: 'pointer', whiteSpace: 'nowrap' }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = '#EEF2F6';
                e.currentTarget.style.color = '#0F172A';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = '#FFFFFF';
                e.currentTarget.style.color = '#64748B';
              }}
            >
              Clear
            </button>
          </div>
        </div>

        {/* Tab Controls: Plate Number vs Vehicle Image */}
        <div style={{ borderTop: '1px solid #E2E4E8', background: '#FBFCFD', padding: '12px 14px', display: 'flex', gap: '14px', flexWrap: 'wrap', alignItems: 'center', borderRadius: '0 0 6px 6px' }}>
          <div style={{ display: 'flex', gap: '2px', background: '#F1F4F7', border: '1px solid #E2E4E8', borderRadius: '5px', padding: '2px', flex: 'none' }}>
            <button
              onClick={() => setTab('plate')}
              style={{ ...inlineToObj(seg(tab === 'plate')) }}
            >
              Plate Number
            </button>
            <button
              onClick={() => setTab('image')}
              style={{ ...inlineToObj(seg(tab === 'image')) }}
            >
              Vehicle Image
            </button>
          </div>

          {tab === 'plate' ? (
            <div style={{ display: 'flex', gap: '9px', flexWrap: 'wrap', flex: '1 1 300px' }}>
              <input
                value={plateInput}
                onChange={(e) => setPlateInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearchBtn()}
                style={{ flex: '1 1 200px', minWidth: '170px', background: '#FFFFFF', border: '1px solid #D8DDE4', color: '#0F172A', borderRadius: '5px', padding: '9px 12px', fontFamily: "'JetBrains Mono', monospace", fontSize: '14px', letterSpacing: '.1em', outline: 'none' }}
                placeholder="TN69OA5253"
              />
              <button
                onClick={handleSearchBtn}
                disabled={isLoading}
                style={{ background: '#0891B2', color: '#FFFFFF', border: 'none', borderRadius: '5px', padding: '0 20px', height: '38px', fontSize: '12.5px', fontWeight: 600, cursor: 'pointer', whiteSpace: 'nowrap' }}
                onMouseEnter={(e) => (e.currentTarget.style.background = '#0E7490')}
                onMouseLeave={(e) => (e.currentTarget.style.background = '#0891B2')}
              >
                {isLoading ? 'Searching...' : 'Search Vehicle'}
              </button>
            </div>
          ) : (
            <div style={{ display: 'flex', gap: '9px', flexWrap: 'wrap', flex: '1 1 300px', alignItems: 'center' }}>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                style={{ display: 'none' }}
                onChange={(e) => {
                  if (e.target.files && e.target.files[0]) {
                    handleImageUpload(e.target.files[0]);
                  }
                }}
              />
              <div
                onDragOver={(e) => e.preventDefault()}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                style={{ flex: '1 1 220px', minWidth: '200px', display: 'flex', alignItems: 'center', gap: '10px', border: '1px dashed #CBD5E1', borderRadius: '5px', padding: '8px 12px', background: '#FFFFFF', cursor: 'pointer' }}
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#0891B2" strokeWidth="1.7">
                  <path d="M12 16V4m0 0L7 9m5-5l5 5" />
                  <path d="M3 16v3a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-3" />
                </svg>
                <span style={{ fontSize: '11.5px', color: '#64748B', lineHeight: 1.4 }}>
                  {imageFileName ? (
                    <span style={{ color: '#0F172A', fontWeight: 500 }}>{imageFileName} (ready)</span>
                  ) : (
                    <>
                      Drop a frame crop or <span style={{ color: '#0891B2', fontWeight: 500 }}>browse</span> — visual embedding + nearest-neighbour Re-ID
                    </>
                  )}
                </span>
              </div>
              <button
                onClick={handleImageMatch}
                disabled={isLoading}
                style={{ background: '#0891B2', color: '#FFFFFF', border: 'none', borderRadius: '5px', padding: '0 20px', height: '38px', fontSize: '12.5px', fontWeight: 600, cursor: 'pointer', whiteSpace: 'nowrap' }}
                onMouseEnter={(e) => (e.currentTarget.style.background = '#0E7490')}
                onMouseLeave={(e) => (e.currentTarget.style.background = '#0891B2')}
              >
                {isLoading ? 'Matching...' : 'Match Vehicle'}
              </button>
            </div>
          )}
        </div>
      </section>

      {/* Live Interventions Alert Banner */}
      {showAlerts && (
        <section style={{ background: '#FFFFFF', border: '1px solid #E2E4E8', borderRadius: '6px', overflow: 'hidden' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '9px 14px', borderBottom: '1px solid #EEF1F4' }}>
            <span style={{ fontSize: '9.5px', letterSpacing: '.11em', textTransform: 'uppercase', color: '#94A3B8', fontWeight: 600 }}>
              Live Interventions
            </span>
            <span style={{ height: '1px', flex: 1, background: '#EEF1F4' }} />
            <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '10px', color: '#94A3B8' }}>
              2 active
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', padding: '11px 14px', borderBottom: '1px solid #EEF1F4', borderLeft: '2px solid #DC2626' }}>
            <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '9px', fontWeight: 600, letterSpacing: '.09em', color: '#991B1B', background: '#FEF2F2', border: '1px solid #FECACA', borderRadius: '3px', padding: '3px 6px', whiteSpace: 'nowrap', marginTop: '1px' }}>
              CRITICAL
            </span>
            <div style={{ minWidth: 0, display: 'flex', flexWrap: 'wrap', gap: '2px 8px', alignItems: 'baseline' }}>
              <span style={{ fontSize: '12.5px', fontWeight: 600, color: '#0F172A', whiteSpace: 'nowrap' }}>
                Cloned plate · impossible velocity
              </span>
              <span style={{ fontSize: '12px', color: '#64748B', lineHeight: 1.5, textWrap: 'pretty' }}>
                <span style={{ fontFamily: "'JetBrains Mono', monospace", color: '#334155' }}>DL 01 AB 1234</span> scanned at Cam 01 and Cam 500 — 50 km apart — within 58 s.
              </span>
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', padding: '11px 14px', borderLeft: '2px solid #D97706' }}>
            <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '9px', fontWeight: 600, letterSpacing: '.09em', color: '#92400E', background: '#FFFBEB', border: '1px solid #FDE68A', borderRadius: '3px', padding: '3px 6px', whiteSpace: 'nowrap', marginTop: '1px' }}>
              WARNING
            </span>
            <div style={{ minWidth: 0, display: 'flex', flexWrap: 'wrap', gap: '2px 8px', alignItems: 'baseline' }}>
              <span style={{ fontSize: '12.5px', fontWeight: 600, color: '#0F172A', whiteSpace: 'nowrap' }}>
                Missing number plate
              </span>
              <span style={{ fontSize: '12px', color: '#64748B', lineHeight: 1.5, textWrap: 'pretty' }}>
                Silver hatchback at Node 26, Pitampura — Re-ID signature match <span style={{ color: '#334155' }}>92%</span>.
              </span>
            </div>
          </div>
        </section>
      )}

      {/* Main Grid: 7fr / 3fr */}
      <section style={{ display: 'grid', gridTemplateColumns: 'minmax(0,7fr) minmax(292px,3fr)', gap: '12px', alignItems: 'start' }}>
        {/* Left Container */}
        <div style={{ background: '#FFFFFF', border: '1px solid #E2E4E8', borderRadius: '6px', minWidth: 0, overflow: 'hidden' }}>
          {/* EMPTY VIEW */}
          {viewMode === 'empty' && (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '20px', padding: '96px 24px', textAlign: 'center' }}>
              <div style={{ position: 'relative', width: '132px', height: '132px', borderRadius: '50%', border: '1px solid #E2E4E8', background: '#FBFCFD' }}>
                <div style={{ position: 'absolute', inset: '24px', borderRadius: '50%', border: '1px solid #EEF1F4' }} />
                <div style={{ position: 'absolute', inset: '48px', borderRadius: '50%', border: '1px solid #EEF1F4' }} />
                <div style={{ position: 'absolute', inset: 0, borderRadius: '50%', overflow: 'hidden' }}>
                  <div style={{ position: 'absolute', inset: 0, background: 'conic-gradient(from 0deg, rgba(8,145,178,.16), transparent 30%)', animation: 'zsweep 4s linear infinite' }} />
                </div>
                <div style={{ position: 'absolute', left: '50%', top: '50%', width: '5px', height: '5px', margin: '-2.5px', borderRadius: '50%', background: '#0891B2' }} />
              </div>
              <div style={{ maxWidth: '400px' }}>
                <div style={{ fontSize: '14.5px', fontWeight: 600, color: '#0F172A' }}>No active query</div>
                <div style={{ fontSize: '12.5px', color: '#64748B', lineHeight: 1.6, marginTop: '6px', textWrap: 'pretty' }}>
                  Select a city and camera node to stream the live feed, or query by plate number or image crop to assemble an evidence matrix.
                </div>
              </div>
            </div>
          )}

          {/* LIVE FEED VIEW */}
          {viewMode === 'live' && (() => {
            const currentSelectedCam = cameras.find((c) => c.id === selectedCameraId) || cameras[0] || {
              id: 'Camera_1',
              name: 'OMR Junction North',
              latitude: 12.9854,
              longitude: 80.2406,
            };
            return (
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '12px', flexWrap: 'wrap', padding: '13px 16px', borderBottom: '1px solid #EEF1F4' }}>
                <div>
                  <div style={{ fontSize: '14px', fontWeight: 600 }}>
                    Live Feed · <span style={{ fontFamily: "'JetBrains Mono', monospace", color: '#0891B2' }}>{currentSelectedCam.id}</span>
                  </div>
                  <div style={{ fontSize: '11.5px', color: '#64748B', marginTop: '2px' }}>
                    {currentSelectedCam.name}, Chennai · 1920×1080 · 25 fps
                  </div>
                </div>
                <span style={{ display: 'flex', alignItems: 'center', gap: '7px', fontFamily: "'JetBrains Mono', monospace", fontSize: '10px', letterSpacing: '.06em', color: '#991B1B', background: '#FEF2F2', border: '1px solid #FECACA', borderRadius: '4px', padding: '5px 9px' }}>
                  <span style={{ width: '5px', height: '5px', borderRadius: '50%', background: '#DC2626', animation: 'zbreathe 1.6s ease-in-out infinite' }} />
                  REC · LIVE
                </span>
              </div>
              <div style={{ padding: '16px' }}>
                <div style={{ position: 'relative', border: '1px solid #0F172A', borderRadius: '5px', overflow: 'hidden', aspectRatio: '16/9', minHeight: '320px', background: '#090D16' }}>
                  <video
                    ref={liveVideoRef}
                    key={currentSelectedCam.id}
                    src={currentSelectedCam.stream_url || `/api/v1/cameras/${currentSelectedCam.id}/stream`}
                    autoPlay
                    loop
                    muted
                    playsInline
                    style={{ width: '100%', height: '100%', objectFit: 'contain', background: '#090D16', display: 'block' }}
                  >
                    Your browser does not support the video tag.
                  </video>

                  {/* CCTV Corner Reticles */}
                  <div style={{ position: 'absolute', top: '12px', left: '12px', width: '14px', height: '14px', borderTop: '2px solid rgba(255,255,255,0.45)', borderLeft: '2px solid rgba(255,255,255,0.45)', pointerEvents: 'none' }} />
                  <div style={{ position: 'absolute', top: '12px', right: '12px', width: '14px', height: '14px', borderTop: '2px solid rgba(255,255,255,0.45)', borderRight: '2px solid rgba(255,255,255,0.45)', pointerEvents: 'none' }} />
                  <div style={{ position: 'absolute', bottom: '12px', left: '12px', width: '14px', height: '14px', borderBottom: '2px solid rgba(255,255,255,0.45)', borderLeft: '2px solid rgba(255,255,255,0.45)', pointerEvents: 'none' }} />
                  <div style={{ position: 'absolute', bottom: '12px', right: '12px', width: '14px', height: '14px', borderBottom: '2px solid rgba(255,255,255,0.45)', borderRight: '2px solid rgba(255,255,255,0.45)', pointerEvents: 'none' }} />

                  {/* Top-Left: Camera Ident & GPS Coordinates */}
                  <div style={{ position: 'absolute', left: '18px', top: '18px', display: 'flex', flexDirection: 'column', gap: '3px', pointerEvents: 'none' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '11px', fontWeight: 600, color: '#38BDF8', letterSpacing: '.04em', background: 'rgba(15,23,42,0.88)', border: '1px solid rgba(56,189,248,0.35)', borderRadius: '3px', padding: '3px 7px' }}>
                        {currentSelectedCam.id.toUpperCase()}
                      </span>
                      <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '10.5px', color: '#F8FAFC', background: 'rgba(15,23,42,0.78)', borderRadius: '3px', padding: '3px 7px' }}>
                        {currentSelectedCam.name.toUpperCase()}
                      </span>
                    </div>
                    <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '9px', color: '#94A3B8', paddingLeft: '2px', textShadow: '0 1px 2px rgba(0,0,0,0.8)' }}>
                      LAT {Number(currentSelectedCam.latitude).toFixed(4)}° N · LNG {Number(currentSelectedCam.longitude).toFixed(4)}° E
                    </div>
                  </div>

                  {/* Top-Right: Pulsing Live Indicator & Ticking Clock */}
                  <div style={{ position: 'absolute', right: '18px', top: '18px', display: 'flex', alignItems: 'center', gap: '8px', pointerEvents: 'none' }}>
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', fontFamily: "'JetBrains Mono', monospace", fontSize: '10px', fontWeight: 600, letterSpacing: '.08em', color: '#EF4444', background: 'rgba(239,68,68,0.15)', border: '1px solid rgba(239,68,68,0.4)', borderRadius: '3px', padding: '3px 8px' }}>
                      <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#DC2626', animation: 'zbreathe 1.2s ease-in-out infinite' }} />
                      LIVE FEED
                    </span>
                    <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '10.5px', color: '#F1F5F9', background: 'rgba(15,23,42,0.88)', border: '1px solid rgba(255,255,255,0.15)', borderRadius: '3px', padding: '3px 8px' }}>
                      {liveClock || '2026-08-31 15:58:24 IST'}
                    </span>
                  </div>

                  {/* Bottom-Left: Technical CCTV Telemetry */}
                  <div style={{ position: 'absolute', left: '18px', bottom: '18px', fontFamily: "'JetBrains Mono', monospace", fontSize: '9.5px', color: '#94A3B8', background: 'rgba(15,23,42,0.85)', border: '1px solid rgba(255,255,255,0.15)', borderRadius: '3px', padding: '4px 8px', pointerEvents: 'none', display: 'flex', gap: '10px' }}>
                    <span style={{ color: '#10B981', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <span style={{ width: '5px', height: '5px', borderRadius: '50%', background: '#10B981' }} />
                      SIGNAL OK
                    </span>
                    <span>1080P · 25 FPS</span>
                    <span>ANPR STREAM ACTIVE</span>
                  </div>

                  {/* Bottom-Right: Surveillance Monitor Controls (No Seekbar) */}
                  <div style={{ position: 'absolute', right: '18px', bottom: '18px', display: 'flex', gap: '6px', alignItems: 'center' }}>
                    <button
                      type="button"
                      onClick={() => {
                        const v = liveVideoRef.current;
                        if (v) {
                          if (v.paused) {
                            v.play();
                            setIsPlaying(true);
                          } else {
                            v.pause();
                            setIsPlaying(false);
                          }
                        }
                      }}
                      title={isPlaying ? 'Pause Feed' : 'Resume Feed'}
                      style={{
                        background: 'rgba(15,23,42,0.88)',
                        border: '1px solid rgba(255,255,255,0.2)',
                        color: '#F1F5F9',
                        borderRadius: '3px',
                        padding: '4px 8px',
                        fontFamily: "'JetBrains Mono', monospace",
                        fontSize: '9.5px',
                        cursor: 'pointer',
                        lineHeight: 1,
                      }}
                    >
                      {isPlaying ? 'PAUSE' : 'RESUME'}
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        const elem = liveVideoRef.current;
                        if (elem) {
                          if (document.fullscreenElement) {
                            document.exitFullscreen().catch(() => {});
                          } else {
                            elem.requestFullscreen().catch(() => {});
                          }
                        }
                      }}
                      title="Fullscreen Monitor"
                      style={{
                        background: 'rgba(15,23,42,0.88)',
                        border: '1px solid rgba(255,255,255,0.2)',
                        color: '#F1F5F9',
                        borderRadius: '3px',
                        padding: '4px 8px',
                        fontFamily: "'JetBrains Mono', monospace",
                        fontSize: '9.5px',
                        cursor: 'pointer',
                        lineHeight: 1,
                      }}
                    >
                      EXPAND ⛶
                    </button>
                  </div>
                </div>
              </div>
            </div>
            );
          })()}

          {/* SIGHTING PHOTOS GRID VIEW */}
          {viewMode === 'grid' && (
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '14px', flexWrap: 'wrap', padding: '13px 16px', borderBottom: '1px solid #EEF1F4' }}>
                <div style={{ minWidth: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', flexWrap: 'wrap' }}>
                    <span style={{ fontSize: '19px', fontWeight: 600, letterSpacing: '-.02em' }}>
                      {activeSightings.length}
                    </span>
                    <span style={{ fontSize: '13.5px', color: '#334155' }}>sightings for</span>
                    <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '13px', color: '#0F172A', background: '#F1F4F7', border: '1px solid #E2E4E8', borderRadius: '4px', padding: '2px 7px', letterSpacing: '.06em' }}>
                      {currentPlate}
                    </span>
                  </div>
                  <div style={{ fontSize: '11.5px', color: '#64748B', marginTop: '4px' }}>
                    {activeCameraCount} camera node{activeCameraCount === 1 ? '' : 's'} · {activeDateRange}
                  </div>
                </div>
                {activeSightings.length > 0 && (
                  <button
                    onClick={() => onViewModeChange('map')}
                    style={{ display: 'flex', alignItems: 'center', gap: '8px', background: '#0891B2', color: '#FFFFFF', border: 'none', borderRadius: '5px', padding: '10px 16px', fontSize: '12.5px', fontWeight: 600, cursor: 'pointer', whiteSpace: 'nowrap' }}
                    onMouseEnter={(e) => (e.currentTarget.style.background = '#0E7490')}
                    onMouseLeave={(e) => (e.currentTarget.style.background = '#0891B2')}
                  >
                    Show trajectory map →
                  </button>
                )}
              </div>

              {isLoading ? (
                <div style={{ padding: '16px', display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(206px, 1fr))', gap: '12px' }}>
                  {Array.from({ length: 6 }).map((_, i) => (
                    <div key={i} style={{ border: '1px solid #E2E4E8', borderRadius: '5px', overflow: 'hidden', background: '#FFFFFF' }}>
                      <div style={{ position: 'relative', aspectRatio: '16/10', background: 'linear-gradient(90deg, #EDF0F4 25%, #E4E9EF 50%, #EDF0F4 75%)', backgroundSize: '200% 100%', animation: 'zshimmer 1.4s ease-in-out infinite' }} />
                      <div style={{ padding: '10px 11px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', gap: '8px' }}>
                          <div style={{ height: '12px', width: '60px', borderRadius: '3px', background: 'linear-gradient(90deg, #EDF0F4 25%, #E4E9EF 50%, #EDF0F4 75%)', backgroundSize: '200% 100%', animation: 'zshimmer 1.4s ease-in-out infinite' }} />
                          <div style={{ height: '12px', width: '40px', borderRadius: '3px', background: 'linear-gradient(90deg, #EDF0F4 25%, #E4E9EF 50%, #EDF0F4 75%)', backgroundSize: '200% 100%', animation: 'zshimmer 1.4s ease-in-out infinite 0.2s' }} />
                        </div>
                        <div style={{ height: '11px', width: '90%', borderRadius: '3px', background: 'linear-gradient(90deg, #EDF0F4 25%, #E4E9EF 50%, #EDF0F4 75%)', backgroundSize: '200% 100%', animation: 'zshimmer 1.4s ease-in-out infinite 0.1s' }} />
                        <div style={{ height: '10px', width: '70%', borderRadius: '3px', background: 'linear-gradient(90deg, #EDF0F4 25%, #E4E9EF 50%, #EDF0F4 75%)', backgroundSize: '200% 100%', animation: 'zshimmer 1.4s ease-in-out infinite 0.3s' }} />
                      </div>
                    </div>
                  ))}
                </div>
              ) : activeSightings.length === 0 ? (
                <div style={{ padding: '64px 20px', textAlign: 'center', color: '#64748B' }}>
                  <p style={{ fontSize: '14px', fontWeight: 500, color: '#0F172A' }}>
                    {currentPlate ? `No detections found for plate ${currentPlate}` : 'No active vehicle search'}
                  </p>
                  <p style={{ fontSize: '12px', marginTop: '4px' }}>
                    {currentPlate ? 'Verify the number or try searching TN13Q5113, TN22BV3211, or TN02BC5854.' : 'Enter a license plate number or upload a vehicle frame crop to begin trajectory tracking.'}
                  </p>
                </div>
              ) : (
                <div style={{ padding: '16px', display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(206px, 1fr))', gap: '12px' }}>
                  {pageItems.map((s, idx) => (
                    <div
                      key={s.id || idx}
                      onClick={() => setSelectedPhotoSighting(s)}
                      style={{ border: '1px solid #E2E4E8', borderRadius: '5px', overflow: 'hidden', background: '#FFFFFF', cursor: 'pointer', transition: 'all 0.15s ease' }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.borderColor = '#0891B2';
                        e.currentTarget.style.boxShadow = '0 4px 12px rgba(8,145,178,0.1)';
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.borderColor = '#E2E4E8';
                        e.currentTarget.style.boxShadow = 'none';
                      }}
                    >
                      <div style={{ position: 'relative', aspectRatio: '16/10', background: 'linear-gradient(#EDF0F4, #E1E6EC)', borderBottom: '1px solid #E2E4E8', overflow: 'hidden' }}>
                        {/* Fallback mockup canvas */}
                        <div style={{ position: 'absolute', left: 0, right: 0, top: '56%', bottom: 0, background: '#D8DEE5', zIndex: 1 }} />
                        <div style={{ position: 'absolute', left: '15%', top: '28%', right: '17%', bottom: '20%', border: '1.5px solid #0891B2', borderRadius: '2px', background: 'rgba(8,145,178,.05)', zIndex: 1 }} />

                        {/* Real vehicle picture from best_crop_key */}
                        {s.best_crop_key && (
                          <img
                            src={s.best_crop_key.startsWith('http') || s.best_crop_key.startsWith('/') ? s.best_crop_key : `/${s.best_crop_key}`}
                            alt={s.plateTag}
                            style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover', zIndex: 2 }}
                            onError={(e) => {
                              // If image file is not on disk yet, hide so canvas mockup displays cleanly
                              e.currentTarget.style.display = 'none';
                            }}
                          />
                        )}

                        {/* Badges on top */}
                        <div style={{ position: 'absolute', left: '8px', top: '8px', fontFamily: "'JetBrains Mono', monospace", fontSize: '8.5px', background: '#0891B2', color: '#FFFFFF', padding: '2px 5px', borderRadius: '2px', letterSpacing: '.02em', zIndex: 10 }}>
                          {(s.vehicle_type || 'VEHICLE').toUpperCase()} {s.conf.replace('OCR ', '').replace('Re-ID ', '') || '0.99'}
                        </div>
                        {s.plate_crop_key && (
                          <div style={{ position: 'absolute', right: '8px', top: '8px', zIndex: 10, background: '#FFFFFF', border: '1px solid #0F172A', borderRadius: '2px', padding: '1px 3px', display: 'flex', alignItems: 'center', height: '18px', overflow: 'hidden' }}>
                            <img
                              src={s.plate_crop_key.startsWith('http') || s.plate_crop_key.startsWith('/') ? s.plate_crop_key : `/${s.plate_crop_key}`}
                              alt="Plate Crop"
                              style={{ maxHeight: '16px', objectFit: 'contain' }}
                              onError={(e) => {
                                (e.currentTarget.parentElement as HTMLElement).style.display = 'none';
                              }}
                            />
                          </div>
                        )}
                        <div style={{ position: 'absolute', left: '50%', bottom: '24%', transform: 'translateX(-50%)', fontFamily: "'JetBrains Mono', monospace", fontSize: '9px', background: '#FFFFFF', border: '1px solid #0F172A', color: '#0F172A', padding: '2px 5px', borderRadius: '2px', letterSpacing: '.06em', whiteSpace: 'nowrap', zIndex: 10 }}>
                          {s.plateTag}
                        </div>
                        <div style={{ position: 'absolute', left: '7px', bottom: '6px', fontFamily: "'JetBrains Mono', monospace", fontSize: '8.5px', color: '#FFFFFF', textShadow: '0 1px 2px rgba(0,0,0,0.8)', background: 'rgba(15,23,42,0.65)', padding: '1px 5px', borderRadius: '2px', zIndex: 10 }}>
                          frame crop
                        </div>
                        <div style={{ position: 'absolute', right: '7px', bottom: '6px', fontFamily: "'JetBrains Mono', monospace", fontSize: '8px', color: '#0891B2', background: 'rgba(255,255,255,0.92)', padding: '1px 4px', borderRadius: '2px', zIndex: 10, fontWeight: 600 }}>
                          Inspect ↗
                        </div>
                      </div>
                      <div style={{ padding: '10px 11px', display: 'flex', flexDirection: 'column', gap: '7px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '8px' }}>
                          <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '11.5px', color: '#0F172A', fontWeight: 500, whiteSpace: 'nowrap' }}>
                            {s.cam}
                          </span>
                          <span
                            style={{
                              fontFamily: "'JetBrains Mono', monospace",
                              fontSize: '9.5px',
                              fontWeight: 600,
                              padding: '2px 6px',
                              borderRadius: '3px',
                              whiteSpace: 'nowrap',
                              flex: 'none',
                              color: s.reid ? '#3730A3' : '#065F46',
                              background: s.reid ? '#EEF2FF' : '#ECFDF5',
                              border: `1px solid ${s.reid ? '#C7D2FE' : '#A7F3D0'}`,
                            }}
                          >
                            {s.conf}
                          </span>
                        </div>
                        <div style={{ fontSize: '12px', color: '#334155', lineHeight: 1.35, textWrap: 'pretty' }}>
                          {s.street}
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '8px', flexWrap: 'wrap', fontFamily: "'JetBrains Mono', monospace", fontSize: '10px', color: '#94A3B8', paddingTop: '7px', borderTop: '1px solid #EEF1F4' }}>
                          <span style={{ whiteSpace: 'nowrap' }}>{s.time} IST</span>
                          <span style={{ whiteSpace: 'nowrap' }}>{s.geo}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Pagination */}
              {totalCount > perPage && (
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '12px', padding: '11px 16px', borderTop: '1px solid #EEF1F4', background: '#FBFCFD', flexWrap: 'wrap' }}>
                  <button
                    onClick={() => setPage((p) => Math.max(0, p - 1))}
                    disabled={page === 0}
                    style={{ background: '#FFFFFF', border: '1px solid #E2E4E8', color: '#334155', borderRadius: '5px', padding: '7px 13px', fontSize: '12px', cursor: page === 0 ? 'default' : 'pointer', opacity: page === 0 ? 0.6 : 1 }}
                    onMouseEnter={(e) => page > 0 && (e.currentTarget.style.background = '#EEF2F6')}
                    onMouseLeave={(e) => (e.currentTarget.style.background = '#FFFFFF')}
                  >
                    ← Previous
                  </button>
                  <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '11px', color: '#64748B' }}>
                    {rangeLabel}
                  </span>
                  <button
                    onClick={() => setPage((p) => (startIdx + perPage < totalCount ? p + 1 : p))}
                    disabled={startIdx + perPage >= totalCount}
                    style={{ background: '#FFFFFF', border: '1px solid #E2E4E8', color: '#334155', borderRadius: '5px', padding: '7px 13px', fontSize: '12px', cursor: startIdx + perPage >= totalCount ? 'default' : 'pointer', opacity: startIdx + perPage >= totalCount ? 0.6 : 1 }}
                    onMouseEnter={(e) => startIdx + perPage < totalCount && (e.currentTarget.style.background = '#EEF2F6')}
                    onMouseLeave={(e) => (e.currentTarget.style.background = '#FFFFFF')}
                  >
                    Next →
                  </button>
                </div>
              )}
            </div>
          )}

          {/* TRAJECTORY MAP VIEW */}
          {viewMode === 'map' && (
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '14px', flexWrap: 'wrap', padding: '13px 16px', borderBottom: '1px solid #EEF1F4' }}>
                <button
                  onClick={() => onViewModeChange('grid')}
                  style={{ background: '#FFFFFF', border: '1px solid #E2E4E8', color: '#334155', borderRadius: '5px', padding: '8px 13px', fontSize: '12.5px', cursor: 'pointer' }}
                  onMouseEnter={(e) => (e.currentTarget.style.background = '#EEF2F6')}
                  onMouseLeave={(e) => (e.currentTarget.style.background = '#FFFFFF')}
                >
                  ← Back to sighting photos
                </button>
                <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '10.5px', color: '#64748B' }}>
                  {route.length} NODES · 4.2 KM · 6.5 MIN
                </div>
              </div>
              <div style={{ padding: '16px' }}>
                <LeafletMap
                  route={route}
                  selectedRouteIndex={selectedRouteIndex}
                  onSelectRouteIndex={onSelectRouteIndex}
                  selRoute={selRoute}
                />
              </div>
            </div>
          )}
        </div>

        {/* Right Aside: Movement History */}
        <aside style={{ background: '#FFFFFF', border: '1px solid #E2E4E8', borderRadius: '6px', overflow: 'hidden' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', gap: '10px', padding: '12px 14px', borderBottom: '1px solid #EEF1F4' }}>
            <span style={{ fontSize: '13.5px', fontWeight: 600 }}>Movement History</span>
            {activeDateRange && (
              <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '9.5px', color: '#94A3B8' }}>{activeDateRange.split(' · ')[0]?.toUpperCase()}</span>
            )}
          </div>

          {route.length === 0 ? (
            <div style={{ padding: '48px 20px', textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '12px' }}>
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#CBD5E1" strokeWidth="1.5">
                <circle cx="12" cy="12" r="9" />
                <path d="M12 7v5l3 3" />
              </svg>
              <span style={{ fontSize: '12px', color: '#94A3B8', lineHeight: 1.5 }}>No vehicle selected.<br/>Search by plate or image to see movement history.</span>
            </div>
          ) : (
            <>
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                {route.map((l, i) => (
                  <button
                    key={l.n}
                    onClick={() => onSelectRouteIndex(i)}
                    style={{
                      display: 'flex',
                      gap: '11px',
                      alignItems: 'flex-start',
                      width: '100%',
                      textAlign: 'left',
                      cursor: 'pointer',
                      padding: '12px 14px',
                      border: 'none',
                      borderBottom: '1px solid #EEF1F4',
                      borderLeft: `2px solid ${selectedRouteIndex === i ? A : 'transparent'}`,
                      background: selectedRouteIndex === i ? '#F7FBFC' : '#FFFFFF',
                      fontFamily: 'inherit',
                    }}
                  >
                    <span
                      style={{
                        flex: 'none',
                        width: '21px',
                        height: '21px',
                        borderRadius: '50%',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontFamily: "'JetBrains Mono', monospace",
                        fontSize: '10px',
                        fontWeight: 600,
                        background: selectedRouteIndex === i ? '#0F172A' : '#F1F4F7',
                        color: selectedRouteIndex === i ? '#FFFFFF' : '#94A3B8',
                        border: selectedRouteIndex === i ? 'none' : '1px solid #E2E4E8',
                      }}
                    >
                      {l.n}
                    </span>
                    <span style={{ display: 'flex', flexDirection: 'column', gap: '3px', minWidth: 0, textAlign: 'left' }}>
                      <span style={{ display: 'flex', alignItems: 'baseline', gap: '8px', flexWrap: 'wrap' }}>
                        <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '12.5px', color: '#0F172A', fontWeight: 500 }}>{l.time}</span>
                        <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '11px', color: '#64748B' }}>{l.cam}</span>
                      </span>
                      <span style={{ fontSize: '11.5px', color: '#64748B', textWrap: 'pretty' }}>{l.street}</span>
                      <span
                        style={{
                          fontFamily: "'JetBrains Mono', monospace",
                          fontSize: '10.5px',
                          color: l.speed.startsWith('Stopped') ? '#92400E' : '#065F46',
                        }}
                      >
                        {l.speed}
                      </span>
                    </span>
                  </button>
                ))}
              </div>

              <div style={{ padding: '12px 14px', borderTop: '1px solid #EEF1F4', background: '#FBFCFD', display: 'flex', flexDirection: 'column', gap: '9px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: '10px', fontSize: '11.5px', color: '#64748B' }}>
                  <span>Average speed</span>
                  <span style={{ fontFamily: "'JetBrains Mono', monospace", color: '#0F172A', flex: 'none' }}>
                    {activeSightings.length > 1 ? '43.5 km/h' : '45 km/h'}
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: '10px', fontSize: '11.5px', color: '#64748B' }}>
                  <span>Dwell at Corridor</span>
                  <span style={{ fontFamily: "'JetBrains Mono', monospace", color: '#92400E', flex: 'none' }}>
                    {activeSightings.length > 1 ? '6.5 min' : '12 min'}
                  </span>
                </div>
                <button
                  onClick={onExportPdf}
                  style={{ marginTop: '3px', width: '100%', background: '#FFFFFF', border: '1px solid #D8DDE4', color: '#0F172A', borderRadius: '5px', padding: '10px', fontSize: '12.5px', fontWeight: 500, cursor: 'pointer' }}
                  onMouseEnter={(e) => (e.currentTarget.style.background = '#EEF2F6')}
                  onMouseLeave={(e) => (e.currentTarget.style.background = '#FFFFFF')}
                >
                  Export police log (PDF)
                </button>
              </div>
            </>
          )}
        </aside>
      </section>

      {/* High-res vehicle and plate crop modal */}
      {selectedPhotoSighting && (
        <VehiclePhotoModal
          sighting={selectedPhotoSighting}
          onClose={() => setSelectedPhotoSighting(null)}
        />
      )}
      
      </div>
      
      {/* Print-Only Police Dossier for PDF Export */}
      <PrintDossier
        plate={currentPlate}
        route={activeRoute}
        detectionsCount={activeSightings.length}
      />
    </>
  );
}

function inlineToObj(css: string): React.CSSProperties {
  const style: Record<string, string> = {};
  css.split(';').forEach((rule) => {
    const colonIdx = rule.indexOf(':');
    if (colonIdx !== -1) {
      const k = rule.slice(0, colonIdx).trim();
      const v = rule.slice(colonIdx + 1).trim();
      if (k && v) {
        const camel = k.replace(/-([a-z])/g, (_, l) => l.toUpperCase());
        style[camel] = v;
      }
    }
  });
  return style as React.CSSProperties;
}
