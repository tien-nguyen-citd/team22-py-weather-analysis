import React, { useState, useMemo } from 'react';
import { keepPreviousData, useQuery } from '@tanstack/react-query';
import { getLocationComparison } from '../api/climateApi';
import { findLocationByName } from '../api/locations';
import { ErrorMessage } from '../components/ErrorMessage';
import { clamp } from '../lib/scoring';
import type { LocationItem } from '../types';

interface ComparePageProps {
  currentLocation: LocationItem;
  locations: LocationItem[];
}

const MONTH_LABELS = [
  'Th 1', 'Th 2', 'Th 3', 'Th 4', 'Th 5', 'Th 6',
  'Th 7', 'Th 8', 'Th 9', 'Th 10', 'Th 11', 'Th 12',
];

export const ComparePage: React.FC<ComparePageProps> = ({
  currentLocation,
  locations,
}) => {
  // Current month (1-12)
  const currentMonthNum = Number(new Intl.DateTimeFormat('en-US', { timeZone: 'Asia/Bangkok', month: 'numeric' }).format(new Date()));
  const [selectedMonth, setSelectedMonth] = useState<number>(currentMonthNum);

  // Compare cities
  const [cityAName, setCityAName] = useState<string>(
    currentLocation.name === 'Hà Nội' ? 'Hà Nội' : currentLocation.name
  );
  const [cityBName, setCityBName] = useState<string>(
    currentLocation.name === 'Đà Lạt' ? 'Hồ Chí Minh' : 'Đà Lạt'
  );

  const cityA = useMemo(
    () => findLocationByName(locations, cityAName) ?? currentLocation,
    [cityAName, currentLocation, locations],
  );
  const cityB = useMemo(
    () => findLocationByName(locations, cityBName) ?? currentLocation,
    [cityBName, currentLocation, locations],
  );

  const comparisonQuery = useQuery({
    queryKey: ['climate', 'compare', cityA.slug, cityB.slug, selectedMonth],
    queryFn: ({ signal }) => getLocationComparison(
      cityA.slug,
      cityB.slug,
      selectedMonth,
      signal,
    ),
    placeholderData: keepPreviousData,
    staleTime: 30 * 60 * 1000,
    retry: 1,
  });

  const controls = (
    <div className="bg-card p-[24px_28px] rounded-[24px] shadow-sh2 flex gap-[14px] items-center justify-between flex-wrap">
        <div className="flex items-center gap-[12px] flex-wrap">
          {/* Select A */}
          <select
            value={cityAName}
            onChange={e => setCityAName(e.target.value)}
            className="border border-border rounded-[12px] bg-tint text-ink p-[10px_14px] text-[15px] font-medium outline-none cursor-pointer focus-ring"
          >
            {locations.map(loc => (
              <option key={loc.slug} value={loc.name}>
                {loc.name}
              </option>
            ))}
          </select>

          <span className="text-[13.5px] text-m3">so với</span>

          {/* Select B */}
          <select
            value={cityBName}
            onChange={e => setCityBName(e.target.value)}
            className="border border-border rounded-[12px] bg-tint text-ink p-[10px_14px] text-[15px] font-medium outline-none cursor-pointer focus-ring"
          >
            {locations.map(loc => (
              <option key={loc.slug} value={loc.name}>
                {loc.name}
              </option>
            ))}
          </select>
        </div>

        {/* 12 Nút Tháng */}
        <div className="flex items-center gap-[4px] flex-wrap">
          {MONTH_LABELS.map((lbl, idx) => {
            const m = idx + 1;
            const isActive = m === selectedMonth;
            return (
              <button
                key={m}
                type="button"
                onClick={() => setSelectedMonth(m)}
                className={`p-[7px_10px] rounded-[9px] text-[12px] transition-all duration-120 cursor-pointer select-none focus-ring ${
                  isActive
                    ? 'bg-acc text-acc-ink font-semibold shadow-xs'
                    : 'bg-tint text-m1 hover:text-ink'
                }`}
              >
                {lbl}
              </button>
            );
          })}
        </div>
    </div>
  );

  const comparison = comparisonQuery.data;
  if (!comparison) {
    return (
      <div className="space-y-[16px] mt-[20px]">
        {controls}
        {comparisonQuery.isError ? (
          <ErrorMessage
            title="Không tải được dữ liệu khí hậu"
            message={
              <>
                Không tải được dữ liệu khí hậu cho{' '}
                <strong>{cityA.name} và {cityB.name}</strong>. Vui lòng kiểm tra
                kết nối mạng và thử lại.
              </>
            }
            onRetry={() => { void comparisonQuery.refetch(); }}
          />
        ) : (
          <div className="space-y-[16px] animate-pulse" aria-label="Đang tải dữ liệu khí hậu">
            <div className="grid grid-cols-1 min-[900px]:grid-cols-2 gap-[16px]">
              <div className="h-[172px] rounded-[24px] bg-acc/60" />
              <div className="h-[172px] rounded-[24px] bg-card shadow-sh2" />
            </div>
            <div className="h-[300px] rounded-[24px] bg-card shadow-sh2" />
            <div className="h-[220px] rounded-[24px] bg-card shadow-sh2" />
          </div>
        )}
      </div>
    );
  }

  const monthsA = comparison.a.months;
  const monthsB = comparison.b.months;
  const currentA = monthsA[selectedMonth - 1];
  const currentB = monthsB[selectedMonth - 1];
  const maxTemp = 34;
  const maxRain = Math.max(120, currentA.rain, currentB.rain);
  const maxDays = 31;
  const scoresA = monthsA.map(m => m.tourismScore);
  const scoresB = monthsB.map(m => m.tourismScore);

  return (
    <div className="space-y-[16px] mt-[20px]">
      {controls}
      {comparisonQuery.isError && (
        <p className="text-[12px] text-m2 px-[4px]">
          Chưa cập nhật được dữ liệu khí hậu; đang hiển thị bản đã lưu.{' '}
          <button type="button" onClick={() => { void comparisonQuery.refetch(); }} className="text-acc underline focus-ring">Thử lại</button>
        </p>
      )}
      <p className="text-[12px] text-m3 px-[4px]">
        Trung bình 10 năm trước ({comparison.baselinePeriod}) · Nguồn: <a href="https://open-meteo.com/en/docs/historical-weather-api" target="_blank" rel="noreferrer" className="underline hover:text-acc focus-ring">Open-Meteo ERA5</a>
      </p>

      {/* Hai thẻ điểm */}
      <div className="grid grid-cols-1 min-[900px]:grid-cols-2 gap-[16px]">
        {/* Thẻ A (nền acc, chữ accInk) */}
        <div className="bg-acc text-acc-ink rounded-[24px] p-[26px_28px] shadow-sh2 flex flex-col justify-between">
          <div>
            <span className="text-[15px] font-medium opacity-90">{cityA.name}</span>
            <div className="flex items-baseline gap-[12px] mt-[6px]">
              <span className="font-nunito font-bold text-[58px] tracking-[-0.035em] leading-none">
                {currentA.tourismScore}
              </span>
              <span className="text-[12.5px] opacity-70">điểm du lịch</span>
            </div>
          </div>
          <p className="text-[13.5px] leading-[1.6] opacity-86 mt-[16px] pretty-text">
            {comparison.a.summary}
          </p>
        </div>

        {/* Thẻ B (nền card, chữ ink) */}
        <div className="bg-card text-ink rounded-[24px] p-[26px_28px] shadow-sh2 flex flex-col justify-between">
          <div>
            <span className="text-[15px] font-medium text-m1">{cityB.name}</span>
            <div className="flex items-baseline gap-[12px] mt-[6px]">
              <span className="font-nunito font-bold text-[58px] tracking-[-0.035em] leading-none text-ink">
                {currentB.tourismScore}
              </span>
              <span className="text-[12.5px] text-m2">điểm du lịch</span>
            </div>
          </div>
          <p className="text-[13.5px] leading-[1.6] text-ink2 mt-[16px] pretty-text">
            {comparison.b.summary}
          </p>
        </div>
      </div>

      {/* Thẻ ba chỉ số so sánh */}
      <div className="bg-card p-[26px_30px_30px] rounded-[24px] shadow-sh2">
        {/* Chỉ số 1: Nhiệt độ trung bình */}
        <div className="py-[16px] border-b border-[var(--track)]">
          <div className="text-[13px] text-m1 font-medium mb-[12px]">
            Nhiệt độ trung bình <span className="text-m4 font-normal">· °C</span>
          </div>

          <div className="space-y-[8px]">
            <div className="flex items-center gap-[12px]">
              <span className="w-[104px] text-[13px] text-m1 truncate">{cityA.name}</span>
              <div className="flex-1 h-[16px] rounded-[8px] bg-track overflow-hidden">
                <div
                  style={{ width: `${clamp((currentA.temperature / maxTemp) * 100, 3, 100)}%` }}
                  className="h-full bg-acc rounded-[8px] transition-all duration-300"
                />
              </div>
              <span className="w-[66px] text-right font-nunito font-semibold text-[16px] text-ink">
                {currentA.temperature}°C
              </span>
            </div>

            <div className="flex items-center gap-[12px]">
              <span className="w-[104px] text-[13px] text-m1 truncate">{cityB.name}</span>
              <div className="flex-1 h-[16px] rounded-[8px] bg-track overflow-hidden">
                <div
                  style={{ width: `${clamp((currentB.temperature / maxTemp) * 100, 3, 100)}%` }}
                  className="h-full bg-dim rounded-[8px] transition-all duration-300"
                />
              </div>
              <span className="w-[66px] text-right font-nunito font-semibold text-[16px] text-ink">
                {currentB.temperature}°C
              </span>
            </div>
          </div>
        </div>

        {/* Chỉ số 2: Lượng mưa cả tháng */}
        <div className="py-[16px] border-b border-[var(--track)]">
          <div className="text-[13px] text-m1 font-medium mb-[12px]">
            Lượng mưa cả tháng <span className="text-m4 font-normal">· mm</span>
          </div>

          <div className="space-y-[8px]">
            <div className="flex items-center gap-[12px]">
              <span className="w-[104px] text-[13px] text-m1 truncate">{cityA.name}</span>
              <div className="flex-1 h-[16px] rounded-[8px] bg-track overflow-hidden">
                <div
                  style={{ width: `${clamp((currentA.rain / maxRain) * 100, 3, 100)}%` }}
                  className="h-full bg-acc rounded-[8px] transition-all duration-300"
                />
              </div>
              <span className="w-[66px] text-right font-nunito font-semibold text-[16px] text-ink">
                {currentA.rain} mm
              </span>
            </div>

            <div className="flex items-center gap-[12px]">
              <span className="w-[104px] text-[13px] text-m1 truncate">{cityB.name}</span>
              <div className="flex-1 h-[16px] rounded-[8px] bg-track overflow-hidden">
                <div
                  style={{ width: `${clamp((currentB.rain / maxRain) * 100, 3, 100)}%` }}
                  className="h-full bg-dim rounded-[8px] transition-all duration-300"
                />
              </div>
              <span className="w-[66px] text-right font-nunito font-semibold text-[16px] text-ink">
                {currentB.rain} mm
              </span>
            </div>
          </div>
        </div>

        {/* Chỉ số 3: Số ngày có mưa */}
        <div className="py-[16px] border-b border-[var(--track)]">
          <div className="text-[13px] text-m1 font-medium mb-[12px]">
            Số ngày có mưa <span className="text-m4 font-normal">· ngày</span>
          </div>

          <div className="space-y-[8px]">
            <div className="flex items-center gap-[12px]">
              <span className="w-[104px] text-[13px] text-m1 truncate">{cityA.name}</span>
              <div className="flex-1 h-[16px] rounded-[8px] bg-track overflow-hidden">
                <div
                  style={{ width: `${clamp((currentA.rainyDays / maxDays) * 100, 3, 100)}%` }}
                  className="h-full bg-acc rounded-[8px] transition-all duration-300"
                />
              </div>
              <span className="w-[66px] text-right font-nunito font-semibold text-[16px] text-ink">
                {currentA.rainyDays} ngày
              </span>
            </div>

            <div className="flex items-center gap-[12px]">
              <span className="w-[104px] text-[13px] text-m1 truncate">{cityB.name}</span>
              <div className="flex-1 h-[16px] rounded-[8px] bg-track overflow-hidden">
                <div
                  style={{ width: `${clamp((currentB.rainyDays / maxDays) * 100, 3, 100)}%` }}
                  className="h-full bg-dim rounded-[8px] transition-all duration-300"
                />
              </div>
              <span className="w-[66px] text-right font-nunito font-semibold text-[16px] text-ink">
                {currentB.rainyDays} ngày
              </span>
            </div>
          </div>
        </div>

        {/* Kết luận so sánh */}
        <p className="text-[14.5px] text-ink2 leading-[1.65] mt-[20px] pretty-text">
          {comparison.conclusion}
        </p>
      </div>

      {/* Thẻ Điểm du lịch cả năm */}
      <div className="bg-card p-[26px_30px_28px] rounded-[24px] shadow-sh2">
        <div className="flex items-baseline justify-between">
          <h4 className="font-nunito font-semibold text-[15px] text-ink">
            Điểm du lịch cả năm
          </h4>
          <span className="text-[12px] text-m3">bấm vào tháng để xem chi tiết</span>
        </div>

        {/* 12 Tháng cột đôi */}
        <div className="overflow-x-auto pb-2 mt-[20px]">
          <div className="flex items-end justify-between gap-[6px] min-w-[560px]">
            {MONTH_LABELS.map((lbl, idx) => {
              const m = idx + 1;
              const isSelected = m === selectedMonth;
              const scoreA = scoresA[idx];
              const scoreB = scoresB[idx];
              const hA = clamp(scoreA * 0.62, 5, 62);
              const hB = clamp(scoreB * 0.62, 5, 62);

              return (
                <button
                  key={m}
                  type="button"
                  onClick={() => setSelectedMonth(m)}
                  className="flex-1 flex flex-col items-center gap-[6px] group cursor-pointer focus-ring rounded-[6px] p-1"
                >
                  <div className="flex items-end gap-[2px] h-[64px]">
                    <div
                      style={{
                        height: `${hA}px`,
                        opacity: isSelected ? 1 : 0.5,
                      }}
                      className="w-[12px] bg-acc rounded-t-[3px] transition-all duration-150"
                      title={`${cityA.name} ${lbl}: ${scoreA}đ`}
                    />
                    <div
                      style={{
                        height: `${hB}px`,
                        opacity: isSelected ? 1 : 0.65,
                      }}
                      className="w-[12px] bg-dim rounded-t-[3px] transition-all duration-150"
                      title={`${cityB.name} ${lbl}: ${scoreB}đ`}
                    />
                  </div>
                  <span
                    className={`text-[11px] font-nunito ${
                      isSelected ? 'text-acc font-bold' : 'text-m3 group-hover:text-ink'
                    }`}
                  >
                    {lbl}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Chú giải cột */}
        <div className="flex items-center gap-[20px] text-[12px] text-m1 mt-[16px] pt-[12px] border-t border-border">
          <div className="flex items-center gap-[6px]">
            <span className="w-[10px] h-[10px] rounded-[2px] bg-acc inline-block" />
            <span>{cityA.name}</span>
          </div>
          <div className="flex items-center gap-[6px]">
            <span className="w-[10px] h-[10px] rounded-[2px] bg-dim inline-block" />
            <span>{cityB.name}</span>
          </div>
        </div>

        {/* Câu khuyến nghị */}
        <p className="text-[14px] text-ink2 leading-[1.65] mt-[16px] pretty-text">
          {comparison.yearRecommendation}
        </p>
      </div>
    </div>
  );
};
