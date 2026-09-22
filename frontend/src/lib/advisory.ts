import type { AdvisoryCandidate, MonthRange } from '../api/advisory';
import type { QuestionUnderstanding } from '../api/nlu';

/** Ba thông tin đủ để chạy một lượt tư vấn. */
export interface AdvisoryQuery {
  locationSlug: string;
  activityId: string;
  time: MonthRange;
}

const DEFAULT_ACTIVITY_BY_LOCATION: Readonly<Record<string, string>> = {
  'ba-ria-vung-tau': 'beach',
  'vung-tau': 'beach',
  'nha-trang': 'beach',
  'phan-thiet': 'beach',
  'phu-quoc': 'beach',
};

export function inferActivityFromLocation(locationSlug: string): string | null {
  return DEFAULT_ACTIVITY_BY_LOCATION[locationSlug] ?? null;
}

export function vietnamYearMonth(now = new Date()): { year: number; month: number } {
  const parts = new Intl.DateTimeFormat('en', {
    timeZone: 'Asia/Ho_Chi_Minh', year: 'numeric', month: '2-digit',
  }).formatToParts(now);
  return {
    year: Number(parts.find(part => part.type === 'year')?.value),
    month: Number(parts.find(part => part.type === 'month')?.value),
  };
}

/** Ngày hôm nay theo giờ Việt Nam, dạng YYYY-MM-DD. */
export function vietnamToday(now = new Date()): string {
  const parts = new Intl.DateTimeFormat('en', {
    timeZone: 'Asia/Ho_Chi_Minh', year: 'numeric', month: '2-digit', day: '2-digit',
  }).formatToParts(now);
  const value = (type: Intl.DateTimeFormatPartTypes) =>
    parts.find(part => part.type === type)?.value ?? '';
  return `${value('year')}-${value('month')}-${value('day')}`;
}

/** Khoảng gồm `count` tháng liên tiếp, bắt đầu từ tháng kế tiếp. */
export function upcomingMonthRange(count: number, now = new Date()): MonthRange {
  const { year, month } = vietnamYearMonth(now);
  const nextMonth = year * 12 + month;
  const format = (index: number) => `${Math.floor(index / 12)}-${String(index % 12 + 1).padStart(2, '0')}`;
  return { startMonth: format(nextMonth), endMonth: format(nextMonth + count - 1) };
}

export function defaultAdvisoryRange(now = new Date()): MonthRange {
  return upcomingMonthRange(12, now);
}

function monthIndex(value: string): number {
  return Number(value.slice(0, 4)) * 12 + Number(value.slice(5, 7)) - 1;
}

function formatMonthIndex(index: number): string {
  return `${Math.floor(index / 12)}-${String(index % 12 + 1).padStart(2, '0')}`;
}

/** Quy kết quả đọc câu hỏi về ba tiêu chí mà /api/advisory nhận. */
export function toAdvisoryQuery(
  understanding: QuestionUnderstanding,
  fallbackLocationSlug: string,
  now = new Date(),
): AdvisoryQuery {
  const { time } = understanding;
  const locationSlug = understanding.locationSlug || fallbackLocationSlug;
  const locationActivity = understanding.locationFromQuestion
    ? inferActivityFromLocation(locationSlug)
    : null;
  let range = defaultAdvisoryRange(now);

  if (time?.kind === 'now') {
    const { year, month } = vietnamYearMonth(now);
    const currentMonth = `${year}-${String(month).padStart(2, '0')}`;
    range = { startMonth: currentMonth, endMonth: currentMonth };
  } else if (time && (time.startDate || time.endDate)) {
    const startMonth = (time.startDate ?? time.endDate)?.slice(0, 7) ?? '';
    const requestedEndMonth = (time.endDate ?? time.startDate)?.slice(0, 7) ?? '';
    const lastAllowedMonth = formatMonthIndex(monthIndex(startMonth) + 11);
    range = {
      startMonth,
      endMonth: monthIndex(requestedEndMonth) > monthIndex(lastAllowedMonth)
        ? lastAllowedMonth
        : requestedEndMonth,
    };
  }

  return {
    locationSlug,
    activityId: understanding.activityId || locationActivity || 'general',
    time: range,
  };
}

export function validateAdvisoryRange(range: MonthRange): string | null {
  const pattern = /^(?!0000)\d{4}-(0[1-9]|1[0-2])$/;
  if (!pattern.test(range.startMonth) || !pattern.test(range.endMonth)) {
    return 'Vui lòng chọn đủ tháng bắt đầu và tháng kết thúc hợp lệ.';
  }
  const index = (value: string) => Number(value.slice(0, 4)) * 12 + Number(value.slice(5, 7));
  const count = index(range.endMonth) - index(range.startMonth) + 1;
  return count < 1 || count > 12 ? 'Chọn từ 1 đến 12 tháng liên tiếp, tháng kết thúc không trước tháng bắt đầu.' : null;
}

/**
 * Xếp ứng viên theo tháng 1 → 12, trong cùng tháng theo ngày bắt đầu.
 * Điểm được tính từ lịch sử khí hậu nên năm không ảnh hưởng tới việc so sánh các tháng.
 */
export function sortCandidatesByMonth(candidates: AdvisoryCandidate[]): AdvisoryCandidate[] {
  // startDate dạng YYYY-MM-DD, bỏ năm còn MM-DD để so sánh.
  return [...candidates].sort((a, b) =>
    a.window.startDate.slice(5).localeCompare(b.window.startDate.slice(5)));
}

/** Nhãn không có năm, dùng trên biểu đồ: 'Tháng 1', 'Đầu tháng 12'. */
export function formatMonthOnlyLabel(window: AdvisoryCandidate['window']): string {
  const month = Number(window.startDate.slice(5, 7));
  if (window.resolution === 'month') return `Tháng ${month}`;
  const day = Number(window.startDate.slice(8, 10));
  const period = day <= 10 ? 'Đầu' : day <= 20 ? 'Giữa' : 'Cuối';
  return `${period} tháng ${month}`;
}

export function formatAdvisoryDate(value: string): string {
  return value.split('-').reverse().join('/');
}

export function formatAdvisoryNumber(value: number): string {
  return value.toLocaleString('vi-VN', { maximumFractionDigits: 1 });
}
