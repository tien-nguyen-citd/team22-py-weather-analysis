import { describe, expect, it } from 'vitest';
import type { ActivityProfile } from '../api/advisory';
import type { QuestionUnderstanding } from '../api/nlu';
import {
  DEFAULT_DESTINATION_ACTIVITY,
  destinationActivities,
  formatMonthChip,
  formatMonthTitle,
  toDestinationQuery,
  upcomingMonths,
} from './destinations';

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

describe('toDestinationQuery', () => {
  const NOW = new Date('2026-09-20T05:00:00Z');
  const understanding = (
    time: QuestionUnderstanding['time'],
    activityId: string | null = 'beach',
  ): QuestionUnderstanding => ({
    locationSlug: 'ha-noi',
    locationFromQuestion: false,
    activityId,
    time,
    intent: 'find_place',
  });

  it.each([
    ['khoảng tháng', { kind: 'months', startDate: '2026-12-01', endDate: '2026-12-31' }, '2026-12'],
    ['khoảng ngày qua tháng', { kind: 'dates', startDate: '2026-10-28', endDate: '2026-11-03' }, '2026-10'],
    ['hiện tại', { kind: 'now', startDate: null, endDate: null }, '2026-09'],
    ['tìm thời điểm', { kind: 'best_time', startDate: '2027-04-01', endDate: '2027-08-31' }, '2026-10'],
    ['không có thời gian', null, '2026-10'],
  ] as const)('quy đổi %s', (_label, time, month) => {
    expect(toDestinationQuery(understanding(time), NOW).month).toBe(month);
  });

  it('giữ hoạt động người dùng nêu trong câu hỏi', () => {
    expect(toDestinationQuery(understanding(null), NOW).activityId).toBe('beach');
  });

  it('dùng du lịch khi câu hỏi không nêu hoạt động', () => {
    expect(toDestinationQuery(understanding(null, null), NOW).activityId).toBe(DEFAULT_DESTINATION_ACTIVITY);
  });
});
