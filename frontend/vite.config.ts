import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import { readFileSync } from 'node:fs'

const brand = JSON.parse(readFileSync(path.resolve(__dirname, 'src/config/brand.json'), 'utf8'))
const escapeHtml = (value: string) => value.replace(/[&<>"']/g, char => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
}[char]!))

// https://vitejs.dev/config/
export default defineConfig({
  envPrefix: 'LOCAL_PREVIEW_PUBLIC_',
  server: {
    host: '127.0.0.1',
    port: 5173,
    strictPort: true,
    proxy: { '/api': { target: 'http://127.0.0.1:8765' } },
  },
  preview: { host: '127.0.0.1', port: 5173, strictPort: true },
  plugins: [
    react(),
    {
      name: 'public-brand-html',
      transformIndexHtml: {
        // Resolve the favicon before Vite rewrites paths on SPA deep links.
        order: 'pre',
        handler(html) {
          const replacements: Record<string, string> = {
            TITLE: `${brand.name} · ${brand.tagline}`,
            DESCRIPTION: brand.description,
            NAME: brand.name,
            PRIMARY: brand.colors.primary,
            FAVICON: brand.assets.favicon,
          }
          return html.replace(/__BRAND_(\w+)__/g, (placeholder, key: string) =>
            replacements[key] === undefined ? placeholder : escapeHtml(replacements[key]))
        },
      },
    },
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  }
})
