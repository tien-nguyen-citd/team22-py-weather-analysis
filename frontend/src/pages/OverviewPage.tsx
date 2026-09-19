import React, { useState } from "react";
import type { LocationForecast } from "../api/forecast";
import { getScoreColor, getFactorColor } from "../lib/scoring";

interface OverviewPageProps {
  data: LocationForecast;
}

export const OverviewPage: React.FC<OverviewPageProps> = ({ data }) => {
  const [showWeekForecast, setShowWeekForecast] = useState(true);

  return (
    <div className="space-y-[16px] mt-[20px]">
      {/* Row 1: Current Weather & Verdict + Hourly Scores */}
      <div className="grid grid-cols-1 min-[900px]:grid-cols-[minmax(0,1fr)_minmax(0,1.25fr)] gap-[16px]">
        {/* Left: Thẻ hiện tại */}
        <div className="bg-card rounded-[24px] p-[30px_32px_32px] shadow-sh2 flex flex-col justify-between">
          <div>
            <div className="flex items-baseline gap-[9px]">
              <h2 className="text-[16px] font-semibold text-ink">
                {data.location.name}
              </h2>
              <span className="text-[12px] text-m3">
                {data.location.regionLabel}
              </span>
            </div>

            <div className="font-nunito font-light text-[104px] leading-[0.9] tracking-[-0.045em] mt-[8px] text-ink select-none">
              {data.tempNow}°
            </div>

            <p className="text-[16.5px] leading-[1.4] text-ink font-medium mt-[6px]">
              {data.conditionDesc}
            </p>

            <p className="text-[13px] text-m2 mt-[4px]">
              cảm giác như {data.apparentTempNow}° · cao {data.tempMax}° / thấp{" "}
              {data.tempMin}°
            </p>
          </div>

          {/* 4 Ô metric phụ */}
          <div className="grid grid-cols-2 gap-[10px] mt-[26px]">
            <div className="bg-tint rounded-[16px] p-[14px_16px]">
              <span className="block uppercase text-[11px] text-m3 tracking-[0.09em] font-medium">
                Độ ẩm
              </span>
              <span className="font-nunito font-semibold text-[23px] text-ink mt-[2px] block">
                {data.humidityNow}%
              </span>
            </div>
            <div className="bg-tint rounded-[16px] p-[14px_16px]">
              <span className="block uppercase text-[11px] text-m3 tracking-[0.09em] font-medium">
                Gió
              </span>
              <span className="font-nunito font-semibold text-[23px] text-ink mt-[2px] block">
                {data.windNow}{" "}
                <span className="text-[15px] font-normal text-m2">km/h</span>
              </span>
            </div>
            <div className="bg-tint rounded-[16px] p-[14px_16px]">
              <span className="block uppercase text-[11px] text-m3 tracking-[0.09em] font-medium">
                Khả năng mưa
              </span>
              <span className="font-nunito font-semibold text-[23px] text-ink mt-[2px] block">
                {data.rainProbNow}%
              </span>
            </div>
            <div className="bg-tint rounded-[16px] p-[14px_16px]">
              <span className="block uppercase text-[11px] text-m3 tracking-[0.09em] font-medium">
                Chỉ số UV
              </span>
              <span className="font-nunito font-semibold text-[23px] text-ink mt-[2px] block">
                {data.uvNow}
              </span>
            </div>
          </div>
        </div>

        {/* Right Column: Verdict card + Hourly bar chart */}
        <div className="flex flex-col gap-[16px]">
          {/* Thẻ nhận định */}
          <div className="bg-acc text-white rounded-[24px] p-[28px_30px] shadow-sh2">
            <div className="flex items-center justify-between gap-[12px]">
              <span className="text-[12.5px] opacity-90 font-medium">
                Nhận định trong ngày
              </span>
              <div className="h-[1px] bg-[var(--accLine)] flex-1" />
              <div className="font-nunito font-bold text-[15px]">
                {data.dayScore}
                <span className="text-[11.5px] opacity-75 font-normal">
                  /100
                </span>
              </div>
            </div>

            <h3 className="font-nunito font-semibold text-[24px] leading-[1.32] mt-[14px] pretty-text">
              {data.verdict}
            </h3>

            <p className="text-[13.5px] leading-[1.6] opacity-90 pretty-text mt-[8px]">
              {data.why}
            </p>

            {/* Hai khung giờ tốt nhất */}
            <div className="flex items-start gap-[28px] mt-[22px] flex-wrap">
              {data.bestWindows.length === 0 ? (
                <p className="text-[13.5px] opacity-90">
                  Hôm nay không còn khung giờ phù hợp
                </p>
              ) : (
                data.bestWindows.map((win) => (
                  <div key={win.range} className="space-y-[2px]">
                    <span className="block uppercase text-[11px] opacity-75 tracking-[0.05em] font-medium">
                      {win.tag}
                    </span>
                    <span className="font-nunito text-[24px] block font-normal">
                      {win.range}
                    </span>
                    <span className="block text-[12px] opacity-85">
                      {win.score} / 100 · {win.note}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Thẻ điểm theo giờ */}
          <div className="bg-card rounded-[24px] p-[26px_28px_24px] shadow-sh2 flex-1 flex flex-col justify-between">
            <div>
              <div className="flex items-baseline justify-between">
                <h4 className="font-nunito font-semibold text-[15px] text-ink">
                  Điểm thuận lợi theo giờ
                </h4>
                <span className="text-[12px] text-m3">0 – 100</span>
              </div>

              {/* 24 cột biểu đồ */}
              <div className="overflow-x-auto pb-1 mt-[20px]">
                <div className="min-w-[560px] min-[900px]:min-w-0">
                  <div className="flex items-end gap-[4px] h-[120px]">
                    {data.hourly.map((h) => {
                      const barHeight = 10 + h.score * 1.05;
                      const barColor = getScoreColor(h.hour, h.score);
                      return (
                        <div
                          key={h.hour}
                          className="flex-1 flex flex-col items-center justify-end h-full group relative"
                        >
                          {/* Tooltip on hover */}
                          <div className="absolute -top-7 hidden group-hover:flex bg-ink text-card text-[11px] py-0.5 px-1.5 rounded whitespace-nowrap z-20 pointer-events-none">
                            {String(h.hour).padStart(2, "0")}:00 · {h.score}đ ·{" "}
                            {h.temp}°C
                          </div>
                          <div
                            style={{
                              height: `${barHeight}px`,
                              backgroundColor: barColor,
                            }}
                            className="w-full rounded-[5px] transition-all duration-200"
                          />
                        </div>
                      );
                    })}
                  </div>

                  {/* Trục giờ */}
                  <div className="flex justify-between text-[11px] text-m3 mt-[9px]">
                    <span>00:00</span>
                    <span>06:00</span>
                    <span>12:00</span>
                    <span>18:00</span>
                    <span>23:00</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Chú giải */}
            <div className="flex items-center gap-[16px] text-[11.5px] text-m1 mt-[14px] flex-wrap">
              <div className="flex items-center gap-[6px]">
                <span className="w-[9px] h-[9px] rounded-[3px] bg-acc inline-block" />
                <span>Rất tốt</span>
              </div>
              <div className="flex items-center gap-[6px]">
                <span className="w-[9px] h-[9px] rounded-[3px] bg-mid inline-block" />
                <span>Tạm được</span>
              </div>
              <div className="flex items-center gap-[6px]">
                <span className="w-[9px] h-[9px] rounded-[3px] bg-dim inline-block" />
                <span>Nên ở trong nhà</span>
              </div>
              <div className="flex items-center gap-[6px]">
                <span className="w-[9px] h-[9px] rounded-[3px] bg-night inline-block" />
                <span>Ban đêm, ngoài giờ tính điểm</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Row 2: Điểm đến từ đâu & Chi tiết trong ngày */}
      <div className="grid grid-cols-1 min-[900px]:grid-cols-[minmax(0,1fr)_minmax(0,1.25fr)] gap-[16px] mt-[16px]">
        {/* Điểm N đến từ đâu */}
        <div className="bg-card rounded-[24px] p-[26px_28px] shadow-sh2">
          <div className="flex items-baseline justify-between">
            <h4 className="font-nunito font-semibold text-[15px] text-ink">
              Các yếu tố thời tiết lúc này
            </h4>
          </div>
          <p className="text-[12.5px] text-m2 mt-[2px]">
            Tham khảo thêm bên cạnh điểm trung bình từ 06:00 đến 17:59
          </p>

          <div className="space-y-[14px] mt-[20px]">
            {data.factors.map((f) => {
              const barColor = getFactorColor(f.value);
              return (
                <div key={f.label} className="space-y-[6px]">
                  <div className="flex justify-between items-baseline text-[13px]">
                    <span className="font-medium text-ink">{f.label}</span>
                    <span className="text-[12px] text-m2">{f.note}</span>
                  </div>
                  <div className="h-[8px] rounded-[4px] bg-track overflow-hidden w-full">
                    <div
                      style={{
                        width: `${f.value}%`,
                        backgroundColor: barColor,
                      }}
                      className="h-full rounded-[4px] transition-all duration-300"
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Chi tiết trong ngày */}
        <div className="bg-card rounded-[24px] p-[26px_28px] shadow-sh2 flex flex-col justify-between">
          <div>
            <h4 className="font-nunito font-semibold text-[15px] text-ink">
              Chi tiết trong ngày
            </h4>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-x-[20px] gap-y-[18px] mt-[20px]">
              <div>
                <span className="block uppercase text-[11px] text-m3 tracking-[0.09em] font-medium">
                  Mặt trời mọc
                </span>
                <span className="font-nunito font-semibold text-[20px] text-ink mt-[2px] block">
                  {data.details.sunrise}
                </span>
              </div>

              <div>
                <span className="block uppercase text-[11px] text-m3 tracking-[0.09em] font-medium">
                  Mặt trời lặn
                </span>
                <span className="font-nunito font-semibold text-[20px] text-ink mt-[2px] block">
                  {data.details.sunset}
                </span>
              </div>

              <div>
                <span className="block uppercase text-[11px] text-m3 tracking-[0.09em] font-medium">
                  Giờ có nắng
                </span>
                <span className="font-nunito font-semibold text-[20px] text-ink mt-[2px] block">
                  {data.details.sunshineHours === null
                    ? "—"
                    : `${data.details.sunshineHours}h`}
                </span>
              </div>

              <div>
                <span className="block uppercase text-[11px] text-m3 tracking-[0.09em] font-medium">
                  Không khí (AQI)
                </span>
                <div className="flex items-baseline gap-[6px] mt-[2px]">
                  <span className="font-nunito font-semibold text-[20px] text-ink">
                    {data.details.aqi ?? "—"}
                  </span>
                  <span className="text-[12.5px] text-m2">
                    {data.details.aqiLabel ?? "Không có dữ liệu"}
                  </span>
                </div>
              </div>

              <div>
                <span className="block uppercase text-[11px] text-m3 tracking-[0.09em] font-medium">
                  Mưa dự kiến
                </span>
                <span className="font-nunito font-semibold text-[20px] text-ink mt-[2px] block">
                  {data.details.rainSum}{" "}
                  <span className="text-[14px] font-normal text-m2">mm</span>
                </span>
              </div>

              <div>
                <span className="block uppercase text-[11px] text-m3 tracking-[0.09em] font-medium">
                  Khung giờ mưa
                </span>
                <span className="font-nunito font-semibold text-[20px] text-ink mt-[2px] block">
                  {data.details.rainWindow}
                </span>
              </div>
            </div>
          </div>

          <div className="text-[12.5px] text-m2 leading-[1.55] mt-[22px] border-t border-border pt-[14px]">
            Điểm sương {data.details.dewPoint}° · {data.location.regionLabel} ·
            số liệu từ Open-Meteo, cập nhật mỗi giờ
          </div>
        </div>
      </div>

      {/* Row 3: Dự báo 7 ngày */}
      <div className="mt-[16px]">
        <div className="flex items-center justify-between mb-[10px]">
          <h4 className="font-nunito font-semibold text-[15px] text-ink">
            Dự báo 7 ngày tới
          </h4>
          <button
            type="button"
            onClick={() => setShowWeekForecast(!showWeekForecast)}
            className="text-[12px] text-m1 hover:text-acc transition-colors cursor-pointer"
          >
            {showWeekForecast ? "Thu gọn" : "Mở rộng"}
          </button>
        </div>

        {showWeekForecast && (
          <div className="grid grid-cols-2 sm:grid-cols-4 min-[900px]:grid-cols-7 gap-[12px]">
            {data.daily7.map((day, idx) => (
              <div
                key={day.date}
                className={`bg-card rounded-[18px] p-[18px_14px_16px] shadow-sh2 text-center flex flex-col justify-between ${
                  idx === 0 ? "border border-acc-soft" : ""
                }`}
              >
                <span className="text-[12.5px] text-m1 block font-medium">
                  {day.dayLabel}
                </span>

                <div className="my-[10px]">
                  <span className="font-nunito font-semibold text-[24px] text-ink block leading-none">
                    {day.tempMax}°
                  </span>
                  <span className="text-[12px] text-m3 block mt-[4px]">
                    {day.tempMin}°
                  </span>
                </div>

                <div>
                  <div className="h-[5px] rounded-[3px] bg-track overflow-hidden w-full mb-[6px]">
                    <div
                      style={{ width: `${Math.min(100, day.rainProb)}%` }}
                      className="h-full bg-acc rounded-[3px]"
                    />
                  </div>
                  <span className="text-[11px] text-m2 font-medium">
                    {day.rainProb}% mưa
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
