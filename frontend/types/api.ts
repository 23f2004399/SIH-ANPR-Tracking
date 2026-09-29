// Types strictly matching ZyroTrace AI OpenAPI schema (api.json & context.md)

export interface ApiEnvelope<T> {
  success: boolean;
  data: T;
  message?: string;
}

export interface Camera {
  id: string;
  name: string;
  latitude: number;
  longitude: number;
  location_label: string | null;
  road_segment_id: string | null;
  is_active: boolean;
  created_at?: string;
}

export interface CameraIn {
  id: string;
  name: string;
  latitude: number;
  longitude: number;
  location_label?: string | null;
  road_segment_id?: string | null;
  is_active?: boolean;
}

export interface JobIn {
  camera_id: string;
  source_file_key: string;
}

export type JobStatus = 'pending' | 'processing' | 'completed' | 'failed';

export interface Job {
  id: string;
  camera_id: string;
  source_file_key: string;
  status: JobStatus;
  progress: number;
  total_frames?: number;
  processed_frames?: number;
  detected_tracks?: number;
  error_message?: string | null;
  created_at: string;
  updated_at?: string;
}

export type VehicleCategory = 'car' | 'truck' | 'motorcycle' | 'bus';

export interface VehicleTrack {
  id: number;
  first_seen_at: string;
  last_seen_at: string;
  primary_plate: string;
  normalized_plate: string;
  confidence: number;
  vehicle_type: VehicleCategory;
  vehicle_color?: string;
  make_model?: string;
  is_hotlist?: boolean;
  hotlist_reason?: string;
  owner_name_masked?: string;
  registration_state?: string;
  vahan_status?: string;
}

export interface VehicleObservation {
  id: number;
  observation_id: number;
  track_id: number;
  camera_id: string;
  camera_name?: string;
  observed_at: string;
  plate_text: string;
  confidence: number;
  speed_kmh?: number;
  latitude?: number;
  longitude?: number;
  image_url?: string;
}

export interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface EvidenceAsset {
  id: number;
  track_id: number;
  timestamp: string;
  asset_type: 'plate_crop' | 'vehicle_crop' | 'full_frame';
  file_url: string;
  bounding_box: BoundingBox;
}

export interface SimilarVehicle {
  track_id: number;
  similarity_score: number;
  plate_text: string;
  vehicle_type: string;
  color: string;
  last_seen_at: string;
  thumbnail_url: string;
  location_name?: string;
}

export type CongestionIndex = 'low' | 'moderate' | 'high' | 'critical';

export interface TrafficOverview {
  window_start: string;
  window_end: string;
  distinct_tracks: number;
  estimated_flow_rate_per_hour: number;
  avg_speed_kmh: number;
  congestion_index: CongestionIndex;
  estimated_co2_kg: number;
  delta_volume_pct?: number;
  delta_speed_pct?: number;
}

export interface CameraTraffic {
  camera_id: string;
  camera_name: string;
  vehicle_count: number;
  avg_speed_kmh: number;
  congestion_level: 'fluid' | 'moderate' | 'heavy' | 'gridlock';
}

export interface SegmentCameraNode {
  id: string;
  name: string;
  latitude: number;
  longitude: number;
}

export interface SegmentTraffic {
  road_segment_id: string;
  segment_name: string;
  total_vehicles: number;
  avg_speed_kmh: number;
  congestion_status: 'fluid' | 'heavy' | 'gridlock';
  cameras: SegmentCameraNode[];
  coordinates?: Array<[number, number]>;
}

export interface TrafficAggregateRow {
  id: number;
  bucket_time: string;
  camera_id?: string;
  segment_id?: string;
  vehicle_count: number;
  avg_speed_kmh: number;
}

export interface TrafficAdvisory {
  id: string;
  title: string;
  priority: 'urgent' | 'advisory' | 'info';
  impact_summary: string;
  co2_reduction_kg: number;
  time_saved_minutes: number;
  recommended_action: string;
  timestamp: string;
}
