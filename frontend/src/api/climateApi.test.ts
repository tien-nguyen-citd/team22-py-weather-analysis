import { afterEach, describe, expect, it, vi } from 'vitest';
import type { LocationItem } from '../types';
import { fetchClimateArchive, getArchiveRange, getHistoryData } from './climateApi';

const HA_NOI: LocationItem = {
  name: 'Hà Nội',
  slug: 'ha-noi',
  region: 'dbbb',
  regionLabel: 'Đồng bằng Bắc Bộ',
  tempOffset: 0,
  lat: 21.0285,
  lon: 105.8542,
};

describe('climate archive', () => {
  afterEach(() => vi.unstubAllGlobals());

  it('uses 12 complete recent months and the previous 10 years as baseline', async () => {
    const range = getArchiveRange(new Date('2026-09-19T00:00:00Z'));
    expect(range).toEqual({
      startDate: '2015-09-01',
      endDate: '2026-08-31',
      recentStart: '2025-09-01',
      recentPeriod: '09/2025–08/2026',
      baselinePeriod: '09/2015–08/2025',
    });

    const time: string[] = [];
    const precipitation_sum: number[] = [];
    const temperature_2m_mean: number[] = [];
    for (let stamp = Date.parse(`${range.startDate}T00:00:00Z`); stamp <= Date.parse(`${range.endDate}T00:00:00Z`); stamp += 86400000) {
      const date = new Date(stamp).toISOString().slice(0, 10);
      const isRecent = date >= range.recentStart;
      time.push(date);
      precipitation_sum.push(isRecent ? 2 : 1);
      temperature_2m_mean.push(isRecent ? 30 : 20);
    }

    const fetchMock = vi.fn(async (url: string) => {
      const parsedUrl = new URL(url, 'http://localhost');
      expect(parsedUrl.pathname).toBe('/api/locations/ha-noi/climate');
      const params = parsedUrl.searchParams;
      expect(params.get('start_date')).toBe(range.startDate);
      expect(params.get('end_date')).toBe(range.endDate);
      return new Response(JSON.stringify({ daily: { time, precipitation_sum, temperature_2m_mean } }), { status: 200 });
    });
    vi.stubGlobal('fetch', fetchMock);

    const location = HA_NOI;
    const archive = await fetchClimateArchive(location, range);
    expect(archive.months).toHaveLength(12);
    expect(archive.recent).toHaveLength(12);
    expect(archive.months[0]).toMatchObject({ month: 1, t: 20, r: 31, d: 31 });
    expect(archive.recent[0]).toMatchObject({ year: 2025, month: 9, t: 30, r: 60, d: 30 });
    expect(archive.recent[11]).toMatchObject({ year: 2026, month: 8, t: 30, r: 62, d: 31 });

    const history = getHistoryData(location, archive);
    expect(history.monthly).toHaveLength(12);
    expect(history.percentDiff).toBe(100);
    expect(history.totalRecent).toBe(730);
    expect(history.totalHistorical).toBe(365);
    expect(history.rainComparison).toBe('cao hơn 100%');
    expect(history.wettestMonth).toMatchObject({ label: '10/2025', rain: 62, days: 31 });
    expect(history.highestTempMonth).toEqual({ maxTemp: 30, maxLabel: '09/2025', minTemp: 30, minLabel: '09/2025' });
  });

  it('describes lower and approximately equal rainfall without a misleading plus sign', () => {
    const location = HA_NOI;
    const archive = {
      months: Array.from({ length: 12 }, (_, index) => ({ month: index + 1, t: 25, r: 10, d: 5, tourismScore: 80 })),
      recent: Array.from({ length: 12 }, (_, index) => ({ year: 2025, month: index + 1, t: 25, r: 5, d: 3 })),
      recentPeriod: '01/2025–12/2025',
      baselinePeriod: '01/2015–12/2024',
      endDate: '2025-12-31',
    };
    expect(getHistoryData(location, archive).rainComparison).toBe('thấp hơn 50%');
    archive.recent = archive.recent.map(item => ({ ...item, r: 10 }));
    expect(getHistoryData(location, archive)).toMatchObject({ percentDiff: 0, rainComparison: 'xấp xỉ mức trung bình' });
  });

  it('rejects incomplete daily history instead of showing misleading climate values', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => new Response(JSON.stringify({ daily: {
      time: ['2026-08-31'], precipitation_sum: [1], temperature_2m_mean: [25],
    } }), { status: 200 })));
    await expect(fetchClimateArchive(HA_NOI, getArchiveRange(new Date('2026-09-19T00:00:00Z'))))
      .rejects.toThrow('Dữ liệu lịch sử chưa đủ ngày');
  });
});
