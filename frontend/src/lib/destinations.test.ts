import { describe, expect, it } from 'vitest';
import type { ActivityProfile } from '../api/advisory';
import { destinationActivities, formatMonthChip, formatMonthTitle, upcomingMonths } from './destinations';

describe('upcomingMonths', () => {
  it('trả 12 tháng bắt đầu từ tháng kế tiếp và qua năm đúng', () => {
    const months = upcomingMonths(12, new Date('2026-11-15T12:00:00+07:00'));
    expect(months).toHaveLength(12);
    expect(months[0]).toBe('2026-12');
    expect(months[1]).toBe('2027-01');
    expect(months[11]).toBe('2027-11');
  });

  it('tính theo giờ Việt Nam khi giờ UTC vẫn còn ở tháng trước', () => {
    expect(upcomingMonths(1, new Date('2026-09-30T18:00:00Z'))).toEqual(['2026-11']);
  });
});

it('định dạng nhãn chip và tiêu đề tháng', () => {
  expect(formatMonthChip('2026-12')).toBe('Th 12/26');
  expect(formatMonthChip('2027-03')).toBe('Th 3/27');
  expect(formatMonthTitle('2027-03')).toBe('Tháng 3/2027');
});

it('bỏ hoạt động phơi quần áo và giữ nguyên thứ tự còn lại', () => {
  const activity = (id: string) => ({ id }) as ActivityProfile;
  const result = destinationActivities(['general', 'drying', 'travel', 'beach'].map(activity));
  expect(result.map(item => item.id)).toEqual(['general', 'travel', 'beach']);
});
