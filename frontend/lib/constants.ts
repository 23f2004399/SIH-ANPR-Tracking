import {
  Camera,
  VehicleTrack,
  VehicleObservation,
  EvidenceAsset,
  SimilarVehicle,
  TrafficOverview,
  SegmentTraffic,
  Job,
  TrafficAdvisory,
} from '@/types/api';

// Institutional Metadata
export const SYSTEM_METADATA = {
  appName: 'ZyroTrace AI',
  subtitle: 'Sovereign Multi-Camera ANPR Telemetry & Traffic Intelligence',
  institutionalAgency: 'Bharat Electronics Ltd (BEL) · Ministry of Road Transport & Highways (MoRTH)',
  clearanceClassification: 'NATIONAL SECURITY LEVEL-3 // SOVEREIGN C4I ACCESS',
  stationNode: 'NORTH DELHI C4I HEADQUARTERS // SECTOR 14',
};

// Mock Cameras Registry across Delhi-NCR Key Highway Junctions
export const MOCK_CAMERAS: Camera[] = [
  {
    id: 'CAM-12',
    name: 'Azadpur Mandi Arterial Node // Cam-12',
    latitude: 28.7095,
    longitude: 77.1725,
    location_label: 'Azadpur Junction, Ring Rd',
    road_segment_id: 'seg-or-w',
    is_active: true,
    created_at: '2026-01-10T08:00:00Z',
  },
  {
    id: 'CAM-14',
    name: 'Shahdara Flyover East Gantry // Cam-14',
    latitude: 28.6732,
    longitude: 77.291,
    location_label: 'Shahdara GT Road Flyover',
    road_segment_id: 'seg-east-gt',
    is_active: true,
    created_at: '2026-01-12T09:30:00Z',
  },
  {
    id: 'CAM-18',
    name: 'Mukarba Chowk Cloverleaf Gantry // Cam-18',
    latitude: 28.7428,
    longitude: 77.1512,
    location_label: 'Mukarba Interchange, NH-44',
    road_segment_id: 'seg-nh44-n',
    is_active: true,
    created_at: '2026-01-15T11:00:00Z',
  },
  {
    id: 'CAM-26',
    name: 'GT Karnal Road High-Speed HUD // Cam-26',
    latitude: 28.7845,
    longitude: 77.1352,
    location_label: 'NH-44 KM 14.2 North Corridor',
    road_segment_id: 'seg-nh44-n',
    is_active: true,
    created_at: '2026-02-01T04:00:00Z',
  },
  {
    id: 'CAM-31',
    name: 'Singhu Border Inter-State Toll Gantry // Cam-31',
    latitude: 28.8415,
    longitude: 77.1128,
    location_label: 'Delhi-Haryana Border Toll Checkpoint',
    road_segment_id: 'seg-nh44-n',
    is_active: true,
    created_at: '2026-02-05T07:20:00Z',
  },
  {
    id: 'CAM-08',
    name: 'Ashram Flyover South Expressway // Cam-08',
    latitude: 28.571,
    longitude: 77.258,
    location_label: 'Ashram Chowk Inner Ring Road',
    road_segment_id: 'seg-ring-s',
    is_active: true,
    created_at: '2026-01-05T12:00:00Z',
  },
  {
    id: 'CAM-04',
    name: 'DND Flyway Yamuna Bridge Gantry // Cam-04',
    latitude: 28.5832,
    longitude: 77.2798,
    location_label: 'DND Toll Approach Yamuna River',
    road_segment_id: 'seg-dnd',
    is_active: true,
    created_at: '2026-01-08T10:00:00Z',
  },
];

