import type { NluDecisionSource } from '../api/nlu';

export type ShortcutKeys = Pick<KeyboardEvent, 'ctrlKey' | 'altKey' | 'shiftKey' | 'metaKey' | 'key'>;

/** Ctrl + Alt + Backspace bật/tắt khung chi tiết phân tích NLU. */
export function isNluDebugShortcut(event: ShortcutKeys): boolean {
  return event.ctrlKey && event.altKey && !event.shiftKey && !event.metaKey
    && event.key === 'Backspace';
}

export const DECISION_SOURCE_LABELS: Record<NluDecisionSource, string> = {
  location: 'Câu có địa điểm trong danh mục',
  keyword: 'Khớp từ khóa',
  best_time: 'Câu hỏi thời điểm tốt nhất',
  no_words: 'Không còn chữ nào sau khi bỏ địa điểm và từ khóa',
  nearest_examples: 'Bỏ phiếu theo câu mẫu gần nhất (k-NN)',
};
