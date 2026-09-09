/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        patino: {
          navy: '#0F172A',
          'navy-light': '#1E293B',
          cobalt: '#2563EB',
          'cobalt-hover': '#1D4ED8',
          gold: '#D97706',
          'gold-light': '#F59E0B',
          'gold-subtle': '#FEF3C7',
          emerald: '#059669',
          'emerald-subtle': '#ECFDF5',
          crimson: '#DC2626',
          'crimson-subtle': '#FEF2F2',
          slate: '#64748B',
          'slate-subtle': '#F1F5F9',
          bg: '#F8FAFC',
        },
      },
      fontFamily: {
        sans: ['Inter', 'Public Sans', 'Roboto', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        xs: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
        card: '0 1px 3px 0 rgba(15, 23, 42, 0.06), 0 1px 2px -1px rgba(15, 23, 42, 0.06)',
        'card-hover': '0 10px 15px -3px rgba(15, 23, 42, 0.08), 0 4px 6px -4px rgba(15, 23, 42, 0.04)',
      },
      backdropBlur: {
        xs: '2px',
      },
    },
  },
  plugins: [],
}
