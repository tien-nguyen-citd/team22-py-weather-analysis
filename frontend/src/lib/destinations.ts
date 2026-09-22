import {
  Camera,
  Coffee,
  Footprints,
  Heart,
  Luggage,
  MapPin,
  Sun,
  Tent,
  Waves,
  type LucideIcon,
} from 'lucide-react';
import type { QuestionUnderstanding } from '../api/nlu';
import { vietnamYearMonth } from './advisory';

/** Hai thông tin đủ để xếp hạng điểm đến. */
export interface DestinationQuery {
  month: string;
  activityId: string;
}

/** Tab "Đi đâu?" mặc định là Du lịch vì hợp ngữ cảnh chọn điểm đến hơn "Nhu cầu chung". */
export const DEFAULT_DESTINATION_ACTIVITY = 'travel';

const ACTIVITY_ICONS: Readonly<Record<string, LucideIcon>> = {
  general: Sun,
  travel: Luggage,
  wedding: Heart,
  running: Footprints,
  photography: Camera,
  coffee: Coffee,
  beach: Waves,
  camping: Tent,
};

/** `count` tháng liên tiếp dạng YYYY-MM, bắt đầu từ tháng kế tiếp theo giờ Việt Nam. */
export function upcomingMonths(count: number, now = new Date()): string[] {
  const { year, month } = vietnamYearMonth(now);
  const nextMonthIndex = year * 12 + month;
  return Array.from({ length: count }, (_, offset) => {
    const index = nextMonthIndex + offset;
    return `${Math.floor(index / 12)}-${String(index % 12 + 1).padStart(2, '0')}`;
  });
}

/** '2026-12' → 'Th 12/26'. */
export function formatMonthChip(month: string): string {
  return `Th ${Number(month.slice(5, 7))}/${month.slice(2, 4)}`;
}

/** '2026-12' → 'Tháng 12/2026'. */
export function formatMonthTitle(month: string): string {
  return `Tháng ${Number(month.slice(5, 7))}/${month.slice(0, 4)}`;
}

export function activityIcon(activityId: string): LucideIcon {
  return ACTIVITY_ICONS[activityId] ?? MapPin;
}

/**
 * Quy kết quả đọc câu hỏi về tháng và hoạt động để xếp hạng điểm đến.
 * Câu hỏi nêu ngày hoặc tháng thì lấy tháng bắt đầu, hỏi hiện tại thì lấy tháng này,
 * còn lại lấy tháng kế tiếp.
 */
export function toDestinationQuery(
  understanding: QuestionUnderstanding,
  now = new Date(),
): DestinationQuery {
  const { time } = understanding;
  const { year, month } = vietnamYearMonth(now);
  const currentMonth = `${year}-${String(month).padStart(2, '0')}`;
  const requestedDate = time?.startDate ?? time?.endDate;
  let targetMonth = upcomingMonths(1, now)[0];

  if (time?.kind === 'now') {
    targetMonth = currentMonth;
  } else if ((time?.kind === 'months' || time?.kind === 'dates') && requestedDate) {
    targetMonth = requestedDate.slice(0, 7);
  }

  return {
    month: targetMonth,
    activityId: understanding.activityId || DEFAULT_DESTINATION_ACTIVITY,
  };
}
