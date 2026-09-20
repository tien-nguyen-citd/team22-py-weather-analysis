import { useState, type FormEvent } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { skipToken, useQuery } from '@tanstack/react-query';
import { CalendarDays, LoaderCircle, Search, WandSparkles } from 'lucide-react';
import { getAdvice, getAdvisoryActivities, type AdvisoryRequest, type MonthRange } from '../api/advisory';
import { AdvisoryResults } from '../components/AdvisoryResults';
import { ErrorMessage } from '../components/ErrorMessage';
import { defaultAdvisoryRange, formatAdvisoryNumber, validateAdvisoryRange } from '../lib/advisory';
import type { LocationItem } from '../types';

const EXAMPLES = [
  { slug: 'ho-chi-minh', activity: 'wedding', label: 'Đám cưới tại TP.HCM' },
  { slug: 'phu-quoc', activity: 'travel', label: 'Du lịch Phú Quốc' },
  { slug: 'da-lat', activity: 'camping', label: 'Cắm trại Đà Lạt' },
];

const FIELD_CLASS = 'focus-ring mt-2 block w-full min-w-0 rounded-xl border border-border bg-tint px-3 py-3 text-sm text-ink';

interface AdvisoryPageProps {
  currentLocation: LocationItem;
  locations: LocationItem[];
}

