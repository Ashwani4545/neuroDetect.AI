/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        clinical: {
          bg: '#f7f9fb',
          panel: '#ffffff',
          border: '#e2e8f0',
          primary: '#0f4c81',
          primaryDark: '#0b3a63',
          accent: '#2f9e8f',
          warn: '#b45309',
          danger: '#b91c1c',
          text: '#1f2937',
          textMuted: '#5b6472',
        },
      },
    },
  },
  plugins: [],
}
