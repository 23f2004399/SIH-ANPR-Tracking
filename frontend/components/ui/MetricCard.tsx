import React from 'react';
import { LucideIcon } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string | number;
  unit?: string;
  subtitle?: string;
  delta?: {
    value: string;
    isPositive?: boolean;
    label?: string;
  };
  icon?: LucideIcon;
  variant?: 'default' | 'alert' | 'clearance' | 'saffron';
  className?: string;
}

export function MetricCard({
  title,
  value,
  unit,
  subtitle,
  delta,
  icon: Icon,
  variant = 'default',
  className = '',
}: MetricCardProps) {
  const borderVariants = {
    default: 'border-border-warm',
    alert: 'border-crimson-700/40 bg-crimson-50/20',
    clearance: 'border-emerald-700/30 bg-emerald-50/20',
    saffron: 'border-saffron-600/40 bg-saffron-50/20',
  };

  return (
    <div
      className={`bg-surface border rounded-[4px] p-4 shadow-gov-sm flex flex-col justify-between ${borderVariants[variant]} ${className}`}
    >
      <div className="flex items-start justify-between gap-2">
        <span className="font-heading uppercase tracking-wider text-xs font-semibold text-slate-500">
          {title}
        </span>
        {Icon && <Icon className="w-4 h-4 text-slate-400 shrink-0" />}
      </div>

      <div className="mt-2 flex items-baseline gap-1.5">
        <span className="font-mono text-2xl font-bold tracking-tight text-navy-950 tabular-nums">
          {value}
        </span>
        {unit && (
          <span className="font-mono text-xs uppercase font-medium text-slate-500">
            {unit}
          </span>
        )}
      </div>

      {(subtitle || delta) && (
        <div className="mt-2.5 pt-2 border-t border-border-subtle flex items-center justify-between text-xs">
          {subtitle && (
            <span className="text-slate-500 text-[11px] truncate">{subtitle}</span>
          )}
          {delta && (
            <span
              className={`font-mono font-medium text-[11px] ml-auto px-1.5 py-0.5 rounded-[2px] tabular-nums ${
                delta.isPositive
                  ? 'bg-emerald-50 text-emerald-700'
                  : 'bg-crimson-50 text-crimson-700'
              }`}
            >
              {delta.value}
            </span>
          )}
        </div>
      )}
    </div>
  );
}
