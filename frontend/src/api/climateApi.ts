import type { LocationItem } from '../types';
import { calculateTourismScore } from '../lib/scoring';
import { requestJson } from './client';

export interface MonthlyClimate {
  month: number;
  t: number;
  r: number;
  d: number;
  tourismScore: number;
}

interface ArchiveDaily {
  time: string[];
  precipitation_sum: (number | null)[];
  temperature_2m_mean: (number | null)[];
}

interface MonthTotal {
  temperatureSum: number;
  rainSum: number;
  rainyDays: number;
  days: number;
}

export interface ClimateArchive {
  months: MonthlyClimate[];
  recent: { year: number; month: number; t: number; r: number; d: number }[];
  recentPeriod: string;
  baselinePeriod: string;
  endDate: string;
}

const formatDate = (date: Date) => date.toISOString().slice(0, 10);
const formatMonthYear = (year: number, month: number) => `${String(month).padStart(2, '0')}/${year}`;
const round1 = (value: number) => Math.round(value * 10) / 10;

function monthKey(year: number, month: number) {
  return `${year}-${String(month).padStart(2, '0')}`;
}

function getBangkokYearMonth(now: Date) {
  const parts = new Intl.DateTimeFormat('en-US', {
    timeZone: 'Asia/Bangkok', year: 'numeric', month: 'numeric',
  }).formatToParts(now);
  return {
    year: Number(parts.find(part => part.type === 'year')?.value),
    month: Number(parts.find(part => part.type === 'month')?.value),
  };
}

export function getArchiveRange(now = new Date()) {
  const { year, month } = getBangkokYearMonth(now);
  const recentStart = new Date(Date.UTC(year, month - 1 - 12, 1));
  const baselineStart = new Date(Date.UTC(year, month - 1 - 12 - 120, 1));
  const baselineEnd = new Date(recentStart.getTime() - 86400000);
  const lastCompleteDay = new Date(Date.UTC(year, month - 1, 0));
  return {
    startDate: formatDate(baselineStart),
    endDate: formatDate(lastCompleteDay),
    recentStart: formatDate(recentStart),
    recentPeriod: `${formatMonthYear(recentStart.getUTCFullYear(), recentStart.getUTCMonth() + 1)}–${formatMonthYear(lastCompleteDay.getUTCFullYear(), lastCompleteDay.getUTCMonth() + 1)}`,
    baselinePeriod: `${formatMonthYear(baselineStart.getUTCFullYear(), baselineStart.getUTCMonth() + 1)}–${formatMonthYear(baselineEnd.getUTCFullYear(), baselineEnd.getUTCMonth() + 1)}`,
  };
}

