/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{vue,js,ts,jsx,tsx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {},
  },
  plugins: [],
  // We use CSS variables for theming, so disable Tailwind's default colors
  // to avoid conflicts. Our style.css defines the design tokens.
  corePlugins: {
    preflight: false,
  },
}
