/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        navy: {
          50: "#f3f6fb",
          100: "#e4ebf5",
          200: "#c8d5e8",
          300: "#9db3d1",
          400: "#6d8ab5",
          500: "#45659b",
          600: "#33507f",
          700: "#273c63",
          800: "#1d2e4d",
          900: "#16233b",
          950: "#0b1424",
        },
      },
      fontFamily: {
        sans: [
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "Roboto",
          "Noto Sans",
          "Noto Sans Gujarati",
          "Noto Sans Devanagari",
          "Helvetica Neue",
          "Arial",
          "sans-serif",
        ],
      },
    },
  },
  plugins: [],
};
