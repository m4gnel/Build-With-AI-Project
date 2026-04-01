/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    './pages/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './app/**/*.{ts,tsx}',
    './src/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        background: '#000000',
        foreground: '#ffffff',
        primary: {
          DEFAULT: '#00F5FF', // Cyan Accent
          foreground: '#000000',
        },
        secondary: {
          DEFAULT: '#8A2BE2', // Purple Accent
          foreground: '#ffffff',
        },
        accent: {
          DEFAULT: '#FF7A00', // Orange Accent
          foreground: '#ffffff',
        },
        muted: {
          DEFAULT: '#111111',
          foreground: '#a1a1aa'
        },
        glass: {
          DEFAULT: 'rgba(255, 255, 255, 0.03)',
          dark: 'rgba(0, 0, 0, 0.5)',
          border: 'rgba(255, 255, 255, 0.08)'
        }
      },
      fontFamily: {
        heading: ['Instrument Serif', 'serif'],
        sans: ['Barlow', 'sans-serif'],
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'hero-glow': 'radial-gradient(circle at top center, rgba(0, 245, 255, 0.15) 0%, transparent 60%)',
      },
      boxShadow: {
        'glass': '0 8px 32px 0 rgba(0, 0, 0, 0.37)',
        'glow': '0 0 20px 0 rgba(0, 245, 255, 0.2)',
      },
      animation: {
        'pulse-slow': 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'fade-in': 'fadeIn 0.8s ease-out forwards',
        'slide-up': 'slideUp 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        }
      }
    },
  },
  plugins: [],
}
