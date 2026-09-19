import { describe, expect, it } from 'vitest';
import { clamp, getFactorColor, getScoreColor } from './scoring';

describe('các helper hiển thị điểm', () => {
  it('giới hạn giá trị trong khoảng', () => {
    expect(clamp(-1, 0, 100)).toBe(0);
    expect(clamp(120, 0, 100)).toBe(100);
  });

  it('chọn màu cột theo giờ và điểm', () => {
    expect(getScoreColor(2, 90)).toBe('var(--night)');
    expect(getScoreColor(10, 75)).toBe('var(--acc)');
    expect(getScoreColor(10, 55)).toBe('var(--mid)');
    expect(getScoreColor(10, 30)).toBe('var(--dim)');
  });

  it('chọn màu yếu tố theo giá trị', () => {
    expect(getFactorColor(70)).toBe('var(--acc)');
    expect(getFactorColor(50)).toBe('var(--mid)');
    expect(getFactorColor(20)).toBe('var(--weak)');
  });
});
