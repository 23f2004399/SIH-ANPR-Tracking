import type { Metadata } from 'next';
import './globals.css';
import { Header } from '@/components/layout/Header';
import { SubNav } from '@/components/layout/SubNav';

export const metadata: Metadata = {
  title: 'ZyroTrace AI — Sovereign Multi-Camera ANPR Telemetry & Traffic Intelligence',
  description:
    'Defense-grade multi-camera ANPR tracking and urban traffic intelligence platform developed for Smart India Hackathon (BEL & MoRTH).',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700;800&family=Plus+Jakarta+Sans:wght@400;500;600;700&family=Rajdhani:wght@500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="min-h-screen bg-porcelain text-slate-700 flex flex-col font-sans">
        <Header />
        <SubNav />
        <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 space-y-5">
          {children}
        </main>
      </body>
    </html>
  );
}
