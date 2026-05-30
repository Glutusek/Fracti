import type { NominatimResult } from '../types/trip'

const BASE = 'https://nominatim.openstreetmap.org'
const cache = new Map<string, NominatimResult[]>()
const MAX_CACHE = 50

export function formatAddressLabel(
  addr: Record<string, string> | undefined,
  fallback: string,
): string {
  if (!addr) return fallback
  const road = addr.road || addr.pedestrian || addr.footway || addr.cycleway
  const num = addr.house_number
  const place =
    addr.city || addr.town || addr.village || addr.hamlet || addr.suburb || addr.county
  if (road && num) return place ? `${road} ${num}, ${place}` : `${road} ${num}`
  if (road) return place ? `${road}, ${place}` : road
  if (place) return place
  return fallback
}

export async function searchAddress(
  q: string,
  signal?: AbortSignal,
): Promise<NominatimResult[]> {
  if (q.length < 3) return []
  if (cache.has(q)) return cache.get(q)!

  const url =
    `${BASE}/search?format=json&q=${encodeURIComponent(q)}` +
    `&limit=8&addressdetails=1&accept-language=pl`

  const res = await fetch(url, { signal })
  if (!res.ok) throw new Error(`Nominatim ${res.status}`)
  const data: NominatimResult[] = await res.json()

  if (cache.size >= MAX_CACHE) {
    const first = cache.keys().next().value
    if (first) cache.delete(first)
  }
  cache.set(q, data)
  return data
}

export async function reverseGeocode(
  lat: number,
  lon: number,
  signal?: AbortSignal,
): Promise<string> {
  const fallback = `${lat.toFixed(4)}, ${lon.toFixed(4)}`
  const url = `${BASE}/reverse?format=json&lat=${lat}&lon=${lon}&addressdetails=1&accept-language=pl`
  const res = await fetch(url, { signal })
  if (!res.ok) return fallback
  const data = await res.json()
  return formatAddressLabel(data.address, data.display_name?.split(',')[0] || fallback)
}
