import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(), 
    VitePWA ({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.ico'],
      manifest: {
        name: 'Blagoda',
        short_name: 'Blagoda',
        description: 'Веб-приложение для прогнозирования спроса',
        theme_color: '#7b1e1e',
        background_color: '#ffffff',
        display: 'standalone',
        start_url: '/',
        icons: [
          {
            src: '/icon-192.png',
            sizes: '192x192',
            type: 'image/png'
          },
          {
            src: '/icon-512.png',
            sizes: '512x512',
            type: 'image/png'
          }
        ]
      }
    })
  ],

  server: {
    host: '0.0.0.0',
    port: 3000,
    allowedHosts: true,
    watch: {
      usePolling: true,
      interval: 300,
    },
  },
})