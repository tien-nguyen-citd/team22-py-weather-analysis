import { useState } from 'react';
import { ArrowDownRight, CalendarDays, CloudRain, Thermometer, Trophy } from 'lucide-react';
import type { ActivityProfile, Advice, AdvisoryCandidate } from '../api/advisory';
import {
  formatAdvisoryDate as dateLabel,
  formatAdvisoryNumber as number,
  formatMonthOnlyLabel,
  sortCandidatesByMonth,
} from '../lib/advisory';

interface AdvisoryResultsProps {
  advice: Advice;
  locationName: string;
  onExploreMonth: (month: string) => void;
}

export function CandidateEvidence({ candidate, activity }: { candidate: AdvisoryCandidate; activity: ActivityProfile }) {
  return (
    <div className="space-y-3 text-sm leading-relaxed">
      <p>{candidate.explanation}</p>
      <dl className="grid gap-2 sm:grid-cols-2">
        <div className="rounded-xl border border-current/20 p-3">
          <dt>Ít mưa · {number(activity.rainWeight * 100)}% trọng số</dt>
          <dd className="mt-1 font-semibold">{number(candidate.rainScore)} × {number(activity.rainWeight * 100)}% = {number(candidate.rainContribution)} điểm</dd>
        </div>
        <div className="rounded-xl border border-current/20 p-3">
          <dt>Nhiệt độ · {number(activity.temperatureWeight * 100)}% trọng số</dt>
          <dd className="mt-1 font-semibold">{candidate.temperatureScore === null
            ? 'Không chấm cho hoạt động này'
            : `${number(candidate.temperatureScore)} × ${number(activity.temperatureWeight * 100)}% = ${number(candidate.temperatureContribution)} điểm`}</dd>
        </div>
      </dl>
      <p>{candidate.sampleDays.toLocaleString('vi-VN')} ngày trong {candidate.sampleYears} năm. Điểm phù hợp không phải xác suất thời tiết tương lai.</p>
    </div>
  );
}

function CandidateCard({ candidate, activity, primary, onExploreMonth }: {
  candidate: AdvisoryCandidate;
  activity: ActivityProfile;
  primary: boolean;
  onExploreMonth: (month: string) => void;
}) {
  return (
    <article aria-label={`${primary ? 'Đề xuất chính' : 'Lựa chọn thay thế'}: ${candidate.window.label}`}
      className={`flex h-full min-w-0 flex-col rounded-[24px] p-6 sm:p-7 shadow-sh2 ${primary ? 'bg-acc text-acc-ink' : 'bg-card text-ink'}`}>
      <div className="flex items-center justify-between gap-3 text-sm font-semibold">
        <span className="inline-flex items-center gap-2">{primary ? <Trophy size={17} aria-hidden="true" /> : <CalendarDays size={17} aria-hidden="true" />}{primary ? 'Đề xuất chính' : 'Lựa chọn thay thế'}</span>
        <span>{number(candidate.score)}<span className="font-normal"> / 100 điểm</span></span>
      </div>
      <h3 className="mt-4 font-nunito text-3xl font-bold">{candidate.window.label}</h3>
      <p className="mt-1 text-sm">
        {dateLabel(candidate.window.startDate)} – {dateLabel(candidate.window.endDate)}
        {candidate.similarToBest && <span className="font-semibold"> · Gần tương đương đề xuất chính</span>}
      </p>
      <dl className="mt-5 grid grid-cols-2 gap-3">
        <div className={`rounded-2xl p-3 ${primary ? 'bg-white/10' : 'bg-tint'}`}>
          <dt className="flex items-center gap-1 text-xs"><Thermometer size={14} aria-hidden="true" />Nhiệt độ TB ngày</dt>
          <dd className="mt-1 font-nunito text-2xl font-bold">{number(candidate.temperatureMean)}°C</dd>
        </div>
        <div className={`rounded-2xl p-3 ${primary ? 'bg-white/10' : 'bg-tint'}`}>
          <dt className="flex items-center gap-1 text-xs"><CloudRain size={14} aria-hidden="true" />Ngày mưa ≥ {number(activity.rainThresholdMm)} mm</dt>
          <dd className="mt-1 font-nunito text-2xl font-bold">{number(candidate.rainyDayPercentage)}%</dd>
        </div>
      </dl>
      <details className="mt-5 border-t border-current/20 pt-4">
        <summary className="focus-ring cursor-pointer rounded text-sm font-semibold">Vì sao chọn?</summary>
        <div className="mt-3"><CandidateEvidence candidate={candidate} activity={activity} /></div>
      </details>
      {candidate.window.resolution === 'month' && (
        <div className="mt-auto pt-4">
          <button type="button" onClick={() => onExploreMonth(candidate.window.startDate.slice(0, 7))}
            className={`focus-ring inline-flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-semibold ${primary ? 'bg-white text-acc' : 'bg-acc-soft text-acc'}`}>
            Xem giai đoạn trong tháng này <ArrowDownRight size={16} aria-hidden="true" />
          </button>
        </div>
      )}
    </article>
  );
}

