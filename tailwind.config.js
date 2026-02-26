/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Pedestrian demand category colors
        'demand-very-high': '#b2182b',
        'demand-high': '#ef8a62',
        'demand-medium': '#fddbc7',
        'demand-low': '#d9d9d9',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
