import { requestJson } from './client';

export type NluTimeKind = 'now' | 'dates' | 'months' | 'best_time';

export type NluIntent = 'find_place' | 'find_time';

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

export type NluDecisionSource =
  | 'location'
  | 'keyword'
  | 'best_time'
  | 'no_words'
  | 'nearest_examples';

export interface NluNeighbor {
  label: string | null;
  text: string;
  similarity: number;
}

export type NluDecisionMethod = 'rule' | 'minilm';

export interface NluDecision {
  method: NluDecisionMethod;
  source: NluDecisionSource;
  matchedText: string | null;
  neighbors: NluNeighbor[];
}

export interface NluDebug {
  embeddingText: string;
  locationText: string | null;
  activity: NluDecision;
  intent: NluDecision;
}

export interface QuestionUnderstanding {
  locationSlug: string | null;
  locationFromQuestion: boolean;
  activityId: string | null;
  time: NluTimeSlot | null;
  intent: NluIntent;
  debug: NluDebug | null;
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
