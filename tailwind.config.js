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
        // Light theme colors
        'bg-primary': '#F8F9FA',
        'bg-surface': '#FFFFFF',
        'primary': '#4A90E2',
        'text-primary': '#212529',
        'text-secondary': '#6C757D',
        'border': '#DEE2E6',
        
        // Dark theme colors
        'dark-bg-primary': '#121212',
        'dark-bg-surface': '#1E1E1E',
        'dark-primary': '#58A6FF',
        'dark-text-primary': '#E0E0E0',
        'dark-text-secondary': '#8B949E',
        'dark-border': '#30363D',
        
        // Status colors
        'status-todo': '#6C757D',
        'status-progress': '#4A90E2',
        'status-completed': '#28A745',
        
        // Priority colors
        'priority-low': '#28A745',
        'priority-medium': '#FFC107',
        'priority-high': '#FF6B35',
        'priority-urgent': '#DC3545',
      },
      fontFamily: {
        'sans': ['Inter', 'system-ui', 'sans-serif'],
      },
      fontSize: {
        'xs': '0.75rem',
        'sm': '0.875rem',
        'base': '1rem',
        'lg': '1.125rem',
        'xl': '1.25rem',
        '2xl': '1.5rem',
        '3xl': '2rem',
        '4xl': '2.5rem',
      },
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
        '128': '32rem',
      },
      borderRadius: {
        'glass': '12px',
      },
      boxShadow: {
        'glass': '0 8px 32px 0 rgba(31, 38, 135, 0.37)',
        'card': '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
      },
      backdropBlur: {
        'glass': '10px',
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
  ],
}
