import React from 'react';

interface TelemetryBadgeProps {
  label: string;
  variant?: 'default' | 'saffron' | 'crimson' | 'emerald' | 'navy' | 'cobalt';
  dot?: boolean;
  pulse?: boolean;
  className?: string;
  title?: string;
}

export function TelemetryBadge({
  label,
  variant = 'default',
  dot = false,
  pulse = false,
  className = '',
  title,
}: TelemetryBadgeProps) {
  const styles = {
    default: 'bg-tint text-slate-700 border-border-warm',
    saffron: 'bg-saffron-50 text-saffron-700 border-saffron-600/30',
    crimson: 'bg-crimson-50 text-crimson-700 border-crimson-700/30',
    emerald: 'bg-emerald-50 text-emerald-700 border-emerald-700/30',
    navy: 'bg-navy-950 text-porcelain border-navy-800',
    cobalt: 'bg-cobalt-50 text-cobalt-600 border-cobalt-600/30',
  };

  const dotColors = {
    default: 'bg-slate-400',
    saffron: 'bg-saffron-600',
    crimson: 'bg-crimson-700',
    emerald: 'bg-emerald-600',
    navy: 'bg-white',
    cobalt: 'bg-cobalt-600',
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-[3px] border font-mono text-xs font-semibold uppercase tracking-wider tabular-nums ${styles[variant]} ${className}`}
      title={title}
    >
      {dot && (
        <span
          className={`w-1.5 h-1.5 rounded-full ${dotColors[variant]} ${
            pulse ? 'animate-ping' : ''
          }`}
        />
      )}
      <span>{label}</span>
    </span>
  );
}
