import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

const agentUrl = process.env.A2A_AGENT_URL ?? 'http://127.0.0.1:8100'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    proxy: { '/ag-ui': agentUrl },
  },
})
