import type { LocationItem } from '../types';
import { requestJson } from './client';

export interface HistoryMonth {
  year: number;
  month: number;
  rain: number;
  baselineRain: number;
}

export interface LocationHistory {
  location: LocationItem;
  recentPeriod: string;
  baselinePeriod: string;
  months: HistoryMonth[];
  totalRain: number;
  baselineTotalRain: number;
  rainDiffPercent: number;
  rainComparison: string;
  wettestMonth: { label: string; rain: number; rainyDays: number };
  hottestMonth: { label: string; temperature: number };
  coolestMonth: { label: string; temperature: number };
}

export interface MonthClimate {
  month: number;
  temperature: number;
  rain: number;
  rainyDays: number;
  tourismScore: number;
}

export interface ComparedLocation {
  location: LocationItem;
  months: MonthClimate[];
  summary: string;
}

export interface LocationComparison {
  month: number;
  baselinePeriod: string;
  a: ComparedLocation;
  b: ComparedLocation;
  conclusion: string;
  yearRecommendation: string;
}

export function getLocationHistory(
  slug: string,
  signal?: AbortSignal,
): Promise<LocationHistory> {
  return requestJson<LocationHistory>(
    `/api/locations/${encodeURIComponent(slug)}/history`,
    { signal },
  );
}

export function getLocationComparison(
  slugA: string,
  slugB: string,
  month: number,
  signal?: AbortSignal,
): Promise<LocationComparison> {
  const params = new URLSearchParams({
    a: slugA,
    b: slugB,
    month: String(month),
  });
  return requestJson<LocationComparison>(`/api/locations/compare?${params}`, {
    signal,
  });
}
