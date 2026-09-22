import { describe, expect, it } from 'vitest';
import type { AdvisoryCandidate } from '../api/advisory';
import type { QuestionUnderstanding } from '../api/nlu';
import {
  defaultAdvisoryRange,
  formatMonthOnlyLabel,
  inferActivityFromLocation,
  sortCandidatesByMonth,
  toAdvisoryQuery,
  validateAdvisoryRange,
  vietnamToday,
} from './advisory';

const NOW = new Date('2026-09-20T05:00:00Z');

function candidate(startDate: string, resolution: 'month' | 'period' = 'month'): AdvisoryCandidate {
  return {
    window: { startDate, endDate: startDate, label: startDate, resolution },
    temperatureMean: 25,
    rainyDayPercentage: 10,
    precipitationMean: 3,
    rainScore: 100,
    temperatureScore: 100,
    rainContribution: 80,
    temperatureContribution: 20,
    score: 100,
    sampleYears: 10,
    sampleDays: 300,
    explanation: '',
    rank: 1,
    similarToBest: false,
  };
}

function understanding(
  time: QuestionUnderstanding['time'],
  overrides: Partial<QuestionUnderstanding> = {},
): QuestionUnderstanding {
  return {
    locationSlug: 'da-lat',
    locationFromQuestion: true,
    activityId: 'camping',
    time,
    intent: 'find_time',
    debug: null,
    ...overrides,
  };
}

describe('Khoảng tháng tư vấn', () => {
  it('lấy tháng kế tiếp theo ngày Việt Nam khi UTC vẫn ở năm trước', () => {
    expect(defaultAdvisoryRange(new Date('2026-12-31T18:00:00Z'))).toEqual({
      startMonth: '2027-02', endMonth: '2028-01',
    });
    expect(defaultAdvisoryRange(new Date('2026-12-15T00:00:00Z'))).toEqual({
      startMonth: '2027-01', endMonth: '2027-12',
    });
  });

  it('cho phép 1–12 tháng liên tiếp qua năm', () => {
    expect(validateAdvisoryRange({ startMonth: '2027-12', endMonth: '2027-12' })).toBeNull();
    expect(validateAdvisoryRange({ startMonth: '2027-12', endMonth: '2028-11' })).toBeNull();
  });

  it.each([
    ['', '2027-01'], ['2027-1', '2027-12'], ['0000-01', '0000-02'],
    ['2027-13', '2028-01'], ['2027-02', '2027-01'], ['2027-01', '2028-01'],
  ])('từ chối khoảng %s đến %s', (startMonth, endMonth) => {
    expect(validateAdvisoryRange({ startMonth, endMonth })).not.toBeNull();
  });
});

