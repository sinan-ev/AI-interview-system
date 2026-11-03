/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        background: {
          DEFAULT: '#0B0F19',
          secondary: '#0F172A',
        },
        card: {
          DEFAULT: '#111827',
          hover: '#172033',
        },
        primary: {
          DEFAULT: '#6366F1',
          hover: '#4F46E5',
          light: '#818CF8',
        },
        secondary: {
          DEFAULT: '#8B5CF6',
          hover: '#7C3AED',
          light: '#A78BFA',
        },
        accent: {
          DEFAULT: '#06B6D4',
          hover: '#0891B2',
          light: '#22D3EE',
        },
        success: {
          DEFAULT: '#22C55E',
          hover: '#16A34A',
          light: '#4ADE80',
        },
        warning: {
          DEFAULT: '#F59E0B',
          hover: '#D97706',
          light: '#FBBF24',
        },
        error: {
          DEFAULT: '#EF4444',
          hover: '#DC2626',
          light: '#F87171',
        },
        border: {
          DEFAULT: '#1E293B',
          light: '#334155',
        },
        text: {
          primary: '#F8FAFC',
          secondary: '#94A3B8',
          muted: '#64748B',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      boxShadow: {
        card: '0 4px 20px -2px rgba(0, 0, 0, 0.5)',
        glow: '0 0 25px -5px rgba(99, 102, 241, 0.25)',
      },
    },
  },
  plugins: [],
}