function aggregateDaily(daily: ArchiveDaily, range: ReturnType<typeof getArchiveRange>): ClimateArchive {
  if (!daily) throw new Error('Dữ liệu lịch sử không hợp lệ');
  const { time, precipitation_sum: rain, temperature_2m_mean: temperature } = daily;
  if (!Array.isArray(time) || !Array.isArray(rain) || !Array.isArray(temperature) ||
      time.length !== rain.length || time.length !== temperature.length) {
    throw new Error('Dữ liệu lịch sử không hợp lệ');
  }

  const totals = new Map<string, MonthTotal>();
  const startTime = Date.parse(`${range.startDate}T00:00:00Z`);
  const expectedDays = Math.round((Date.parse(`${range.endDate}T00:00:00Z`) - startTime) / 86400000) + 1;
  if (time.length !== expectedDays) throw new Error('Dữ liệu lịch sử chưa đủ ngày');

  for (let index = 0; index < time.length; index++) {
    const expectedDate = new Date(startTime + index * 86400000);
    const date = time[index];
    const rainValue = rain[index];
    const tempValue = temperature[index];
    if (date !== formatDate(expectedDate) ||
        typeof rainValue !== 'number' || !Number.isFinite(rainValue) || rainValue < 0 ||
        typeof tempValue !== 'number' || !Number.isFinite(tempValue)) {
      throw new Error('Dữ liệu lịch sử không hợp lệ');
    }
    const key = date.slice(0, 7);
    const total = totals.get(key) ?? { temperatureSum: 0, rainSum: 0, rainyDays: 0, days: 0 };
    total.temperatureSum += tempValue;
    total.rainSum += rainValue;
    total.rainyDays += Number(rainValue >= 1);
    total.days += 1;
    totals.set(key, total);
  }

  const recentStartYear = Number(range.recentStart.slice(0, 4));
  const recentStartMonth = Number(range.recentStart.slice(5, 7));
  const recent = Array.from({ length: 12 }, (_, index) => {
    const date = new Date(Date.UTC(recentStartYear, recentStartMonth - 1 + index, 1));
    const year = date.getUTCFullYear();
    const month = date.getUTCMonth() + 1;
    const total = totals.get(monthKey(year, month));
    if (!total) throw new Error('Dữ liệu lịch sử chưa đủ tháng');
    return { year, month, t: round1(total.temperatureSum / total.days), r: Math.round(total.rainSum), d: total.rainyDays };
  });

  const months = Array.from({ length: 12 }, (_, index) => {
    const month = index + 1;
    let temperatureTotal = 0;
    let rainTotal = 0;
    let rainyDaysTotal = 0;
    for (let yearOffset = -120; yearOffset < 0; yearOffset += 12) {
      const date = new Date(Date.UTC(recentStartYear, recentStartMonth - 1 + yearOffset + ((month - recentStartMonth + 12) % 12), 1));
      const total = totals.get(monthKey(date.getUTCFullYear(), month));
      if (!total) throw new Error('Dữ liệu lịch sử chưa đủ 10 năm');
      temperatureTotal += total.temperatureSum / total.days;
      rainTotal += total.rainSum;
      rainyDaysTotal += total.rainyDays;
    }
    const t = round1(temperatureTotal / 10);
    const r = Math.round(rainTotal / 10);
    const d = Math.round(rainyDaysTotal / 10);
    return { month, t, r, d, tourismScore: calculateTourismScore(t, d) };
  });

  return { months, recent, recentPeriod: range.recentPeriod, baselinePeriod: range.baselinePeriod, endDate: range.endDate };
}

export async function fetchClimateArchive(location: LocationItem, range: ReturnType<typeof getArchiveRange>, signal?: AbortSignal): Promise<ClimateArchive> {
  const params = new URLSearchParams({
    start_date: range.startDate,
    end_date: range.endDate,
  });
  const payload = await requestJson<{ daily: ArchiveDaily }>(
    `/api/locations/${encodeURIComponent(location.slug)}/climate?${params}`,
    { signal },
  );
  return aggregateDaily(payload?.daily, range);
}

export function getHistoryData(location: LocationItem, archive: ClimateArchive) {
  const monthly = archive.recent.map(item => ({
    monthLabel: `Th ${item.month}`,
    month: item.month,
    year: item.year,
    recentRain: item.r,
    historicalAvg: archive.months[item.month - 1].r,
  }));
  const totalRecent = monthly.reduce((sum, item) => sum + item.recentRain, 0);
  const totalHistorical = monthly.reduce((sum, item) => sum + item.historicalAvg, 0);
  const wettest = archive.recent.reduce((best, item) => item.r > best.r ? item : best);
  const hottest = archive.recent.reduce((best, item) => item.t > best.t ? item : best);
  const coolest = archive.recent.reduce((best, item) => item.t < best.t ? item : best);
  const percentDiff = totalHistorical > 0 ? Math.round((totalRecent / totalHistorical - 1) * 100) : 0;
  return {
    location,
    monthly,
    period: archive.recentPeriod,
    baselinePeriod: archive.baselinePeriod,
    totalRecent,
    totalHistorical,
    percentDiff,
    rainComparison: percentDiff > 0
      ? `cao hơn ${percentDiff}%`
      : percentDiff < 0
        ? `thấp hơn ${Math.abs(percentDiff)}%`
        : 'xấp xỉ mức trung bình',
    wettestMonth: { label: formatMonthYear(wettest.year, wettest.month), rain: wettest.r, days: wettest.d },
    highestTempMonth: {
      maxTemp: hottest.t,
      maxLabel: formatMonthYear(hottest.year, hottest.month),
      minTemp: coolest.t,
      minLabel: formatMonthYear(coolest.year, coolest.month),
    },
  };
}
