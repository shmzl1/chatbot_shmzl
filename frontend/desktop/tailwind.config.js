/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      boxShadow: {
        paper: "0 18px 50px rgba(89, 76, 54, 0.12)",
        soft: "0 10px 30px rgba(51, 65, 85, 0.08)",
      },
      fontFamily: {
        sans: ["Inter", "Microsoft YaHei", "PingFang SC", "system-ui", "sans-serif"],
        serif: ["Georgia", "Source Han Serif SC", "SimSun", "serif"],
      },
    },
  },
  plugins: [],
};
