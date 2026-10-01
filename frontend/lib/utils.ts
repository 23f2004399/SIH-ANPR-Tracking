import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

/**
 * Normalizes Indian license plates by removing spaces, dots, dashes, and converting to uppercase.
 * Example: "dl-01 ab 1234" -> "DL01AB1234"
 */
export function normalizePlate(plate: string): string {
  return plate.replace(/[\s\-_.]/g, '').toUpperCase();
}

/**
 * Formats a raw plate into spaced segments for readability (e.g. DL 01 AB 1234)
 */
export function formatDisplayPlate(plate: string): string {
  const clean = normalizePlate(plate);
  if (clean.length === 10) {
    return `${clean.slice(0, 2)} ${clean.slice(2, 4)} ${clean.slice(4, 6)} ${clean.slice(6)}`;
  }
  return clean;
}

/**
 * Formats a Date or ISO timestamp into Indian Standard Time (IST) with seconds
 */
export function formatIST(isoDate?: string | Date): string {
  if (!isoDate) return '—';
  try {
    const d = typeof isoDate === 'string' ? new Date(isoDate) : isoDate;
    if (isNaN(d.getTime())) return String(isoDate);

    const istString = d.toLocaleString('en-IN', {
      timeZone: 'Asia/Kolkata',
      year: 'numeric',
      month: 'short',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    });
    return `${istString} IST`;
  } catch {
    return String(isoDate);
  }
}

/**
 * Formats time only in IST (HH:mm:ss)
 */
export function formatISTTime(isoDate?: string | Date): string {
  if (!isoDate) return '—';
  try {
    const d = typeof isoDate === 'string' ? new Date(isoDate) : isoDate;
    if (isNaN(d.getTime())) return String(isoDate);

    return d.toLocaleTimeString('en-IN', {
      timeZone: 'Asia/Kolkata',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    });
  } catch {
    return String(isoDate);
  }
}

/**
 * Formats speed with appropriate visual category
 */
export function getSpeedBadge(speedKmh?: number): {
  label: string;
  bg: string;
  text: string;
  border: string;
} {
  if (speedKmh === undefined || speedKmh === null) {
    return {
      label: 'N/A',
      bg: 'bg-porcelain',
      text: 'text-slate-500',
      border: 'border-border-warm',
    };
  }
  if (speedKmh > 80) {
    return {
      label: `${speedKmh} km/h`,
      bg: 'bg-crimson-50',
      text: 'text-crimson-700',
      border: 'border-crimson-700/30',
    };
  }
  if (speedKmh >= 50) {
    return {
      label: `${speedKmh} km/h`,
      bg: 'bg-saffron-50',
      text: 'text-saffron-700',
      border: 'border-saffron-600/30',
    };
  }
  return {
    label: `${speedKmh} km/h`,
    bg: 'bg-emerald-50',
    text: 'text-emerald-700',
    border: 'border-emerald-700/30',
  };
}

/**
 * Confidence score formatting and visual classification
 */
export function getConfidenceBadge(confidence: number): {
  label: string;
  pct: number;
  textColor: string;
  barColor: string;
} {
  const pct = Math.round(confidence <= 1 ? confidence * 100 : confidence);
  if (pct >= 90) {
    return {
      label: `${pct}%`,
      pct,
      textColor: 'text-emerald-700',
      barColor: 'bg-emerald-700',
    };
  }
  if (pct >= 75) {
    return {
      label: `${pct}%`,
      pct,
      textColor: 'text-saffron-700',
      barColor: 'bg-saffron-600',
    };
  }
  return {
    label: `${pct}%`,
    pct,
    textColor: 'text-crimson-700',
    barColor: 'bg-crimson-700',
  };
}

/**
 * Detect plate variant (private: white, commercial: yellow, EV: green)
 */
export function getPlateVariant(
  plate: string,
  vehicleType?: string
): 'private' | 'commercial' | 'ev' {
  const clean = normalizePlate(plate);
  // EV plates in India often have digits/letters or EV tag or green designation
  if (clean.includes('EV') || clean.endsWith('E')) {
    return 'ev';
  }
  // Commercial vehicles typically have T, Y, P, or freight designations, or vehicleType = truck/bus
  if (
    vehicleType === 'truck' ||
    vehicleType === 'bus' ||
    clean.includes('T') ||
    clean.includes('Z')
  ) {
    return 'commercial';
  }
  return 'private';
}
