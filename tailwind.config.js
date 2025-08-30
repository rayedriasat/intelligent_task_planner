/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',
    './planner/templates/**/*.html',
    './static/js/**/*.js',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Enhanced light theme with better contrast for animated background
        'bg-primary': 'transparent',
        'bg-surface': 'rgba(255, 255, 255, 0.95)',
        'primary': {
          DEFAULT: '#2563EB',
          50: '#EFF6FF',
          100: '#DBEAFE',
          200: '#BFDBFE',
          300: '#93C5FD',
          400: '#60A5FA',
          500: '#2563EB',
          600: '#1D4ED8',
          700: '#1E40AF',
          800: '#1E3A8A',
          900: '#172554',
        },
        'text-primary': '#111827',
        'text-secondary': '#4B5563',
        'border': '#D1D5DB',

        // Enhanced dark theme with better contrast for animated background
        'dark-bg-primary': 'transparent',
        'dark-bg-surface': 'rgba(15, 15, 35, 0.95)',
        'dark-primary': {
          DEFAULT: '#60A5FA',
          50: '#F0F9FF',
          100: '#E0F2FE',
          200: '#BAE6FD',
          300: '#7DD3FC',
          400: '#38BDF8',
          500: '#60A5FA',
          600: '#2563EB',
          700: '#1D4ED8',
          800: '#1E40AF',
          900: '#1E3A8A',
        },
        'dark-text-primary': '#F9FAFB',
        'dark-text-secondary': '#D1D5DB',
        'dark-border': '#4B5563',

        // Enhanced status colors
        'status-todo': '#64748B',
        'status-progress': '#3B82F6',
        'status-completed': '#10B981',

        // Enhanced priority colors
        'priority-low': '#10B981',
        'priority-medium': '#F59E0B',
        'priority-high': '#F97316',
        'priority-urgent': '#EF4444',
      },
      fontFamily: {
        'sans': ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      fontSize: {
        'xs': ['0.75rem', { lineHeight: '1rem' }],
        'sm': ['0.875rem', { lineHeight: '1.25rem' }],
        'base': ['1rem', { lineHeight: '1.5rem' }],
        'lg': ['1.125rem', { lineHeight: '1.75rem' }],
        'xl': ['1.25rem', { lineHeight: '1.75rem' }],
        '2xl': ['1.5rem', { lineHeight: '2rem' }],
        '3xl': ['1.875rem', { lineHeight: '2.25rem' }],
        '4xl': ['2.25rem', { lineHeight: '2.5rem' }],
      },
      spacing: {
        '18': '4.5rem',
        '22': '5.5rem',
        '88': '22rem',
        '128': '32rem',
      },
      borderRadius: {
        'glass': '20px',
        'xl': '12px',
        '2xl': '16px',
        '3xl': '24px',
      },
      boxShadow: {
        'glass': '0 25px 50px -12px rgba(0, 0, 0, 0.25), 0 8px 32px rgba(31, 38, 135, 0.2)',
        'card': '0 20px 40px -8px rgba(0, 0, 0, 0.12), 0 8px 16px -4px rgba(0, 0, 0, 0.08)',
        'elegant': '0 30px 60px -12px rgba(0, 0, 0, 0.15), 0 12px 24px -6px rgba(0, 0, 0, 0.1)',
        'float': '0 35px 70px -15px rgba(0, 0, 0, 0.2), 0 15px 30px -8px rgba(0, 0, 0, 0.12)',
      },
      backdropBlur: {
        'glass': '20px',
      },
      animation: {
        'fade-in': 'fadeIn 0.6s ease-in-out',
        'slide-up': 'slideUp 0.4s ease-out',
        'bounce-gentle': 'bounceGentle 0.8s ease-in-out',
        'gradient-shift': 'gradientShift 15s ease-in-out infinite',
        'modal-slide': 'modalSlideIn 0.5s cubic-bezier(0.34, 1.56, 0.64, 1)',
        'notification-slide': 'notificationSlide 0.5s cubic-bezier(0.68, -0.55, 0.265, 1.55)',
        'urgent-glow': 'urgentGlow 2s ease-in-out infinite',
        'page-enter': 'pageEnter 0.6s cubic-bezier(0.4, 0, 0.2, 1)',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        bounceGentle: {
          '0%, 20%, 50%, 80%, 100%': { transform: 'translateY(0)' },
          '40%': { transform: 'translateY(-6px)' },
          '60%': { transform: 'translateY(-3px)' },
        },
        gradientShift: {
          '0%, 100%': { opacity: '1', transform: 'scale(1)' },
          '50%': { opacity: '0.8', transform: 'scale(1.05)' },
        },
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
  ],
}
