/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'aws-nav': '#232f3e',
        'aws-nav-hover': '#1b2631',
        'aws-nav-active': '#2a3f54',
        'aws-orange': '#ff9900',
        'aws-orange-hover': '#ec7211',
        'aws-dark': '#16191f',
        'aws-squid-ink': '#232f3e',
        'aws-border': '#d5dbdb',
        'aws-border-secondary': '#eaeded',
        'aws-text': '#16191f',
        'aws-text-secondary': '#545b64',
        'aws-text-tertiary': '#687078',
        'aws-text-link': '#0073bb',
        'aws-bg-primary': '#ffffff',
        'aws-bg-secondary': '#fafafa',
        'aws-bg-tertiary': '#f2f3f3',
        'aws-success': '#1d8102',
        'aws-error': '#d13212',
        'aws-warning': '#ff9900',
        'aws-info': '#0073bb',
      },
      fontFamily: {
        'aws': [
          '"Amazon Ember"',
          'system-ui',
          '-apple-system',
          '"Segoe UI"',
          'Roboto',
          '"Helvetica Neue"',
          'Arial',
          'sans-serif',
        ],
      },
      spacing: {
        'aws-xs': '4px',
        'aws-sm': '8px',
        'aws-md': '16px',
        'aws-lg': '24px',
        'aws-xl': '32px',
      },
      borderRadius: {
        'aws-sm': '2px',
        'aws-md': '4px',
        'aws-lg': '8px',
      },
      boxShadow: {
        'aws-sm': '0 1px 1px 0 rgba(0, 28, 36, 0.3), 1px 1px 1px 0 rgba(0, 28, 36, 0.15)',
        'aws-md': '0 1px 4px -2px rgba(0, 28, 36, 0.5)',
      },
      fontSize: {
        'aws-heading': ['18px', { lineHeight: '22px', fontWeight: '700' }],
        'aws-body': ['14px', { lineHeight: '20px' }],
        'aws-small': ['12px', { lineHeight: '16px' }],
      },
    },
  },
  plugins: [],
}
