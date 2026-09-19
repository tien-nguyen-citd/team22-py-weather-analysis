import { requestJson } from './client';

export function fetchCurrentTemperatures(
  signal?: AbortSignal,
): Promise<Record<string, number>> {
  return requestJson<Record<string, number>>('/api/locations/temperatures', { signal });
}
