import { requestJson } from './client';

export type NluTimeKind = 'now' | 'dates' | 'months' | 'best_time';

export interface NluTimeSlot {
  kind: NluTimeKind;
  startDate: string | null;
  endDate: string | null;
}

export interface UnderstandRequest {
  question: string;
  currentLocationSlug: string | null;
  today: string;
}

export interface QuestionUnderstanding {
  locationSlug: string | null;
  locationFromQuestion: boolean;
  activityId: string | null;
  time: NluTimeSlot | null;
}

export interface NluHealth {
  status: string;
  extractor: string;
}

export function understandQuestion(
  request: UnderstandRequest,
  signal?: AbortSignal,
): Promise<QuestionUnderstanding> {
  return requestJson('/nlu/understand', {
    method: 'POST',
    body: JSON.stringify(request),
    signal,
  });
}

export function getNluHealth(signal?: AbortSignal): Promise<NluHealth> {
  return requestJson('/nlu/health', { signal });
}
