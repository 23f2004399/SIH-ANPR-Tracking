import { apiClient } from './client';
import { Job, JobIn } from '@/types/api';
import { MOCK_JOBS } from '../constants';

export async function fetchJobs(
  limit: number = 50,
  offset: number = 0
): Promise<Job[]> {
  try {
    const res = await apiClient.get('/api/v1/jobs', {
      params: { limit, offset },
    });
    const payload = res.data;
    const items = payload?.data || (Array.isArray(payload) ? payload : null);
    if (Array.isArray(items)) {
      return items.map((j) => ({
        id: String(j.id),
        camera_id: j.camera_id,
        source_file_key: j.source_file_key,
        status: j.status || 'queued',
        progress: typeof j.progress === 'number' ? Math.round(j.progress <= 1 ? j.progress * 100 : j.progress) : 0,
        total_frames: j.total_frames || 10000,
        processed_frames: j.processed_frames || 0,
        detected_tracks: j.detected_tracks || 0,
        error_message: j.error_message || null,
        created_at: j.created_at || new Date().toISOString(),
        updated_at: j.completed_at || j.started_at,
      }));
    }
  } catch (error) {
    console.warn('[ZyroTrace] GET /api/v1/jobs failed. Using cached jobs.', error);
  }
  return MOCK_JOBS;
}

export async function fetchJobById(jobId: string): Promise<Job | null> {
  try {
    const numericId = parseInt(jobId.replace(/\D/g, ''), 10);
    const res = await apiClient.get(`/api/v1/jobs/${isNaN(numericId) ? jobId : numericId}`);
    const j = res.data?.data || res.data;
    if (j) {
      return {
        id: String(j.id),
        camera_id: j.camera_id,
        source_file_key: j.source_file_key,
        status: j.status,
        progress: typeof j.progress === 'number' ? Math.round(j.progress <= 1 ? j.progress * 100 : j.progress) : 0,
        total_frames: j.total_frames || 10000,
        processed_frames: j.processed_frames || 0,
        detected_tracks: j.detected_tracks || 0,
        error_message: j.error_message || null,
        created_at: j.created_at || new Date().toISOString(),
      };
    }
  } catch (error) {
    console.warn(`[ZyroTrace] GET /api/v1/jobs/${jobId} failed.`, error);
  }
  return MOCK_JOBS.find((j) => j.id === jobId) || null;
}

export async function createJob(jobIn: JobIn): Promise<Job> {
  const res = await apiClient.post('/api/v1/jobs', {
    camera_id: jobIn.camera_id,
    source_file_key: jobIn.source_file_key,
  });
  const j = res.data?.data || res.data;
  return {
    id: String(j.id || Math.floor(1000 + Math.random() * 9000)),
    camera_id: j.camera_id || jobIn.camera_id,
    source_file_key: j.source_file_key || jobIn.source_file_key,
    status: j.status || 'queued',
    progress: j.progress || 0,
    total_frames: j.total_frames || 10000,
    processed_frames: j.processed_frames || 0,
    detected_tracks: j.detected_tracks || 0,
    created_at: j.created_at || new Date().toISOString(),
  };
}