// Verified Pre-loaded Vehicle Tracks
export const MOCK_VEHICLE_TRACKS: VehicleTrack[] = [
  {
    id: 9021,
    first_seen_at: '2026-09-29T14:10:15+05:30',
    last_seen_at: '2026-09-29T14:48:22+05:30',
    primary_plate: 'HR 26 CX 9021',
    normalized_plate: 'HR26CX9021',
    confidence: 0.984,
    vehicle_type: 'car',
    vehicle_color: 'Arctic White',
    make_model: 'Hyundai Creta SX (O) 2024',
    is_hotlist: true,
    hotlist_reason: 'RED CORNER // ARMED ROBBERY SUSPECT (CRIME BRANCH FIR #108/2026)',
    owner_name_masked: 'R**** K**** S****',
    registration_state: 'Haryana (Gurugram RTO)',
    vahan_status: 'FLAGGED / POLICE SURVEILLANCE INTERCEPT',
  },
  {
    id: 1234,
    first_seen_at: '2026-09-29T13:45:00+05:30',
    last_seen_at: '2026-09-29T14:25:10+05:30',
    primary_plate: 'DL 01 AB 1234',
    normalized_plate: 'DL01AB1234',
    confidence: 0.962,
    vehicle_type: 'car',
    vehicle_color: 'Metallic Silver',
    make_model: 'Maruti Suzuki Swift Dzire VXi',
    is_hotlist: true,
    hotlist_reason: 'STOLEN VEHICLE ALERT (FIR #294/2026, CIVIL LINES POLICE STATION)',
    owner_name_masked: 'A**** P**** V****',
    registration_state: 'Delhi (Mall Road RTO)',
    vahan_status: 'STOLEN / ACTIVE SEIZURE WARRANT',
  },
  {
    id: 8844,
    first_seen_at: '2026-09-29T14:02:18+05:30',
    last_seen_at: '2026-09-29T14:30:00+05:30',
    primary_plate: 'UP 16 Z 8844',
    normalized_plate: 'UP16Z8844',
    confidence: 0.941,
    vehicle_type: 'truck',
    vehicle_color: 'Industrial Yellow / Grey Cab',
    make_model: 'Tata Prima Multi-Axle 35-Ton Freight',
    is_hotlist: true,
    hotlist_reason: 'RESTRICTED PEAK ROUTE & OVERHEIGHT HAZARD (RING ROAD VIOLATION)',
    owner_name_masked: 'N**** L**** C****',
    registration_state: 'Uttar Pradesh (Noida RTO)',
    vahan_status: 'OVERHEIGHT VIOLATION PENDING E-CHALLAN',
  },
];

// Chronological Multi-Camera Sightings for Track 9021 (HR 26 CX 9021)
export const MOCK_OBSERVATIONS_9021: VehicleObservation[] = [
  {
    id: 101,
    observation_id: 101,
    track_id: 9021,
    camera_id: 'CAM-12',
    camera_name: 'Azadpur Mandi Arterial Node // Cam-12',
    observed_at: '2026-09-29T14:10:15+05:30',
    plate_text: 'HR 26 CX 9021',
    confidence: 0.978,
    speed_kmh: 62,
    latitude: 28.7095,
    longitude: 77.1725,
  },
  {
    id: 102,
    observation_id: 102,
    track_id: 9021,
    camera_id: 'CAM-18',
    camera_name: 'Mukarba Chowk Cloverleaf Gantry // Cam-18',
    observed_at: '2026-09-29T14:18:40+05:30',
    plate_text: 'HR 26 CX 9021',
    confidence: 0.985,
    speed_kmh: 78,
    latitude: 28.7428,
    longitude: 77.1512,
  },
  {
    id: 103,
    observation_id: 103,
    track_id: 9021,
    camera_id: 'CAM-26',
    camera_name: 'GT Karnal Road High-Speed HUD // Cam-26',
    observed_at: '2026-09-29T14:32:04+05:30',
    plate_text: 'HR 26 CX 9021',
    confidence: 0.991,
    speed_kmh: 94, // OVERSPEED
    latitude: 28.7845,
    longitude: 77.1352,
  },
  {
    id: 104,
    observation_id: 104,
    track_id: 9021,
    camera_id: 'CAM-31',
    camera_name: 'Singhu Border Inter-State Toll Gantry // Cam-31',
    observed_at: '2026-09-29T14:48:22+05:30',
    plate_text: 'HR 26 CX 9021',
    confidence: 0.982,
    speed_kmh: 71,
    latitude: 28.8415,
    longitude: 77.1128,
  },
];

// Sightings for Track 1234 (DL 01 AB 1234)
export const MOCK_OBSERVATIONS_1234: VehicleObservation[] = [
  {
    id: 201,
    observation_id: 201,
    track_id: 1234,
    camera_id: 'CAM-14',
    camera_name: 'Shahdara Flyover East Gantry // Cam-14',
    observed_at: '2026-09-29T14:25:10+05:30',
    plate_text: 'DL 01 AB 1234',
    confidence: 0.962,
    speed_kmh: 58,
    latitude: 28.6732,
    longitude: 77.291,
  },
];

// Sightings for Track 8844 (UP 16 Z 8844)
export const MOCK_OBSERVATIONS_8844: VehicleObservation[] = [
  {
    id: 301,
    observation_id: 301,
    track_id: 8844,
    camera_id: 'CAM-08',
    camera_name: 'Ashram Flyover South Expressway // Cam-08',
    observed_at: '2026-09-29T14:30:00+05:30',
    plate_text: 'UP 16 Z 8844',
    confidence: 0.941,
    speed_kmh: 42,
    latitude: 28.571,
    longitude: 77.258,
  },
];

