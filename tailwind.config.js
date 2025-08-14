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
        // Enhanced light theme with sophisticated gradients
        'bg-primary': '#F8FAFC',
        'bg-surface': '#FFFFFF',
        'primary': {
          DEFAULT: '#4A90E2',
          50: '#EFF6FF',
          100: '#DBEAFE',
          200: '#BFDBFE',
          300: '#93C5FD',
          400: '#60A5FA',
          500: '#4A90E2',
          600: '#2563EB',
          700: '#1D4ED8',
          800: '#1E40AF',
          900: '#1E3A8A',
        },
        'text-primary': '#1F2937',
        'text-secondary': '#6B7280',
        'border': '#E5E7EB',

        // Enhanced dark theme
        'dark-bg-primary': '#0F0F23',
        'dark-bg-surface': '#1A1B3A',
        'dark-primary': {
          DEFAULT: '#58A6FF',
          50: '#F0F9FF',
          100: '#E0F2FE',
          200: '#BAE6FD',
          300: '#7DD3FC',
          400: '#38BDF8',
          500: '#58A6FF',
          600: '#0EA5E9',
          700: '#0284C7',
          800: '#0369A1',
          900: '#0C4A6E',
        },
        'dark-text-primary': '#F3F4F6',
        'dark-text-secondary': '#9CA3AF',
        'dark-border': '#374151',

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
