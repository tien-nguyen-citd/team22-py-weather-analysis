import type { PageTab } from '../components/Header';

export const PAGE_TABS: PageTab[] = ['tong-quan', 'so-sanh', 'lich-su', 'tu-van', 'di-dau'];

// Địa điểm đang xem được giữ trong history state thay vì trên URL.
// Không có state thì các trang dùng vị trí của người dùng.
export interface ViewedLocationState {
  locationSlug: string;
}

export function isPageTab(value: string | undefined): value is PageTab {
  return PAGE_TABS.includes(value as PageTab);
}

export function pagePath(page: PageTab): string {
  return page === 'tong-quan' ? '/' : `/${page}`;
}

export function readViewedLocationSlug(state: unknown): string | undefined {
  const slug = (state as Partial<ViewedLocationState> | null)?.locationSlug;
  return typeof slug === 'string' ? slug : undefined;
}
