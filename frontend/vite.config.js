import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig(({ mode }) => ({
  plugins: [react()],
  server: {
    port: 3000,
    open: true,
    proxy: {
      '/api': {
        target: process.env.VITE_DEV_API_TARGET || 'http://127.0.0.1:8001',
        changeOrigin: true,
        secure: false,
      }
    }
  },
  esbuild: {
    // Debug logging includes locations and consultation details; keep it out
    // of production bundles (console.error/warn are kept).
    pure: mode === 'production' ? ['console.log', 'console.info', 'console.debug'] : [],
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom', 'styled-components', 'framer-motion', 'axios'],
        },
      },
    },
  },
}))
