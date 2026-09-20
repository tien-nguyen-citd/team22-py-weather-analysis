import { describe, expect, it } from 'vitest';
import { defaultAdvisoryRange, validateAdvisoryRange } from './advisory';

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
