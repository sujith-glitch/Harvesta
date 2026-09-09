/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Harvesta-inspired palette
        cream: {
          50: '#FBFAF5',
          100: '#F5F5F0',
          200: '#EFEDE6',
          300: '#E5E2D6',
        },
        ink: {
          900: '#1A1D21',
          800: '#21252B',
          700: '#2C3138',
          600: '#3F464F',
          500: '#5C6570',
          400: '#8590A0',
          300: '#A8B2BD',
        },
        lime: {
          DEFAULT: '#D4E157',
          soft: '#E6EBA0',
          deep: '#A6BC12',
          50: '#F9FBE0',
          100: '#F0F4C3',
          200: '#E6EBA0',
          300: '#D4E157',
          400: '#C5D524',
          500: '#A6BC12',
        },
        leaf: {
          50: '#F1F8E9',
          100: '#DCEDC8',
          200: '#AED581',
          300: '#7CB342',
          400: '#558B2F',
          500: '#33691E',
          600: '#1B5E20',
        },
        amber: {
          soft: '#FFEB3B',
          deep: '#F9A825',
        },
        terracotta: '#E07856',
      },
      fontFamily: {
        sans: ['Inter', 'Plus Jakarta Sans', 'system-ui', '-apple-system', 'sans-serif'],
        display: ['Plus Jakarta Sans', 'Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'monospace'],
      },
      boxShadow: {
        'soft': '0 4px 20px rgba(15, 23, 42, 0.06), 0 1px 3px rgba(15, 23, 42, 0.04)',
        'soft-lg': '0 12px 40px rgba(15, 23, 42, 0.08), 0 4px 12px rgba(15, 23, 42, 0.04)',
        'soft-xl': '0 24px 60px rgba(15, 23, 42, 0.10), 0 8px 24px rgba(15, 23, 42, 0.05)',
        'glass': '0 8px 32px rgba(15, 23, 42, 0.08), 0 1px 0 rgba(255,255,255,0.6) inset',
        'lift': '0 12px 32px rgba(15, 23, 42, 0.12), 0 2px 8px rgba(15, 23, 42, 0.06)',
      },
      borderRadius: {
        'xl': '14px',
        '2xl': '18px',
        '3xl': '24px',
      },
      backdropBlur: {
        xs: '2px',
      },
      keyframes: {
        'fade-up': {
          '0%': { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'pulse-soft': {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.6' },
        },
        'spin-slow': {
          '0%': { transform: 'rotate(0deg)' },
          '100%': { transform: 'rotate(360deg)' },
        },
      },
      animation: {
        'fade-up': 'fade-up 0.4s ease-out both',
        'pulse-soft': 'pulse-soft 2s ease-in-out infinite',
        'spin-slow': 'spin-slow 1.4s linear infinite',
      },
    },
  },
  plugins: [],
}
