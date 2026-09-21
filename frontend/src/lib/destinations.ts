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
import type { ActivityProfile } from '../api/advisory';
import { vietnamYearMonth } from './advisory';

/** Tab "Đi đâu?" mặc định là Du lịch vì hợp ngữ cảnh chọn điểm đến hơn "Nhu cầu chung". */
export const DEFAULT_DESTINATION_ACTIVITY = 'travel';

/** Phơi quần áo không có nghĩa khi chọn nơi để đi. */
const EXCLUDED_ACTIVITY_IDS = new Set(['drying']);

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

export function destinationActivities(activities: ActivityProfile[]): ActivityProfile[] {
  return activities.filter(activity => !EXCLUDED_ACTIVITY_IDS.has(activity.id));
}

export function activityIcon(activityId: string): LucideIcon {
  return ACTIVITY_ICONS[activityId] ?? MapPin;
}
