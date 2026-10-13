/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        clinical: {
          bg: '#F7F5F0',
          panel: '#FFFFFF',
          border: '#E4E0D6',
          borderLight: '#F0EDE5',
          primary: '#13293D',
          primaryDark: '#0A1C30',
          accent: '#2F7B6B',
          warn: '#B45309',
          warnBg: '#FBF1DF',
          warnBorder: '#EBD9AE',
          warnText: '#7A5A1E',
          danger: '#B42318',
          text: '#1C1B19',
          textMuted: '#6B6355',
          textFaint: '#9A9382',
        },
      },
      fontFamily: {
        serif: ['"Source Serif 4"', 'serif'],
        sans: ['"IBM Plex Sans"', 'sans-serif'],
        mono: ['"IBM Plex Mono"', 'monospace'],
      },
    },
  },
  plugins: [],
}
