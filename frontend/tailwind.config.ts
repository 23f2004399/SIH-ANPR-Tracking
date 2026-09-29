import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        porcelain: '#FBFBFA',
        surface: '#FFFFFF',
        tint: '#F4F4F0',
        'border-warm': '#E5E2DC',
        'border-subtle': '#EEECE6',
        navy: {
          800: '#112240',
          900: '#0F1E36',
          950: '#0A192F',
        },
        slate: {
          400: '#94A3B8',
          500: '#64748B',
          700: '#334155',
        },
        saffron: {
          50: '#FFFBEB',
          600: '#D97706',
          700: '#EA580C',
        },
        emerald: {
          50: '#ECFDF5',
          600: '#059669',
          700: '#047857',
        },
        crimson: {
          50: '#FEF2F2',
          700: '#B91C1C',
        },
        cobalt: {
          50: '#EFF6FF',
          600: '#1D4ED8',
        },
      },
      fontFamily: {
        heading: ['var(--font-rajdhani)', 'Rajdhani', 'sans-serif'],
        sans: ['var(--font-jakarta)', 'Plus Jakarta Sans', 'sans-serif'],
        mono: ['var(--font-jetbrains)', 'JetBrains Mono', 'monospace'],
      },
      boxShadow: {
        'gov-sm': '0 1px 2px rgba(10, 25, 47, 0.05)',
        'gov-md': '0 4px 6px -1px rgba(10, 25, 47, 0.08), 0 2px 4px -2px rgba(10, 25, 47, 0.04)',
        'gov-lg': '0 10px 15px -3px rgba(10, 25, 47, 0.1), 0 4px 6px -4px rgba(10, 25, 47, 0.05)',
      },
    },
  },
  plugins: [],
};

export default config;
