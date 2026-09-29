import React from 'react';
import { formatDisplayPlate, getPlateVariant } from '@/lib/utils';

interface HsrpPlateProps {
  plateText: string;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'private' | 'commercial' | 'ev';
  vehicleType?: string;
  className?: string;
}

export function HsrpPlate({
  plateText,
  size = 'md',
  variant,
  vehicleType,
  className = '',
}: HsrpPlateProps) {
  const resolvedVariant = variant || getPlateVariant(plateText, vehicleType);
  const formattedText = formatDisplayPlate(plateText);

  const bgStyles = {
    private: 'bg-white text-slate-900 border-slate-700/80 shadow-inner',
    commercial: 'bg-[#FBBF24] text-slate-950 border-amber-600 shadow-inner',
    ev: 'bg-[#059669] text-white border-emerald-800 shadow-inner',
  };

  const sizeStyles = {
    sm: {
      container: 'h-6 text-xs border-[1.5px]',
      blueBand: 'px-1 py-0.5 text-[6px]',
      chakra: 'text-[6px]',
      ind: 'text-[7px]',
      text: 'px-2 tracking-wider text-[11px] font-bold',
    },
    md: {
      container: 'h-8 text-sm border-2',
      blueBand: 'px-1.5 py-0.5 text-[7px]',
      chakra: 'text-[8px]',
      ind: 'text-[8.5px]',
      text: 'px-2.5 tracking-widest text-sm font-extrabold',
    },
    lg: {
      container: 'h-10 text-base border-2',
      blueBand: 'px-2 py-0.5 text-[8px]',
      chakra: 'text-[9px]',
      ind: 'text-[10px]',
      text: 'px-3 tracking-widest text-base font-extrabold',
    },
  };

  const s = sizeStyles[size];

  return (
    <div
      className={`inline-flex items-stretch rounded-[3px] overflow-hidden font-mono select-none transition-transform ${bgStyles[resolvedVariant]} ${s.container} ${className}`}
      title={`Indian High Security Registration Plate (HSRP) — ${plateText}`}
    >
      {/* Sovereign Blue Strip (HSRP Emblem) */}
      <div className={`bg-[#003399] text-white flex flex-col items-center justify-between font-mono font-black ${s.blueBand}`}>
        <span className={`text-amber-300 leading-none ${s.chakra}`} aria-hidden="true">
          ☸
        </span>
        <span className={`tracking-tighter font-extrabold leading-none ${s.ind}`}>
          IND
        </span>
      </div>

      {/* Embossed Registration Text */}
      <div
        className={`flex items-center justify-center text-center uppercase tabular-nums font-mono ${s.text}`}
      >
        {formattedText}
      </div>
    </div>
  );
}
