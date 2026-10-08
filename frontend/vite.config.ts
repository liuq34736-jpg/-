import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import { readFileSync } from 'node:fs'
import { createHash } from 'node:crypto'

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
    headers: { 'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'no-referrer', 'X-Frame-Options': 'DENY' },
  },
  preview: { host: '127.0.0.1', port: 5173, strictPort: true, headers: { 'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'no-referrer', 'X-Frame-Options': 'DENY' } },
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
    {
      name: 'local-script-csp',
      transformIndexHtml: {
        order: 'post',
        handler(html) {
          const hashes = [...html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)]
            .filter(([, attributes, content]) => !/\bsrc\s*=/i.test(attributes) && content.trim())
            .map(([, , content]) => `'sha256-${createHash('sha256').update(content).digest('base64')}'`)
          return html.replace('__LOCAL_INLINE_SCRIPT_HASHES__', hashes.join(' '))
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
