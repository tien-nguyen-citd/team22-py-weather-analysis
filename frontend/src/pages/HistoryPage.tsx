import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { getLocationHistory } from '../api/climateApi';
import { ErrorMessage } from '../components/ErrorMessage';
import { HistoryPageFooter } from '../components/HistoryPageFooter';
import { clamp } from '../lib/scoring';
import type { LocationItem } from '../types';

interface HistoryPageProps {
  currentLocation: LocationItem;
}

export const HistoryPage: React.FC<HistoryPageProps> = ({ currentLocation }) => {
  const { data: history, isError, refetch } = useQuery({
    queryKey: ['climate', 'history', currentLocation.slug],
    queryFn: ({ signal }) => getLocationHistory(currentLocation.slug, signal),
    staleTime: 30 * 60 * 1000,
    retry: 1,
  });

  if (!history) {
    if (isError) {
      return (
        <ErrorMessage
          title="Không tải được dữ liệu lịch sử"
          message={
            <>
              Không tải được dữ liệu lịch sử cho{' '}
              <strong>{currentLocation.name}</strong>. Vui lòng kiểm tra kết
              nối mạng và thử lại.
            </>
          }
          onRetry={() => { void refetch(); }}
        />
      );
    }
    return (
      <div className="grid grid-cols-1 min-[900px]:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)] gap-[16px] mt-[20px] animate-pulse" aria-label="Đang tải dữ liệu lịch sử">
        <div className="h-[370px] rounded-[24px] bg-card shadow-sh2" />
        <div className="space-y-[12px]">
          {[0, 1, 2].map(index => <div key={index} className="h-[116px] rounded-[20px] bg-card shadow-sh2" />)}
        </div>
      </div>
    );
  }

  // Tìm maxRain của cả 2 series để tính tỉ lệ cột
  const maxMm = Math.max(100, ...history.months.flatMap(m => [m.rain, m.baselineRain]));

  const diffSign = history.rainDiffPercent > 0 ? `+${history.rainDiffPercent}%` : `${history.rainDiffPercent}%`;

  return (
    <div className="space-y-[16px] mt-[20px]">
      <div className="grid grid-cols-1 min-[900px]:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)] gap-[16px]">
        {/* Cột trái: Thẻ biểu đồ lượng mưa */}
        <div className="bg-card rounded-[24px] p-[28px_30px] shadow-sh2 flex flex-col justify-between">
          <div>
            {isError && (
              <p className="text-[12px] text-m2 mb-[12px]">
                Chưa cập nhật được dữ liệu lịch sử; đang hiển thị bản đã lưu.{' '}
                <button type="button" onClick={() => { void refetch(); }} className="text-acc underline focus-ring">Thử lại</button>
              </p>
            )}
            <h2 className="font-nunito font-bold text-[20px] text-ink">
              Lượng mưa 12 tháng trọn vẹn gần nhất · {currentLocation.name}
            </h2>
            <p className="text-[12px] text-m3 mt-[4px]">
              {history.recentPeriod} · Trung bình 10 năm trước ({history.baselinePeriod})
            </p>

            {/* 12 nhóm cột đôi */}
            <div className="overflow-x-auto pb-2 mt-[26px]">
              <div className="flex items-end justify-between gap-[9px] h-[210px] min-w-[560px]">
                {history.months.map(m => {
                  // Công thức tính từ spec SCORING.md:
                  // clamp(mm / (maxMm * 1.35) * 150, 3, 150) * 1.1
                  const hRecent = clamp((m.rain / (maxMm * 1.35)) * 150, 3, 150) * 1.1;
                  const hHistorical = clamp((m.baselineRain / (maxMm * 1.35)) * 150, 3, 150) * 1.1;

                  return (
                    <div
                      key={`${m.year}-${m.month}`}
                      className="flex-1 flex flex-col items-center justify-end h-full gap-[8px] group"
                    >
                      <div className="flex items-end gap-[3px] w-full justify-center h-[165px]">
                        {/* Cột Trung bình nhiều năm (dim) */}
                        <div
                          style={{ height: `${hHistorical}px` }}
                          className="w-[12px] bg-dim rounded-t-[5px] transition-all duration-200"
                          title={`Trung bình 10 năm của Th ${m.month}: ${m.baselineRain} mm`}
                        />
                        {/* Cột 12 tháng qua (acc) */}
                        <div
                          style={{ height: `${hRecent}px` }}
                          className="w-[12px] bg-acc rounded-t-[5px] transition-all duration-200"
                          title={`Th ${m.month}/${m.year}: ${m.rain} mm`}
                        />
                      </div>

                      <span className="text-[10.5px] text-m3 font-nunito leading-none">
                        Th {m.month}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Chú giải */}
          <div className="flex items-center gap-[20px] text-[12.5px] text-m1 mt-[18px] pt-[14px] border-t border-border">
            <div className="flex items-center gap-[7px]">
              <span className="w-[10px] h-[10px] rounded-[3px] bg-acc inline-block" />
              <span>12 tháng gần nhất</span>
            </div>
            <div className="flex items-center gap-[7px]">
              <span className="w-[10px] h-[10px] rounded-[3px] bg-dim inline-block" />
              <span>Trung bình 10 năm</span>
            </div>
          </div>
        </div>

        {/* Cột phải: Ba thẻ insight */}
        <div className="flex flex-col gap-[12px]">
          {/* Insight 1: Tổng lượng mưa so sánh */}
          <div className="bg-card rounded-[20px] p-[22px_24px] shadow-sh2 flex-1 flex flex-col justify-center">
            <span className="font-nunito font-bold text-[30px] text-acc tracking-[-0.02em] leading-tight">
              {diffSign}
            </span>
            <p className="text-[14px] text-ink2 leading-[1.55] mt-[6px] pretty-text">
              Tổng {history.totalRain.toLocaleString('vi-VN')} mm, {history.rainComparison} so với mức trung bình {history.baselineTotalRain.toLocaleString('vi-VN')} mm của cùng 12 tháng trong 10 năm trước.
            </p>
          </div>

          {/* Insight 2: Tháng mưa nhiều nhất */}
          <div className="bg-card rounded-[20px] p-[22px_24px] shadow-sh2 flex-1 flex flex-col justify-center">
            <span className="font-nunito font-bold text-[30px] text-acc tracking-[-0.02em] leading-tight">
              {history.wettestMonth.label}
            </span>
            <p className="text-[14px] text-ink2 leading-[1.55] mt-[6px] pretty-text">
              Tháng mưa nhiều nhất trong giai đoạn: {history.wettestMonth.rain} mm và {history.wettestMonth.rainyDays} ngày có mưa (từ 1 mm).
            </p>
          </div>

          {/* Insight 3: Nhiệt độ trung bình cao nhất/thấp nhất */}
          <div className="bg-card rounded-[20px] p-[22px_24px] shadow-sh2 flex-1 flex flex-col justify-center">
            <span className="font-nunito font-bold text-[30px] text-acc tracking-[-0.02em] leading-tight">
              {history.hottestMonth.temperature}°C
            </span>
            <p className="text-[14px] text-ink2 leading-[1.55] mt-[6px] pretty-text">
              Nhiệt độ trung bình tháng cao nhất vào {history.hottestMonth.label}; thấp nhất là {history.coolestMonth.temperature}°C vào {history.coolestMonth.label}.
            </p>
          </div>
        </div>
      </div>

      <HistoryPageFooter />
    </div>
  );
};
