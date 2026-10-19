/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        background: '#0B0F19',
        surface: {
          DEFAULT: '#0F172A',
          hover: '#141E33',
          elevated: '#17223B',
          border: '#1E293B',
          'border-subtle': '#334155',
        },
        security: {
          pass: {
            DEFAULT: '#10B981',
            muted: 'rgba(16, 185, 129, 0.1)',
            border: 'rgba(16, 185, 129, 0.25)',
          },
          fail: {
            DEFAULT: '#EF4444',
            muted: 'rgba(239, 68, 68, 0.1)',
            border: 'rgba(239, 68, 68, 0.25)',
          },
          error: {
            DEFAULT: '#F59E0B',
            muted: 'rgba(245, 158, 11, 0.1)',
            border: 'rgba(245, 158, 11, 0.25)',
          },
          notrun: {
            DEFAULT: '#64748B',
            muted: 'rgba(100, 116, 139, 0.1)',
            border: 'rgba(100, 116, 139, 0.25)',
          },
        },
        brand: {
          blue: '#3B82F6',
          indigo: '#6366F1',
          cyan: '#06B6D4',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
    },
  },
  plugins: [],
};
