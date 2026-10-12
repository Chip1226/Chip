import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        sand: {
          50: "#FBF9F5", // page background (off-white)
          100: "#F5F1EA",
          200: "#EAE3D6",
          300: "#D9CDB8",
        },
        ink: {
          DEFAULT: "#1F2326", // dark charcoal text
          soft: "#4A5157",
          muted: "#6E767D",
        },
        pool: {
          50: "#E8F4F8",
          100: "#C9E5EE",
          500: "#0A6E8C", // brand accent
          600: "#085C75",
          700: "#06485C",
        },
        sun: {
          DEFAULT: "#E0893B", // warm desert accent, used sparingly
          dark: "#A6531A", // darker version, readable as small text
        },
      },
      fontFamily: {
        display: ["var(--font-display)", "system-ui", "sans-serif"],
        sans: ["var(--font-body)", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
