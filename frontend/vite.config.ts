import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [tailwindcss(), react()],
  server: {
    proxy: {
      '/api': process.env.WEATHER_API_URL ?? 'http://localhost:8000',
      '/nlu': process.env.WEATHER_NLU_URL ?? 'http://localhost:8002',
    },
  },
})