export function AdvisoryResults({ advice, locationName, onExploreMonth }: AdvisoryResultsProps) {
  const best = advice.recommendations[0];
  const [selectedDate, setSelectedDate] = useState(best?.window.startDate);
  const selected = advice.candidates.find(item => item.window.startDate === selectedDate) ?? best;
  // Biểu đồ xếp theo tháng 1 → 12 và bỏ năm để dễ dò theo lịch.
  const monthOrderedCandidates = sortCandidatesByMonth(advice.candidates);

  if (!best || !selected) return <p role="status">Chưa có thời điểm để đề xuất trong khoảng đã chọn.</p>;

  return (
    <section aria-label="Kết quả tư vấn" className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-acc">{advice.activity.name} · {locationName}</p>
          <h2 className="mt-1 font-nunito text-2xl font-bold">Những thời điểm đáng cân nhắc</h2>
        </div>
        <p className="text-xs text-m1">Lịch sử {dateLabel(advice.baselineStart)} – {dateLabel(advice.baselineEnd)}</p>
      </div>
      <p className={`rounded-2xl px-4 py-3 text-sm leading-relaxed ${advice.lowSuitability ? 'border border-amber-300 bg-amber-50 text-amber-900' : 'bg-acc-soft text-ink2'}`}>
        {advice.summary}
      </p>
      <p className="text-sm text-m1">Tham khảo từ lịch sử khí hậu, không phải dự báo cho ngày cụ thể.</p>
      <div className="grid gap-4 sm:grid-cols-2">
        {advice.recommendations.slice(0, 2).map(candidate => (
          <CandidateCard key={candidate.window.startDate} candidate={candidate} activity={advice.activity}
            primary={candidate === best} onExploreMonth={onExploreMonth} />
        ))}
      </div>
      <section aria-label="So sánh các thời điểm" className="min-w-0 rounded-[24px] bg-card p-5 shadow-sh2 sm:p-7">
        <h3 className="font-nunito text-xl font-bold">Cả khoảng thời gian, trong một cái nhìn</h3>
        <p className="mt-1 text-sm text-m1">Điểm càng cao càng phù hợp với tiêu chí. Chọn một cột để xem số liệu; có thể dùng phím Tab và Enter.</p>
        <div className="mt-5 overflow-x-auto pb-3">
          <div className="flex min-w-max gap-2">
            {monthOrderedCandidates.map(candidate => {
              const active = candidate.window.startDate === selected.window.startDate;
              const label = formatMonthOnlyLabel(candidate.window);
              return (
                <button key={candidate.window.startDate} type="button" aria-pressed={active}
                  aria-label={`${label}: ${number(candidate.score)} điểm`}
                  onClick={() => setSelectedDate(candidate.window.startDate)}
                  className={`focus-ring flex w-[76px] shrink-0 flex-col rounded-xl border p-2 text-center ${active ? 'border-acc bg-acc-soft' : 'border-transparent hover:bg-tint'}`}>
                  <span className="text-sm font-bold text-ink">{number(candidate.score)}</span>
                  <span className="my-2 flex h-28 w-full items-end rounded bg-track/40" aria-hidden="true">
                    <span className={`w-full rounded ${candidate.rank === 1 ? 'bg-acc' : 'bg-mid'}`} style={{ height: `${Math.max(2, candidate.score)}%` }} />
                  </span>
                  <span className="text-xs leading-5 text-ink2">{label}</span>
                </button>
              );
            })}
          </div>
        </div>
        <div aria-live="polite" aria-atomic="true" className="mt-3 rounded-2xl bg-tint p-4 sm:p-5">
          <h4 className="mb-3 font-semibold">{formatMonthOnlyLabel(selected.window)} · Hạng {selected.rank}/{advice.candidates.length}</h4>
          <CandidateEvidence candidate={selected} activity={advice.activity} />
        </div>
      </section>
      <details open className="rounded-2xl border border-border p-4 text-sm text-m1">
        <summary className="focus-ring cursor-pointer rounded font-semibold text-ink2">Hiểu đúng kết quả</summary>
        <ul className="mt-3 list-disc space-y-2 pl-5">{advice.notes.map(note => <li key={note}>{note}</li>)}</ul>
      </details>
    </section>
  );
}