// Forensic Evidence Assets for Track 9021
export const MOCK_EVIDENCE_9021: EvidenceAsset[] = [
  {
    id: 501,
    track_id: 9021,
    timestamp: '2026-09-29T14:32:04+05:30',
    asset_type: 'plate_crop',
    file_url: 'https://images.unsplash.com/photo-1549399542-7e3f8b79c341?auto=format&fit=crop&w=400&q=80',
    bounding_box: { x: 412, y: 530, width: 220, height: 75 },
  },
  {
    id: 502,
    track_id: 9021,
    timestamp: '2026-09-29T14:32:04+05:30',
    asset_type: 'vehicle_crop',
    file_url: 'https://images.unsplash.com/photo-1552519507-da3b142c6e3d?auto=format&fit=crop&w=700&q=80',
    bounding_box: { x: 280, y: 340, width: 520, height: 380 },
  },
  {
    id: 503,
    track_id: 9021,
    timestamp: '2026-09-29T14:32:04+05:30',
    asset_type: 'full_frame',
    file_url: 'https://images.unsplash.com/photo-1506521781263-d8422e82f27a?auto=format&fit=crop&w=1200&q=80',
    bounding_box: { x: 280, y: 340, width: 520, height: 380 },
  },
];

// Vector Re-ID Similar Vehicles for Track 9021
export const MOCK_SIMILAR_VEHICLES: SimilarVehicle[] = [
  {
    track_id: 9102,
    similarity_score: 0.942,
    plate_text: 'HR 26 DQ 4410',
    vehicle_type: 'SUV (White Hyundai Creta 2023)',
    color: 'White',
    last_seen_at: '2026-09-29T13:58:10+05:30',
    thumbnail_url: 'https://images.unsplash.com/photo-1552519507-da3b142c6e3d?auto=format&fit=crop&w=300&q=80',
    location_name: 'Dhaula Kuan Underpass Cam-03',
  },
  {
    track_id: 9145,
    similarity_score: 0.915,
    plate_text: 'DL 08 CC 8932',
    vehicle_type: 'SUV (White Kia Seltos Facelift)',
    color: 'Pearl White',
    last_seen_at: '2026-09-29T14:14:00+05:30',
    thumbnail_url: 'https://images.unsplash.com/photo-1549399542-7e3f8b79c341?auto=format&fit=crop&w=300&q=80',
    location_name: 'Outer Ring Rd Rohini Cam-07',
  },
  {
    track_id: 9188,
    similarity_score: 0.887,
    plate_text: 'UP 14 ER 1109',
    vehicle_type: 'SUV (White Maruti Grand Vitara)',
    color: 'Arctic White',
    last_seen_at: '2026-09-29T14:20:15+05:30',
    thumbnail_url: 'https://images.unsplash.com/photo-1552519507-da3b142c6e3d?auto=format&fit=crop&w=300&q=80',
    location_name: 'Noida Toll Plaza Gantry Cam-05',
  },
];

// Urban Corridor Segments
export const MOCK_SEGMENTS: SegmentTraffic[] = [
  {
    road_segment_id: 'seg-nh44-n',
    segment_name: 'NH-44 North Trunk (Mukarba Chowk ── Singhu Border)',
    total_vehicles: 46280,
    avg_speed_kmh: 76.4,
    congestion_status: 'fluid',
    cameras: [
      { id: 'CAM-18', name: 'Mukarba Chowk Cloverleaf Gantry', latitude: 28.7428, longitude: 77.1512 },
      { id: 'CAM-26', name: 'GT Karnal Road High-Speed HUD', latitude: 28.7845, longitude: 77.1352 },
      { id: 'CAM-31', name: 'Singhu Border Inter-State Toll Gantry', latitude: 28.8415, longitude: 77.1128 },
    ],
    coordinates: [
      [28.7428, 77.1512],
      [28.7845, 77.1352],
      [28.8415, 77.1128],
    ],
  },
  {
    road_segment_id: 'seg-ring-s',
    segment_name: 'Inner Ring Road Arterial (AIIMS ── Ashram Chowk)',
    total_vehicles: 68140,
    avg_speed_kmh: 21.8,
    congestion_status: 'gridlock',
    cameras: [
      { id: 'CAM-08', name: 'Ashram Flyover South Expressway', latitude: 28.571, longitude: 77.258 },
    ],
    coordinates: [
      [28.5672, 77.2100],
      [28.571, 77.258],
    ],
  },
  {
    road_segment_id: 'seg-dnd',
    segment_name: 'Delhi-Noida Direct (DND) Flyway Expressway',
    total_vehicles: 38400,
    avg_speed_kmh: 58.2,
    congestion_status: 'fluid',
    cameras: [
      { id: 'CAM-04', name: 'DND Flyway Yamuna Bridge Gantry', latitude: 28.5832, longitude: 77.2798 },
    ],
    coordinates: [
      [28.5832, 77.2798],
      [28.5750, 77.3100],
    ],
  },
  {
    road_segment_id: 'seg-or-w',
    segment_name: 'Outer Ring Road West (Peeragarhi ── Azadpur Mandi)',
    total_vehicles: 52910,
    avg_speed_kmh: 36.5,
    congestion_status: 'heavy',
    cameras: [
      { id: 'CAM-12', name: 'Azadpur Mandi Arterial Node', latitude: 28.7095, longitude: 77.1725 },
    ],
    coordinates: [
      [28.6780, 77.0950],
      [28.7095, 77.1725],
    ],
  },
];

