import { readFileSync } from 'node:fs'
import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const cert = process.env.HARVESTA_HTTPS_CERT || env.HARVESTA_HTTPS_CERT
  const key = process.env.HARVESTA_HTTPS_KEY || env.HARVESTA_HTTPS_KEY
  if (Boolean(cert) !== Boolean(key)) throw new Error('Set both HARVESTA_HTTPS_CERT and HARVESTA_HTTPS_KEY.')
  return {
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    strictPort: true,
    allowedHosts: true,
    https: cert && key ? { cert: readFileSync(cert), key: readFileSync(key) } : undefined,
    proxy: {
      '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true },
    },
  },
  }
})
