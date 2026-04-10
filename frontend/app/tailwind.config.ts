import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Tu peux ajouter des couleurs personnalisées ici si besoin
      },
    },
  },
  plugins: [],
  darkMode: 'class', // Permet de forcer le dark mode plus tard
};
export default config;