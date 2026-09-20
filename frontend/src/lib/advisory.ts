import type { MonthRange } from '../api/advisory';

export function defaultAdvisoryRange(now = new Date()): MonthRange {
  const parts = new Intl.DateTimeFormat('en', {
    timeZone: 'Asia/Ho_Chi_Minh', year: 'numeric', month: '2-digit',
  }).formatToParts(now);
  const year = Number(parts.find(part => part.type === 'year')?.value);
  const month = Number(parts.find(part => part.type === 'month')?.value);
  const nextMonth = year * 12 + month;
  const format = (index: number) => `${Math.floor(index / 12)}-${String(index % 12 + 1).padStart(2, '0')}`;
  return { startMonth: format(nextMonth), endMonth: format(nextMonth + 11) };
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

export function formatAdvisoryDate(value: string): string {
  return value.split('-').reverse().join('/');
}

export function formatAdvisoryNumber(value: number): string {
  return value.toLocaleString('vi-VN', { maximumFractionDigits: 1 });
}
