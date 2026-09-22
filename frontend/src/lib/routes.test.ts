import { describe, expect, it } from 'vitest';
import { isPageTab, pagePath, readViewedLocationSlug } from './routes';

describe('routes', () => {
  it('trang tổng quan nằm ở đường dẫn gốc', () => {
    expect(pagePath('tong-quan')).toBe('/');
    expect(pagePath('tu-van')).toBe('/tu-van');
  });

  it('chỉ nhận các trang có trong danh mục', () => {
    expect(isPageTab('lich-su')).toBe(true);
    expect(isPageTab('ha-noi')).toBe(false);
    expect(isPageTab('di-dau')).toBe(false);
    expect(isPageTab(undefined)).toBe(false);
  });

  it('đọc địa điểm đang xem từ history state', () => {
    expect(readViewedLocationSlug({ locationSlug: 'da-nang' })).toBe('da-nang');
    expect(readViewedLocationSlug(null)).toBeUndefined();
    expect(readViewedLocationSlug({ locationSlug: 1 })).toBeUndefined();
  });
});