describe('Quy đổi kết quả đọc câu hỏi', () => {
  it.each([
    ['không có thời gian', null, { startMonth: '2026-10', endMonth: '2027-09' }],
    ['hiện tại', { kind: 'now', startDate: '2026-09-20', endDate: '2026-09-20' }, { startMonth: '2026-09', endMonth: '2026-09' }],
    ['khoảng ngày', { kind: 'dates', startDate: '2026-10-28', endDate: '2026-11-03' }, { startMonth: '2026-10', endMonth: '2026-11' }],
    ['khoảng tháng', { kind: 'months', startDate: '2027-01-01', endDate: '2027-03-31' }, { startMonth: '2027-01', endMonth: '2027-03' }],
    ['tìm thời điểm không giới hạn', { kind: 'best_time', startDate: null, endDate: null }, { startMonth: '2026-10', endMonth: '2027-09' }],
    ['tìm thời điểm có giới hạn', { kind: 'best_time', startDate: '2027-04-01', endDate: '2027-08-31' }, { startMonth: '2027-04', endMonth: '2027-08' }],
  ] as const)('quy đổi %s', (_label, time, expected) => {
    expect(toAdvisoryQuery(understanding(time), 'ha-noi', NOW).time).toEqual(expected);
  });

  it.each([
    [{ kind: 'dates', startDate: '2027-02-10', endDate: null }, { startMonth: '2027-02', endMonth: '2027-02' }],
    [{ kind: 'months', startDate: null, endDate: '2027-06-30' }, { startMonth: '2027-06', endMonth: '2027-06' }],
  ] as const)('dùng mốc còn lại khi khoảng thời gian thiếu một đầu', (time, expected) => {
    expect(toAdvisoryQuery(understanding(time), 'ha-noi', NOW).time).toEqual(expected);
  });

  it('dùng địa điểm hiện tại và nhu cầu chung khi service không đọc được', () => {
    const result = toAdvisoryQuery(understanding(null, {
      locationSlug: null,
      activityId: null,
    }), 'ha-noi', NOW);

    expect(result.locationSlug).toBe('ha-noi');
    expect(result.activityId).toBe('general');
  });

  it.each([
    'ba-ria-vung-tau',
    'vung-tau',
    'nha-trang',
    'phan-thiet',
    'phu-quoc',
  ])('gợi ý tắm biển khi câu hỏi chỉ nêu địa điểm %s', locationSlug => {
    const result = toAdvisoryQuery(understanding(null, {
      locationSlug,
      locationFromQuestion: true,
      activityId: null,
    }), 'ha-noi', NOW);

    expect(result.activityId).toBe('beach');
  });

  it('ưu tiên hoạt động người dùng nói rõ hơn gợi ý của địa điểm', () => {
    const result = toAdvisoryQuery(understanding(null, {
      locationSlug: 'vung-tau',
      locationFromQuestion: true,
      activityId: 'outdoor_event',
    }), 'ha-noi', NOW);

    expect(result.activityId).toBe('outdoor_event');
  });

  it('dùng nhu cầu chung cho địa điểm không có hoạt động đặc trưng', () => {
    const result = toAdvisoryQuery(understanding(null, {
      locationSlug: 'ha-noi',
      locationFromQuestion: true,
      activityId: null,
    }), 'da-nang', NOW);

    expect(result.activityId).toBe('general');
    expect(inferActivityFromLocation('ha-noi')).toBeNull();
  });

  it('không suy luận từ vị trí mặc định khi câu hỏi không nhắc địa điểm', () => {
    const result = toAdvisoryQuery(understanding(null, {
      locationSlug: null,
      locationFromQuestion: false,
      activityId: null,
    }), 'vung-tau', NOW);

    expect(result.activityId).toBe('general');
  });

  it('cắt khoảng dài hơn 12 tháng từ tháng bắt đầu', () => {
    const result = toAdvisoryQuery(understanding({
      kind: 'months', startDate: '2026-11-01', endDate: '2028-03-31',
    }), 'ha-noi', NOW);

    expect(result.time).toEqual({ startMonth: '2026-11', endMonth: '2027-10' });
  });
});

describe('Biểu đồ theo tháng', () => {
  it('xếp khoảng 12 tháng qua năm theo tháng 1 → 12', () => {
    const candidates = ['2026-10', '2026-11', '2026-12', '2027-01', '2027-02', '2027-03',
      '2027-04', '2027-05', '2027-06', '2027-07', '2027-08', '2027-09']
      .map(month => candidate(`${month}-01`));

    expect(sortCandidatesByMonth(candidates).map(item => formatMonthOnlyLabel(item.window))).toEqual([
      'Tháng 1', 'Tháng 2', 'Tháng 3', 'Tháng 4', 'Tháng 5', 'Tháng 6',
      'Tháng 7', 'Tháng 8', 'Tháng 9', 'Tháng 10', 'Tháng 11', 'Tháng 12',
    ]);
  });

  it('xếp giai đoạn theo tháng rồi đầu, giữa, cuối tháng', () => {
    const candidates = ['2026-12-01', '2026-12-11', '2026-12-21', '2027-01-01', '2027-01-11', '2027-01-21']
      .map(startDate => candidate(startDate, 'period'));

    expect(sortCandidatesByMonth(candidates).map(item => formatMonthOnlyLabel(item.window))).toEqual([
      'Đầu tháng 1', 'Giữa tháng 1', 'Cuối tháng 1',
      'Đầu tháng 12', 'Giữa tháng 12', 'Cuối tháng 12',
    ]);
  });

  it('không làm đổi thứ tự của danh sách gốc', () => {
    const candidates = [candidate('2026-12-01'), candidate('2027-01-01')];
    sortCandidatesByMonth(candidates);
    expect(candidates.map(item => item.window.startDate)).toEqual(['2026-12-01', '2027-01-01']);
  });
});

describe('Ngày Việt Nam', () => {
  it('đổi ngày theo múi giờ Việt Nam thay vì UTC', () => {
    expect(vietnamToday(new Date('2026-09-20T16:59:59Z'))).toBe('2026-09-20');
    expect(vietnamToday(new Date('2026-09-20T17:00:00Z'))).toBe('2026-09-21');
  });
});
