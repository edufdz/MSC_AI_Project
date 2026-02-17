/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: '#0A0A0A',
        'bg-card': '#161616',
        'bg-card-hover': '#1E1E1E',
        'bg-surface': '#0F0F0F',
        accent: '#D7D7D2',
        'accent-dim': '#B9B9B6',
        border: '#2A2A2A',
        'border-light': '#383838',
        'text-primary': '#F5F5F2',
        'text-dim': '#B9B9B6',
        'text-muted': '#7A7A78',
        graphite: '#2A2A2A',
        pearl: '#F5F5F2',
        smoke: '#B9B9B6',
        platinum: '#D7D7D2',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'Cascadia Code', 'monospace'],
      },
    },
  },
  plugins: [],
}
