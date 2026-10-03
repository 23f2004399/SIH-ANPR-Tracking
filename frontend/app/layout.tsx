import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'ZyroTrace AI · Surveillance & City Traffic Analytics',
  description: 'AI-Powered Vehicle Tracking, ANPR Re-ID, and Urban Congestion Intelligence',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Instrument+Sans:ital,wght@0,400..700;1,400..700&family=JetBrains+Mono:wght@400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="min-h-screen bg-[#F4F5F7] text-[#0F172A] antialiased" suppressHydrationWarning>
        {children}
      </body>
    </html>
  );
}
