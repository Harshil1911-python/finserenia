/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{ts,tsx,js,jsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // Serenia primary purple
        primary: {
          50: "#F0EEFF",
          100: "#E0DDFF",
          200: "#C4BDFF",
          300: "#A29BFE",
          400: "#8A7EFD",
          500: "#6C5CE7",   // main
          600: "#5A4BD1",
          700: "#4838B8",
          800: "#37299A",
          900: "#261D7B",
        },
        // Serenia teal
        teal: {
          50: "#E0FAF5",
          100: "#B2F5E8",
          200: "#76EDD4",
          300: "#38E0BE",
          400: "#00D2A7",
          500: "#00B894",   // main
          600: "#009A7C",
          700: "#007B63",
          800: "#005D4B",
          900: "#003D31",
        },
        // Status colors
        success: "#00B894",
        warning: "#FDCB6E",
        danger: "#D63031",
        info: "#74B9FF",
        // Neutral
        surface: {
          50: "#FAFAFA",
          100: "#F5F5F7",
          200: "#E9EAEF",
          300: "#D1D3DE",
          dark: {
            DEFAULT: "#1A1D24",
            elevated: "#22252E",
            border: "#2D3040",
          }
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
        display: ["Plus Jakarta Sans", "Inter", "sans-serif"],
      },
      fontSize: {
        "2xs": ["10px", "14px"],
        xs: ["12px", "16px"],
        sm: ["13px", "18px"],
        base: ["14px", "20px"],
        md: ["15px", "22px"],
        lg: ["16px", "24px"],
        xl: ["18px", "28px"],
        "2xl": ["20px", "30px"],
        "3xl": ["24px", "32px"],
        "4xl": ["30px", "38px"],
        "5xl": ["36px", "44px"],
      },
      boxShadow: {
        card: "0 1px 3px 0 rgba(0,0,0,0.06), 0 1px 2px 0 rgba(0,0,0,0.04)",
        "card-hover": "0 4px 12px 0 rgba(108,92,231,0.12), 0 1px 3px 0 rgba(0,0,0,0.06)",
        modal: "0 20px 60px 0 rgba(0,0,0,0.15), 0 4px 16px 0 rgba(0,0,0,0.08)",
        sidebar: "4px 0 24px 0 rgba(0,0,0,0.06)",
      },
      borderRadius: {
        sm: "6px",
        DEFAULT: "10px",
        md: "12px",
        lg: "16px",
        xl: "20px",
        "2xl": "24px",
      },
      animation: {
        "fade-in": "fadeIn 0.2s ease-out",
        "slide-up": "slideUp 0.25s ease-out",
        "slide-down": "slideDown 0.2s ease-out",
        "scale-in": "scaleIn 0.15s ease-out",
        shimmer: "shimmer 1.5s infinite",
        pulse: "pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
      },
      keyframes: {
        fadeIn: { from: { opacity: 0 }, to: { opacity: 1 } },
        slideUp: { from: { opacity: 0, transform: "translateY(8px)" }, to: { opacity: 1, transform: "translateY(0)" } },
        slideDown: { from: { opacity: 0, transform: "translateY(-8px)" }, to: { opacity: 1, transform: "translateY(0)" } },
        scaleIn: { from: { opacity: 0, transform: "scale(0.95)" }, to: { opacity: 1, transform: "scale(1)" } },
        shimmer: { "0%": { backgroundPosition: "-1000px 0" }, "100%": { backgroundPosition: "1000px 0" } },
      },
      spacing: {
        "sidebar": "256px",
        "sidebar-collapsed": "64px",
        "topbar": "60px",
      }
    },
  },
  plugins: [],
};
