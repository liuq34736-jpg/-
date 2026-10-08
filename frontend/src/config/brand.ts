import brand from './brand.json'

export const BRAND = Object.freeze(brand)
export const BRAND_TITLE = `${BRAND.name} · ${BRAND.tagline}`

function hexToHsl(hex: string): string {
  const values = hex.slice(1).match(/.{2}/g)!.map(value => parseInt(value, 16) / 255)
  const [red, green, blue] = values
  const max = Math.max(...values)
  const min = Math.min(...values)
  const delta = max - min
  const lightness = (max + min) / 2
  const saturation = delta === 0 ? 0 : delta / (1 - Math.abs(2 * lightness - 1))
  let hue = 0
  if (delta !== 0) {
    if (max === red) hue = ((green - blue) / delta) % 6
    else if (max === green) hue = (blue - red) / delta + 2
    else hue = (red - green) / delta + 4
    hue *= 60
    if (hue < 0) hue += 360
  }
  return `${hue.toFixed(2)} ${(saturation * 100).toFixed(2)}% ${(lightness * 100).toFixed(2)}%`
}

// Public brand data only. No environment variables or server configuration.
export function applyBrand(): void {
  document.title = BRAND_TITLE
  const style = document.documentElement.style
  for (const [key, value] of Object.entries(BRAND.colors)) {
    style.setProperty(`--brand-${key}`, value)
  }
  style.setProperty('--primary', hexToHsl(BRAND.colors.primary))
  style.setProperty('--background', hexToHsl(BRAND.colors.background))
}
