/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ['class'],
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        border: 'hsl(var(--border))', input: 'hsl(var(--input))', ring: 'hsl(var(--ring))',
        background: 'hsl(var(--background))', foreground: 'hsl(var(--foreground))',
        primary: { DEFAULT: 'hsl(var(--primary))', foreground: 'hsl(var(--primary-foreground))' },
        secondary: { DEFAULT: 'hsl(var(--secondary))', foreground: 'hsl(var(--secondary-foreground))' },
        destructive: { DEFAULT: 'hsl(var(--destructive))', foreground: 'hsl(var(--destructive-foreground))' },
        muted: { DEFAULT: 'hsl(var(--muted))', foreground: 'hsl(var(--muted-foreground))' },
        accent: { DEFAULT: 'hsl(var(--accent))', foreground: 'hsl(var(--accent-foreground))' },
        card: { DEFAULT: 'hsl(var(--card))', foreground: 'hsl(var(--card-foreground))' },
      },
      borderRadius: { lg: 'var(--radius)', md: 'calc(var(--radius) - 2px)', sm: 'calc(var(--radius) - 4px)' },
      keyframes: {
        'fade-in':   { from: { opacity: '0', transform: 'translateY(6px)' }, to: { opacity: '1', transform: 'translateY(0)' } },
        'progress':  { from: { width: '0%' }, to: { width: 'var(--progress-width)' } },
        'shake':     { '0%,100%': { transform: 'translateX(0)' }, '15%': { transform: 'translateX(-8px)' }, '30%': { transform: 'translateX(7px)' }, '45%': { transform: 'translateX(-6px)' }, '60%': { transform: 'translateX(5px)' }, '75%': { transform: 'translateX(-3px)' }, '90%': { transform: 'translateX(2px)' } },
        'slide-up':  { from: { opacity: '0', transform: 'translateY(16px)' }, to: { opacity: '1', transform: 'translateY(0)' } },
        'scale-in':  { from: { opacity: '0', transform: 'scale(0.7)' }, to: { opacity: '1', transform: 'scale(1)' } },
      },
      animation: {
        'fade-in':  'fade-in 0.25s ease-out',
        'progress': 'progress 0.8s ease-out forwards',
        'shake':    'shake 0.5s cubic-bezier(.36,.07,.19,.97) both',
        'slide-up': 'slide-up 0.25s ease-out',
        'scale-in': 'scale-in 0.4s cubic-bezier(0.34,1.56,0.64,1)',
      },
    },
  },
  plugins: [],
}
