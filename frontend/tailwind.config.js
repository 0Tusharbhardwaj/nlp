/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        cyber: {
          bg: '#080d1a',
          card: '#0f172a',
          cardHover: '#1e293b',
          border: '#1e293b',
          borderFocus: '#38bdf8',
          accent: '#38bdf8',
          accentGlow: 'rgba(56, 189, 248, 0.15)',
          safe: '#10b981',
          safeGlow: 'rgba(16, 185, 129, 0.2)',
          vuln: '#ef4444',
          vulnGlow: 'rgba(239, 68, 68, 0.2)',
          warn: '#f59e0b',
          muted: '#94a3b8',
        }
      },
      fontFamily: {
        mono: ['"Fira Code"', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'monospace'],
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
      },
      boxShadow: {
        'glow-cyan': '0 0 20px -5px rgba(56, 189, 248, 0.3)',
        'glow-vuln': '0 0 25px -5px rgba(239, 68, 68, 0.4)',
        'glow-safe': '0 0 25px -5px rgba(16, 185, 129, 0.4)',
      }
    },
  },
  plugins: [],
}
