import axios, { AxiosInstance } from 'axios';

// When running in the browser, relative URLs like '/api/v1/...' are automatically
// proxied by Next.js rewrites in next.config.mjs to http://127.0.0.1:8000.
// If NEXT_PUBLIC_API_URL is explicitly set (e.g. deployed cloud backend), it uses that.
const getBaseUrl = (): string => {
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL;
  }
  if (typeof window !== 'undefined') {
    return ''; // Relative to origin in browser, proxied via Next rewrites
  }
  return process.env.BACKEND_INTERNAL_URL || 'http://127.0.0.1:8000';
};

export const apiClient: AxiosInstance = axios.create({
  baseURL: getBaseUrl(),
  timeout: 6000,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
});

export async function checkBackendHealth(): Promise<boolean> {
  try {
    const res = await apiClient.get('/health');
    return res.status === 200;
  } catch {
    return false;
  }
}
