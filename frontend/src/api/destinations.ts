import type { ActivityProfile, AdvisoryCandidate } from './advisory';
import { requestJson } from './client';

export interface DestinationRequest {
  month: string;
  activityId: string;
}

export interface DestinationResult {
  location: {
    slug: string;
    name: string;
    regionLabel: string;
  };
  candidate: AdvisoryCandidate;
}

export interface DestinationRanking {
  month: string;
  activity: ActivityProfile;
  baselineStart: string;
  baselineEnd: string;
  destinations: DestinationResult[];
  summary: string;
  lowSuitability: boolean;
  notes: string[];
}

export function getDestinationRanking(
  request: DestinationRequest,
  signal?: AbortSignal,
): Promise<DestinationRanking> {
  return requestJson('/api/advisory/destinations', {
    method: 'POST',
    body: JSON.stringify(request),
    signal,
  });
}
