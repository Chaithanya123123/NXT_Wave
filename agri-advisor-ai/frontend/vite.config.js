import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/ask': 'http://localhost:8000',
      '/transcribe': 'http://localhost:8000',
      '/tts': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
      '/kb': 'http://localhost:8000',
    },
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
})
