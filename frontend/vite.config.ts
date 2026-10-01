import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: { proxy: { '/api': 'http://127.0.0.1:8766', '/health': 'http://127.0.0.1:8766' } },
  build: { outDir: '../norvald_lab/web', emptyOutDir: true, chunkSizeWarningLimit: 1500 },
});
