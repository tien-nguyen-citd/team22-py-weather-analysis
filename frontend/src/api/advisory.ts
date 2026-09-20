import { requestJson } from './client';

export interface MonthRange {
  startMonth: string;
  endMonth: string;
}

export interface AdvisoryRequest {
  locationSlug: string;
  time: MonthRange;
  activityId: string;
  topK: number;
}

export interface ActivityProfile {
  id: string;
  name: string;
  rainWeight: number;
  temperatureWeight: number;
  temperatureMin: number | null;
  temperatureMax: number | null;
  description: string;
  rainThresholdMm: number;
}

export interface AdvisoryCandidate {
  window: {
    startDate: string;
    endDate: string;
    label: string;
    resolution: 'month' | 'period';
  };
  temperatureMean: number;
  rainyDayPercentage: number;
  precipitationMean: number;
  rainScore: number;
  temperatureScore: number | null;
  rainContribution: number;
  temperatureContribution: number;
  score: number;
  sampleYears: number;
  sampleDays: number;
  explanation: string;
  rank: number;
  similarToBest: boolean;
}

export interface Advice {
  request: AdvisoryRequest;
  baselineStart: string;
  baselineEnd: string;
  activity: ActivityProfile;
  recommendations: AdvisoryCandidate[];
  candidates: AdvisoryCandidate[];
  summary: string;
  lowSuitability: boolean;
  notes: string[];
}

export function getAdvisoryActivities(signal?: AbortSignal): Promise<ActivityProfile[]> {
  return requestJson('/api/advisory/activities', { signal });
}

export function getAdvice(request: AdvisoryRequest, signal?: AbortSignal): Promise<Advice> {
  return requestJson('/api/advisory', {
    method: 'POST',
    body: JSON.stringify(request),
    signal,
  });
}