// Traffic Overview
export const MOCK_TRAFFIC_OVERVIEW: TrafficOverview = {
  window_start: '2026-09-28T14:30:00+05:30',
  window_end: '2026-09-29T14:30:00+05:30',
  distinct_tracks: 524000,
  estimated_flow_rate_per_hour: 21833,
  avg_speed_kmh: 38.2,
  congestion_index: 'high',
  estimated_co2_kg: 142500,
  delta_volume_pct: 3.4,
  delta_speed_pct: -5.1,
};

// Smart City AI Traffic Advisories
export const MOCK_ADVISORIES: TrafficAdvisory[] = [
  {
    id: 'ADV-01',
    title: 'Peak Corridor Freight Diversion (Ashram ── Badarpur)',
    priority: 'urgent',
    impact_summary: 'Divert 3+ axle freight trucks to Western Peripheral Expressway via KMP corridor.',
    co2_reduction_kg: 4200,
    time_saved_minutes: 24,
    recommended_action: 'Activate dynamic VMS boards at Sarita Vihar & Ashram underpass. Trigger signal plan S-44.',
    timestamp: '2026-09-29T14:15:00+05:30',
  },
  {
    id: 'ADV-02',
    title: 'Adaptive Signal Timing Extension (NH-44 Mukarba Southbound)',
    priority: 'advisory',
    impact_summary: 'Extend Phase-2 green cycle by +32 seconds on Southbound slip lane.',
    co2_reduction_kg: 1850,
    time_saved_minutes: 14,
    recommended_action: 'Coordinate with Delhi Traffic Police Central Signal Controller (ITMS Node #9).',
    timestamp: '2026-09-29T14:22:00+05:30',
  },
  {
    id: 'ADV-03',
    title: 'Reversible Toll Lane Activation (DND Flyway Eastbound)',
    priority: 'info',
    impact_summary: 'Anticipate evening commuter surge from Okhla to Noida Sector 16.',
    co2_reduction_kg: 950,
    time_saved_minutes: 8,
    recommended_action: 'Open reversible lane #4 from 17:30 to 20:00 to eliminate tailback queue.',
    timestamp: '2026-09-29T14:28:00+05:30',
  },
];

// Video Ingestion Pipeline Jobs
export const MOCK_JOBS: Job[] = [
  {
    id: 'job-9081',
    camera_id: 'CAM-26',
    source_file_key: 'cctv_feeds/gt_karnal_20260929_1400.mp4',
    status: 'completed',
    progress: 100,
    total_frames: 18000,
    processed_frames: 18000,
    detected_tracks: 1420,
    created_at: '2026-09-29T14:00:00+05:30',
    updated_at: '2026-09-29T14:10:00+05:30',
  },
  {
    id: 'job-9082',
    camera_id: 'CAM-18',
    source_file_key: 'cctv_feeds/mukarba_chowk_20260929_1415.mp4',
    status: 'processing',
    progress: 68,
    total_frames: 12000,
    processed_frames: 8160,
    detected_tracks: 890,
    created_at: '2026-09-29T14:15:00+05:30',
    updated_at: '2026-09-29T14:28:00+05:30',
  },
  {
    id: 'job-9083',
    camera_id: 'CAM-08',
    source_file_key: 'cctv_feeds/ashram_flyover_live_stream.m3u8',
    status: 'processing',
    progress: 42,
    total_frames: 25000,
    processed_frames: 10500,
    detected_tracks: 1140,
    created_at: '2026-09-29T14:20:00+05:30',
    updated_at: '2026-09-29T14:32:00+05:30',
  },
];
