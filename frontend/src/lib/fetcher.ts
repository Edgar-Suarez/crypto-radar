import { API_BASE } from './config'

export class ApiError extends Error {
  constructor(public status: number, message: string) { super(message) }
}

export async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), 10_000)
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      ...options, signal: controller.signal,
      headers: { 'Content-Type': 'application/json', ...options?.headers },
    })
    clearTimeout(timeout)
    if (!res.ok) throw new ApiError(res.status, `API ${res.status}: ${path}`)
    return res.json() as Promise<T>
  } catch (err) {
    clearTimeout(timeout)
    if (err instanceof ApiError) throw err
    throw new ApiError(0, `Network: ${(err as Error).message}`)
  }
}
