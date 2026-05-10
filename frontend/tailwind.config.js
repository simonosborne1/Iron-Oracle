/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          DEFAULT: "#f97316",  // orange-500 — heavy equipment aesthetic
          dark: "#ea580c",
        },
      },
    },
  },
  plugins: [],
};