export function AdvisoryPage({ currentLocation, locations }: AdvisoryPageProps) {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [activityId, setActivityId] = useState(() => searchParams.get('activity') ?? 'general');
  const [range, setRange] = useState<MonthRange>(() => defaultAdvisoryRange());
  const [submitted, setSubmitted] = useState<AdvisoryRequest | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);
  const activities = useQuery({
    queryKey: ['advisory', 'activities'],
    queryFn: ({ signal }) => getAdvisoryActivities(signal),
    staleTime: 30 * 60 * 1000,
    retry: false,
  });
  const advice = useQuery({
    queryKey: ['advisory', 'advice', submitted],
    queryFn: submitted ? ({ signal }) => getAdvice(submitted, signal) : skipToken,
    staleTime: 30 * 60 * 1000,
    retry: false,
  });
  const profile = activities.data?.find(item => item.id === activityId);

  function clearResults() {
    setSubmitted(null);
    setValidationError(null);
  }

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const error = validateAdvisoryRange(range) ?? (!profile ? 'Vui lòng chọn hoạt động trong danh mục.' : null);
    setValidationError(error);
    if (error) return;
    const request = { locationSlug: currentLocation.slug, activityId, time: range, topK: 2 };
    if (submitted && JSON.stringify(submitted) === JSON.stringify(request)) {
      void advice.refetch();
    } else {
      setSubmitted(request);
    }
  }

  function exploreMonth(month: string) {
    const time = { startMonth: month, endMonth: month };
    setRange(time);
    setValidationError(null);
    setSubmitted({ locationSlug: currentLocation.slug, activityId, time, topK: 2 });
  }

  return (
    <div className="mt-5 space-y-7">
      <section aria-label="Yêu cầu tư vấn" className="rounded-[24px] bg-card p-5 shadow-sh2 sm:p-7">
        <div className="flex items-start gap-3">
          <span className="rounded-2xl bg-acc-soft p-3 text-acc"><CalendarDays size={24} aria-hidden="true" /></span>
          <div>
            <h1 className="font-nunito text-2xl font-bold sm:text-[28px]">Chọn lúc đẹp, lên kế hoạch hay</h1>
            <p className="mt-1 text-sm leading-relaxed text-m1">Tìm thời điểm phù hợp cho hoạt động tại <strong className="text-ink2">{currentLocation.name}</strong>, từ lịch sử khí hậu 10 năm.</p>
          </div>
        </div>
        <div className="mt-5 flex flex-wrap items-center gap-2" aria-label="Điền nhanh ví dụ">
          <span className="mr-1 inline-flex items-center gap-1 text-xs text-m1"><WandSparkles size={14} aria-hidden="true" />Thử ý tưởng:</span>
          {EXAMPLES.filter(example => locations.some(location => location.slug === example.slug)).map(example => (
            <button key={example.slug} type="button" className="focus-ring rounded-full border border-border px-3 py-2 text-xs text-ink2 hover:bg-acc-soft"
              onClick={() => {
                clearResults();
                setActivityId(example.activity);
                setRange(defaultAdvisoryRange());
                navigate(`/${example.slug}/tu-van?activity=${example.activity}`);
              }}>{example.label}</button>
          ))}
        </div>
        {activities.isPending ? (
          <p role="status" className="mt-5 text-sm text-m1">Đang tải danh mục hoạt động…</p>
        ) : activities.isError && !activities.data ? (
          <ErrorMessage title="Chưa tải được hoạt động" message="Vui lòng thử lại để chọn tiêu chí tư vấn." onRetry={() => { void activities.refetch(); }} />
        ) : (
          <form className="mt-5" onSubmit={submit} noValidate>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-[1.3fr_1fr_1fr_auto] lg:items-end">
              <div className="min-w-0 text-sm font-semibold">
                <label htmlFor="advisory-activity">Hoạt động</label>
                <select id="advisory-activity" className={FIELD_CLASS} value={activityId} onChange={event => { setActivityId(event.target.value); clearResults(); }}>
                  {!profile && <option value={activityId}>Chọn hoạt động</option>}
                  {activities.data?.map(activity => <option key={activity.id} value={activity.id}>{activity.name}</option>)}
                </select>
              </div>
              <div className="min-w-0 text-sm font-semibold">
                <label htmlFor="advisory-start">Từ tháng</label>
                <input id="advisory-start" type="month" className={FIELD_CLASS} value={range.startMonth} min="0001-01" max="9999-12"
                  aria-describedby={validationError ? 'advisory-form-error' : 'advisory-range-hint'} aria-invalid={!!validationError}
                  onChange={event => { setRange({ ...range, startMonth: event.target.value }); clearResults(); }} />
              </div>
              <div className="min-w-0 text-sm font-semibold">
                <label htmlFor="advisory-end">Đến tháng</label>
                <input id="advisory-end" type="month" className={FIELD_CLASS} value={range.endMonth} min="0001-01" max="9999-12"
                  aria-describedby={validationError ? 'advisory-form-error' : 'advisory-range-hint'} aria-invalid={!!validationError}
                  onChange={event => { setRange({ ...range, endMonth: event.target.value }); clearResults(); }} />
              </div>
              <button type="submit" disabled={advice.isFetching && !!submitted} className="focus-ring inline-flex min-h-12 items-center justify-center gap-2 rounded-xl bg-acc px-4 py-3 text-sm font-semibold text-acc-ink">
                <Search size={16} aria-hidden="true" />Tìm thời điểm phù hợp
              </button>
            </div>
            <p id="advisory-range-hint" className="mt-3 text-xs text-m1">Chọn tối đa 12 tháng. Với khoảng 1–2 tháng, kết quả chi tiết đến đầu, giữa và cuối tháng.</p>
            {validationError && <p id="advisory-form-error" role="alert" className="mt-3 text-sm text-red-700">{validationError}</p>}
            {profile && <div className="mt-4 rounded-2xl bg-tint px-4 py-3 text-sm leading-relaxed text-ink2">
              <p>{profile.description}</p>
              <p className="mt-1 text-xs text-m1">Mức ưu tiên: ít mưa {formatAdvisoryNumber(profile.rainWeight * 100)}% · nhiệt độ {formatAdvisoryNumber(profile.temperatureWeight * 100)}%.</p>
            </div>}
          </form>
        )}
      </section>

      <div aria-live="polite" aria-atomic="true">
        {submitted && advice.isFetching && (
          <div role="status" className="flex items-center gap-3 rounded-2xl border border-border bg-card p-5 text-sm text-ink2">
            <LoaderCircle size={22} className="shrink-0 animate-spin motion-reduce:animate-none text-acc" aria-hidden="true" />
            <div><p className="font-semibold">Đang tìm thời điểm phù hợp…</p><p className="mt-1 text-m1">Lần đầu ở một địa điểm có thể cần thêm thời gian để tải lịch sử. Bạn vẫn có thể đổi tiêu chí.</p></div>
          </div>
        )}
        {submitted && advice.isError && !advice.isFetching && (
          <ErrorMessage title="Chưa thể đưa ra tư vấn" message={advice.error instanceof Error ? advice.error.message : 'Vui lòng thử lại.'} onRetry={() => { void advice.refetch(); }} />
        )}
      </div>
      {submitted && advice.data && !advice.isError && (
        <AdvisoryResults key={JSON.stringify(advice.data.request)} advice={advice.data} locationName={currentLocation.name} onExploreMonth={exploreMonth} />
      )}
      {!submitted && (
        <div className="rounded-[24px] border border-dashed border-border px-6 py-10 text-center">
          <p className="font-nunito text-xl font-semibold text-ink2">Một kế hoạch, vài thời điểm đáng chọn</p>
          <p className="mx-auto mt-2 max-w-lg text-sm leading-relaxed text-m1">Chọn hoạt động và khoảng tháng, rồi tìm đề xuất. Mỗi lựa chọn đều có số liệu mưa, nhiệt độ và lý do để bạn cân nhắc.</p>
        </div>
      )}
    </div>
  );
}
