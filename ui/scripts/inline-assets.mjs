import { readFile, writeFile } from 'node:fs/promises'
import { basename, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const scriptPath = fileURLToPath(import.meta.url)
const distDir = join(scriptPath, '..', '..', 'dist')
const htmlPath = join(distDir, 'index.html')
let html = await readFile(htmlPath, 'utf8')

async function inlineAsset(path, tagName) {
  const filename = basename(new URL(path, 'http://vite.local').pathname)
  const asset = await readFile(join(distDir, 'assets', filename), 'utf8')
  if (tagName === 'script') {
    return `<script type="module">${asset.replace(/<\/script/gi, '<\\/script')}</script>`
  }
  return `<style>${asset.replace(/<\/style/gi, '<\\/style')}</style>`
}

const jsMatches = [...html.matchAll(/<script\b[^>]*\bsrc="([^"]+)"[^>]*>\s*<\/script>/g)]
const cssMatches = [...html.matchAll(/<link\b[^>]*\bhref="([^"]+\.css)"[^>]*\/?\s*>/g)]
if (jsMatches.length !== 1) throw new Error(`Expected one Vite entry script, found ${jsMatches.length}`)

for (const match of cssMatches) {
  const asset = await inlineAsset(match[1], 'style')
  html = html.replace(match[0], () => asset)
}
for (const match of jsMatches) {
  const asset = await inlineAsset(match[1], 'script')
  html = html.replace(match[0], () => asset)
}

if (/<script\b[^>]*\bsrc="\/?assets\/|<link\b[^>]*\bhref="\/?assets\//.test(html)) {
  throw new Error('Vite build still references external assets; MCP App must be self-contained.')
}

await writeFile(htmlPath, html)
console.log(`Embedded React MCP App assets in ${htmlPath}`)
