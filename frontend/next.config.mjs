/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    const backendUrl = process.env.BACKEND_URL || 'http://127.0.0.1:8000';
    return [
      {
        source: '/api/v1/:path*',
        destination: `${backendUrl}/api/v1/:path*`,
      },
      {
        source: '/crops/:path*',
        destination: `${backendUrl}/crops/:path*`,
      },
      {
        source: '/backend-health',
        destination: `${backendUrl}/health`,
      },
      {
        source: '/backend-ready',
        destination: `${backendUrl}/ready`,
      },
    ];
  },
};

export default nextConfig;
