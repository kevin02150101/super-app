/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['../templates/**/*.html'],
  theme: {
    extend: {
      fontFamily: {
        display: ["'D-DIN'", "'D-DIN PRO'", 'Inter', 'system-ui', 'sans-serif'],
        sans:    ["'D-DIN'", 'Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      colors: {
        brand: {
          blue:   '#1E96E5',
          cyan:   '#3BCFFF',
          navy:   '#0F1A2F',
          green:  '#6ECC71',
          orange: '#FF8020',
          red:    '#FF4040',
          white:  '#F5F7FA',
        },
        ink:   { DEFAULT: '#F5F7FA', soft: 'rgba(245,247,250,0.70)', mute: 'rgba(245,247,250,0.45)' },
        paper: { DEFAULT: '#0F1A2F', soft: '#152441', tint: '#1B2D52' },
        line:  { DEFAULT: 'rgba(59,207,255,0.16)', soft: 'rgba(59,207,255,0.08)' },
      },
      letterSpacing: { wider2: '0.16em' },
    },
  },
  plugins: [],
};
