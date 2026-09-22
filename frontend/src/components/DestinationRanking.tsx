import { keepPreviousData, useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import {
  AlertTriangle,
  ArrowUpRight,
  ChevronRight,
  CloudRain,
  LoaderCircle,
  Medal,
  Sparkles,
  Thermometer,
  Trophy,
} from 'lucide-react';
import type { ActivityProfile } from '../api/advisory';
import { getDestinationRanking, type DestinationResult } from '../api/destinations';
import { formatAdvisoryDate as dateLabel, formatAdvisoryNumber as number } from '../lib/advisory';
import { formatMonthTitle } from '../lib/destinations';
import { pagePath, type ViewedLocationState } from '../lib/routes';
import { getFactorColor } from '../lib/scoring';
import { CandidateEvidence } from './AdvisoryResults';
import { ErrorMessage } from './ErrorMessage';

interface DestinationRankingProps {
  month: string;
  activityId: string;
}

// Hàng của bảng xếp hạng. Trên màn hình hẹp, thanh điểm xuống dòng thứ hai,
// nhiệt độ và ngày mưa chuyển vào dưới tên điểm đến.
const ROW_GRID = 'grid grid-cols-[2.25rem_minmax(0,1fr)_auto_1rem] items-center gap-x-3 gap-y-2 '
  + 'sm:grid-cols-[2.25rem_minmax(0,1.2fr)_minmax(0,1fr)_3rem_4.5rem_4.5rem_1rem]';

function ScoreRing({ score }: { score: number }) {
  const radius = 30;
  const circumference = 2 * Math.PI * radius;
  return (
    <div className="relative h-[76px] w-[76px] shrink-0">
      <svg viewBox="0 0 76 76" className="h-full w-full -rotate-90" aria-hidden="true">
        <circle cx="38" cy="38" r={radius} fill="none" stroke="currentColor" strokeOpacity={0.2} strokeWidth={6} />
        <circle cx="38" cy="38" r={radius} fill="none" stroke="currentColor" strokeWidth={6} strokeLinecap="round"
          strokeDasharray={circumference} strokeDashoffset={circumference * (1 - score / 100)}
          className="transition-[stroke-dashoffset] duration-500 motion-reduce:transition-none" />
      </svg>
      <span className="absolute inset-0 flex flex-col items-center justify-center leading-none">
        <span className="font-nunito text-2xl font-bold">{Math.round(score)}</span>
        <span className="mt-0.5 text-[10px] opacity-80">/100</span>
      </span>
    </div>
  );
}

function WeatherLink({ slug, primary }: { slug: string; primary: boolean }) {
  const state: ViewedLocationState = { locationSlug: slug };
  return (
    <Link to={pagePath('tong-quan')} state={state}
      className={`focus-ring inline-flex items-center gap-1 rounded-xl px-3 py-2 text-sm font-semibold transition-colors ${
        primary ? 'bg-white text-acc hover:bg-white/90' : 'bg-acc-soft text-acc hover:bg-acc hover:text-acc-ink'}`}>
      Xem thời tiết hiện tại <ArrowUpRight size={16} aria-hidden="true" />
    </Link>
  );
}

function PodiumCard({ result, activity, primary }: {
  result: DestinationResult;
  activity: ActivityProfile;
  primary: boolean;
}) {
  const { location, candidate } = result;
  const statClass = `rounded-2xl p-3 ${primary ? 'bg-white/10' : 'bg-tint'}`;
  return (
    <article aria-label={`Hạng ${candidate.rank}: ${location.name}, ${number(candidate.score)} điểm`}
      className={`flex h-full min-w-0 flex-col rounded-[24px] p-6 shadow-sh2 sm:p-7 ${primary ? 'bg-acc text-acc-ink' : 'bg-card text-ink'}`}>
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <p className={`inline-flex items-center gap-2 text-sm font-semibold ${primary ? '' : 'text-acc'}`}>
            {primary
              ? <Trophy size={17} aria-hidden="true" />
              : <span className="flex h-6 w-6 items-center justify-center rounded-full bg-acc-soft text-xs font-bold">{candidate.rank}</span>}
            {primary ? 'Hợp nhất tháng này' : `Hạng ${candidate.rank}`}
          </p>
          <h3 className="mt-3 font-nunito text-3xl font-bold leading-tight">{location.name}</h3>
          <p className={`mt-1 text-sm ${primary ? 'opacity-85' : 'text-m1'}`}>{location.regionLabel}</p>
        </div>
        <div className={primary ? '' : 'text-acc'}><ScoreRing score={candidate.score} /></div>
      </div>
      <dl className="mt-6 grid grid-cols-2 gap-3">
        <div className={statClass}>
          <dt className="flex items-center gap-1 text-xs"><Thermometer size={14} aria-hidden="true" />Nhiệt độ TB ngày</dt>
          <dd className="mt-1 font-nunito text-2xl font-bold">{number(candidate.temperatureMean)}°C</dd>
        </div>
        <div className={statClass}>
          <dt className="flex items-center gap-1 text-xs"><CloudRain size={14} aria-hidden="true" />Ngày mưa ≥ {number(activity.rainThresholdMm)} mm</dt>
          <dd className="mt-1 font-nunito text-2xl font-bold">{number(candidate.rainyDayPercentage)}%</dd>
        </div>
      </dl>
      <details className="group mt-4 border-t border-current/20 pt-3">
        <summary className="focus-ring flex cursor-pointer list-none items-center gap-1 rounded text-sm font-semibold [&::-webkit-details-marker]:hidden">
          <ChevronRight size={16} aria-hidden="true" className="transition-transform group-open:rotate-90 motion-reduce:transition-none" />
          Vì sao?
        </summary>
        <div className="mt-3"><CandidateEvidence candidate={candidate} activity={activity} /></div>
      </details>
      <div className="mt-auto pt-4"><WeatherLink slug={location.slug} primary={primary} /></div>
    </article>
  );
}

function RankingRow({ result, activity }: { result: DestinationResult; activity: ActivityProfile }) {
  const { location, candidate } = result;
  const onPodium = candidate.rank <= 2;
  return (
    <li className="border-t border-track first:border-t-0">
      <details className="group">
        <summary className={`${ROW_GRID} focus-ring cursor-pointer list-none rounded-2xl px-2 py-3 transition-colors hover:bg-tint sm:px-3 [&::-webkit-details-marker]:hidden`}>
          <span className={`flex h-8 w-8 items-center justify-center rounded-full text-sm font-bold tabular-nums ${onPodium ? 'bg-acc-soft text-acc' : 'text-m1'}`}>
            {candidate.rank}
          </span>
          <span className="min-w-0">
            <span className="block truncate font-semibold text-ink">{location.name}</span>
            <span className="block truncate text-xs text-m2">{location.regionLabel}</span>
            <span className="mt-0.5 block text-xs text-m1 sm:hidden">
              {number(candidate.temperatureMean)}°C · {number(candidate.rainyDayPercentage)}% ngày mưa
            </span>
          </span>
          <span className="col-start-2 col-end-5 row-start-2 h-2 overflow-hidden rounded-full bg-track sm:col-start-auto sm:col-end-auto sm:row-start-auto" aria-hidden="true">
            <span className="block h-full rounded-full transition-[width] duration-500 motion-reduce:transition-none"
              style={{ width: `${Math.max(2, candidate.score)}%`, background: getFactorColor(candidate.score) }} />
          </span>
          <span className="text-right font-nunito text-lg font-bold tabular-nums text-ink">{number(candidate.score)}</span>
          <span className="hidden text-right text-sm tabular-nums text-ink2 sm:block">{number(candidate.temperatureMean)}°C</span>
          <span className="hidden text-right text-sm tabular-nums text-ink2 sm:block">{number(candidate.rainyDayPercentage)}%</span>
          <ChevronRight size={16} aria-hidden="true" className="text-m3 transition-transform group-open:rotate-90 motion-reduce:transition-none" />
        </summary>
        <div className="mx-2 mb-4 mt-1 rounded-2xl bg-tint p-4 text-ink2 sm:ml-[3.25rem] sm:mr-3">
          <CandidateEvidence candidate={candidate} activity={activity} />
          <div className="mt-3"><WeatherLink slug={location.slug} primary={false} /></div>
        </div>
      </details>
    </li>
  );
}

function RankingSkeleton() {
  return (
    <div className="space-y-5 animate-pulse motion-reduce:animate-none" aria-hidden="true">
      <div className="h-12 rounded-2xl bg-acc-soft" />
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="h-[300px] rounded-[24px] bg-acc/60" />
        <div className="h-[300px] rounded-[24px] bg-card shadow-sh2" />
      </div>
      <div className="h-[420px] rounded-[24px] bg-card shadow-sh2" />
    </div>
  );
}

export function DestinationRanking({ month, activityId }: DestinationRankingProps) {
  const ranking = useQuery({
    queryKey: ['advisory', 'destinations', month, activityId],
    queryFn: ({ signal }) => getDestinationRanking({ month, activityId }, signal),
    placeholderData: keepPreviousData,
    staleTime: 30 * 60 * 1000,
    retry: false,
  });

  if (ranking.isPending) {
    return (
      <div className="space-y-5">
        <div role="status" className="flex items-center gap-3 rounded-2xl border border-border bg-card p-5 text-sm text-ink2">
          <LoaderCircle size={22} className="shrink-0 animate-spin text-acc motion-reduce:animate-none" aria-hidden="true" />
          <div>
            <p className="font-semibold">Đang xếp hạng điểm đến…</p>
            <p className="mt-1 text-m1">Lần đầu có thể lâu hơn nếu máy chủ chưa nạp lịch sử khí hậu.</p>
          </div>
        </div>
        <RankingSkeleton />
      </div>
    );
  }

  if (ranking.isError) {
    return (
      <ErrorMessage
        title="Chưa xếp hạng được điểm đến"
        message={ranking.error instanceof Error ? ranking.error.message : 'Vui lòng thử lại.'}
        onRetry={() => {
          void ranking.refetch();
        }}
      />
    );
  }

  const { activity, destinations } = ranking.data;
  const podium = destinations.slice(0, 2);
  const best = podium[0];
  const isUpdating = ranking.isPlaceholderData;

  if (!best) return <p role="status" className="text-sm text-m1">Chưa có điểm đến phù hợp cho lựa chọn này.</p>;

  return (
    <section aria-label="Xếp hạng điểm đến" aria-busy={isUpdating}
      className={`space-y-5 transition-opacity duration-300 motion-reduce:transition-none ${isUpdating ? 'opacity-60' : ''}`}>
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-acc">{activity.name} · {formatMonthTitle(ranking.data.month)}</p>
          <h2 className="mt-1 font-nunito text-2xl font-bold">Nên đi đâu?</h2>
        </div>
        <p className="text-xs text-m1">{destinations.length} điểm đến · lịch sử {dateLabel(ranking.data.baselineStart)} – {dateLabel(ranking.data.baselineEnd)}</p>
      </div>

      <p className={`flex items-start gap-2.5 rounded-2xl px-4 py-3 text-sm leading-relaxed ${
        ranking.data.lowSuitability ? 'border border-amber-300 bg-amber-50 text-amber-900' : 'bg-acc-soft text-ink2'}`}>
        {ranking.data.lowSuitability
          ? <AlertTriangle size={18} className="mt-0.5 shrink-0" aria-hidden="true" />
          : <Sparkles size={18} className="mt-0.5 shrink-0 text-acc" aria-hidden="true" />}
        <span>{ranking.data.summary}</span>
      </p>

      <div className="grid gap-4 sm:grid-cols-2">
        {podium.map(result => (
          <PodiumCard key={result.location.slug} result={result} activity={activity} primary={result === best} />
        ))}
      </div>

      <section aria-label="Bảng xếp hạng đầy đủ" className="min-w-0 rounded-[24px] bg-card p-4 shadow-sh2 sm:p-6">
        <div className="flex items-center gap-2 px-2 sm:px-3">
          <Medal size={18} className="text-acc" aria-hidden="true" />
          <h3 className="font-nunito text-xl font-bold">Bảng xếp hạng đầy đủ</h3>
        </div>
        <p className="mt-1 px-2 text-sm text-m1 sm:px-3">Chọn một dòng để xem vì sao điểm đến được xếp hạng như vậy.</p>
        <div className={`${ROW_GRID} mt-4 hidden px-3 text-[11px] font-semibold uppercase tracking-wide text-m3 sm:grid`} aria-hidden="true">
          <span>Hạng</span>
          <span>Điểm đến</span>
          <span>Mức phù hợp</span>
          <span className="text-right">Điểm</span>
          <span className="text-right">Nhiệt độ</span>
          <span className="text-right">Ngày mưa</span>
          <span />
        </div>
        <ol className="mt-2">
          {destinations.map(result => (
            <RankingRow key={result.location.slug} result={result} activity={activity} />
          ))}
        </ol>
      </section>

      <details open className="rounded-2xl border border-border p-4 text-sm text-m1">
        <summary className="focus-ring cursor-pointer rounded font-semibold text-ink2">Hiểu đúng kết quả</summary>
        <ul className="mt-3 list-disc space-y-2 pl-5">{ranking.data.notes.map(note => <li key={note}>{note}</li>)}</ul>
      </details>
    </section>
  );
}
