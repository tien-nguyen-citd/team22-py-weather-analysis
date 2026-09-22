import { useState } from 'react';
import { skipToken, useQuery } from '@tanstack/react-query';
import { LoaderCircle, PencilLine } from 'lucide-react';
import { getAdvice, getAdvisoryActivities } from '../api/advisory';
import { understandQuestion, type NluDebug, type QuestionUnderstanding } from '../api/nlu';
import { AdvisoryChatBox } from '../components/AdvisoryChatBox';
import { AdvisoryFormPanel, type AdvisoryFormMode } from '../components/AdvisoryFormPanel';
import { AdvisoryPageFooter } from '../components/AdvisoryPageFooter';
import { AdvisoryQueryForm } from '../components/AdvisoryQueryForm';
import { AdvisoryResults } from '../components/AdvisoryResults';
import { DestinationQueryForm } from '../components/DestinationQueryForm';
import { DestinationRanking } from '../components/DestinationRanking';
import { ErrorMessage } from '../components/ErrorMessage';
import { NluDebugPanel } from '../components/NluDebugPanel';
import { useKeyboardToggle } from '../hooks/useKeyboardToggle';
import {
  defaultAdvisoryRange,
  formatAdvisoryDate,
  inferActivityFromLocation,
  toAdvisoryQuery,
  vietnamToday,
  type AdvisoryQuery,
} from '../lib/advisory';
import {
  DEFAULT_DESTINATION_ACTIVITY,
  formatMonthTitle,
  toDestinationQuery,
  upcomingMonths,
  type DestinationQuery,
} from '../lib/destinations';
import { isNluDebugShortcut } from '../lib/nluDebug';
import type { LocationItem } from '../types';

const TOP_K = 2;

interface AskedQuestion {
  question: string;
  understanding: QuestionUnderstanding & { debug: NluDebug };
}

interface AdvisoryPageProps {
  locations: LocationItem[];
  userLocationSlug: string;
}

export function AdvisoryPage({ locations, userLocationSlug }: AdvisoryPageProps) {
  // null: đang ở khung hỏi đáp; còn lại: form đang mở ở chế độ tương ứng.
  const [formMode, setFormMode] = useState<AdvisoryFormMode | null>(null);
  const [isAsking, setIsAsking] = useState(false);
  const [askFailed, setAskFailed] = useState(false);
  const [query, setQuery] = useState<AdvisoryQuery | null>(null);
  const [destinationQuery, setDestinationQuery] = useState<DestinationQuery | null>(null);
  const [askedByQuestion, setAskedByQuestion] = useState(false);
  const [activityInferredFromLocation, setActivityInferredFromLocation] = useState(false);
  const [lastAsked, setLastAsked] = useState<AskedQuestion | null>(null);
  const showNluDebug = useKeyboardToggle(isNluDebugShortcut);

  const activities = useQuery({
    queryKey: ['advisory', 'activities'],
    queryFn: ({ signal }) => getAdvisoryActivities(signal),
    staleTime: 30 * 60 * 1000,
    retry: false,
  });
  const advice = useQuery({
    queryKey: ['advisory', query],
    queryFn: query
      ? ({ signal }) => getAdvice({ ...query, topK: TOP_K }, signal)
      : skipToken,
    staleTime: 30 * 60 * 1000,
    retry: false,
  });

  async function ask(question: string) {
    setIsAsking(true);
    setAskFailed(false);
    try {
      const now = new Date();
      const understood = await understandQuestion({
        question,
        currentLocationSlug: userLocationSlug,
        today: vietnamToday(now),
      });
      const { debug } = understood;
      setLastAsked(debug ? { question, understanding: { ...understood, debug } } : null);
      if (understood.intent === 'find_place') {
        setDestinationQuery(toDestinationQuery(understood, now));
        setQuery(null);
      } else {
        setDestinationQuery(null);
        setQuery(toAdvisoryQuery(understood, userLocationSlug, now));
        setActivityInferredFromLocation(
          understood.activityId === null
          && understood.locationFromQuestion
          && inferActivityFromLocation(understood.locationSlug ?? '') !== null,
        );
      }
      setAskedByQuestion(true);
      setFormMode(null);
    } catch {
      setAskFailed(true);
    } finally {
      setIsAsking(false);
    }
  }

  function runTimeFormQuery(next: AdvisoryQuery) {
    setQuery(next);
    setDestinationQuery(null);
    setAskedByQuestion(false);
    setActivityInferredFromLocation(false);
    setLastAsked(null);
    setFormMode(null);
  }

  function runPlaceFormQuery(next: DestinationQuery) {
    setDestinationQuery(next);
    setQuery(null);
    setAskedByQuestion(false);
    setActivityInferredFromLocation(false);
    setLastAsked(null);
    setFormMode(null);
  }

  // Form mở đúng loại kết quả đang xem, để nút "Sửa" dẫn tới đúng form.
  function openForm() {
    setFormMode(destinationQuery ? 'place' : 'time');
  }

  function exploreMonth(month: string) {
    if (!query) return;
    setQuery({ ...query, time: { startMonth: month, endMonth: month } });
  }

  const locationName = (slug: string) =>
    locations.find(location => location.slug === slug)?.name ?? slug;
  const activityName = (id: string) =>
    activities.data?.find(activity => activity.id === id)?.name ?? id;

  // Giá trị ban đầu của hai form lấy từ kết quả đang xem, kể cả khi đổi sang chế độ kia.
  const timeFormInitial: AdvisoryQuery = {
    locationSlug: query?.locationSlug ?? userLocationSlug,
    activityId: query?.activityId ?? destinationQuery?.activityId ?? '',
    time: query?.time
      ?? (destinationQuery
        ? { startMonth: destinationQuery.month, endMonth: destinationQuery.month }
        : defaultAdvisoryRange()),
  };
  const placeFormInitial: DestinationQuery = destinationQuery ?? {
    month: query?.time.startMonth ?? upcomingMonths(1)[0],
    activityId: query?.activityId ?? DEFAULT_DESTINATION_ACTIVITY,
  };

  return (
    <div className="mt-5 space-y-7">
      {activities.isPending ? (
        <p role="status" className="text-sm text-m1">
          Đang tải danh mục hoạt động…
        </p>
      ) : activities.isError && !activities.data ? (
        <ErrorMessage
          title="Chưa tải được hoạt động"
          message="Vui lòng thử lại để chọn tiêu chí tư vấn."
          onRetry={() => {
            void activities.refetch();
          }}
        />
      ) : formMode ? (
        <AdvisoryFormPanel
          mode={formMode}
          onChangeMode={setFormMode}
          onBackToChat={() => setFormMode(null)}
        >
          {formMode === 'time' ? (
            <AdvisoryQueryForm
              locations={locations}
              activities={activities.data ?? []}
              initial={timeFormInitial}
              onSubmit={runTimeFormQuery}
            />
          ) : (
            <DestinationQueryForm
              activities={activities.data ?? []}
              initial={placeFormInitial}
              onSubmit={runPlaceFormQuery}
            />
          )}
        </AdvisoryFormPanel>
      ) : (
        <AdvisoryChatBox
          isAsking={isAsking}
          askFailed={askFailed}
          onAsk={question => void ask(question)}
          onOpenForm={openForm}
        />
      )}

      {showNluDebug && lastAsked && (
        <NluDebugPanel question={lastAsked.question} understanding={lastAsked.understanding} />
      )}

      <div aria-live="polite" aria-atomic="true">
        {query && advice.isFetching && (
          <div
            role="status"
            className="flex items-center gap-3 rounded-2xl border border-border bg-card p-5 text-sm text-ink2"
          >
            <LoaderCircle
              size={22}
              className="shrink-0 animate-spin text-acc motion-reduce:animate-none"
              aria-hidden="true"
            />
            <div>
              <p className="font-semibold">Đang tìm thời điểm phù hợp…</p>
              <p className="mt-1 text-m1">
                Lần đầu ở một địa điểm có thể cần thêm thời gian để tải lịch sử.
              </p>
            </div>
          </div>
        )}
        {query && advice.isError && !advice.isFetching && (
          <ErrorMessage
            title="Chưa thể đưa ra tư vấn"
            message={advice.error instanceof Error ? advice.error.message : 'Vui lòng thử lại.'}
            onRetry={() => {
              void advice.refetch();
            }}
          />
        )}
      </div>

      {query && askedByQuestion && advice.data && !advice.isError && (
        <div className="flex flex-wrap items-center gap-x-3 gap-y-2 rounded-2xl bg-acc-soft px-4 py-3 text-sm text-ink2">
          <span className="font-semibold text-acc">
            {activityInferredFromLocation ? 'Gợi ý theo địa điểm' : 'Hiểu là'}
          </span>
          <span>
            {locationName(query.locationSlug)} · {formatAdvisoryDate(query.time.startMonth)} –{' '}
            {formatAdvisoryDate(query.time.endMonth)} · {activityName(query.activityId)}
          </span>
          <button
            type="button"
            onClick={openForm}
            className="focus-ring ml-auto inline-flex items-center gap-1.5 rounded-lg px-2 py-1 font-semibold text-acc hover:bg-card"
          >
            <PencilLine size={14} aria-hidden="true" />
            Sửa
          </button>
        </div>
      )}

      {query && advice.data && !advice.isError && (
        <AdvisoryResults
          key={JSON.stringify(advice.data.request)}
          advice={advice.data}
          locationName={locationName(query.locationSlug)}
          onExploreMonth={exploreMonth}
        />
      )}

      {destinationQuery && askedByQuestion && (
        <div className="flex flex-wrap items-center gap-x-3 gap-y-2 rounded-2xl bg-acc-soft px-4 py-3 text-sm text-ink2">
          <span className="font-semibold text-acc">Hiểu là</span>
          <span>
            Tìm điểm đến · {formatMonthTitle(destinationQuery.month)} · {activityName(destinationQuery.activityId)}
          </span>
          <button
            type="button"
            onClick={openForm}
            className="focus-ring ml-auto inline-flex items-center gap-1.5 rounded-lg px-2 py-1 font-semibold text-acc hover:bg-card"
          >
            <PencilLine size={14} aria-hidden="true" />
            Sửa
          </button>
        </div>
      )}

      {destinationQuery && (
        <DestinationRanking month={destinationQuery.month} activityId={destinationQuery.activityId} />
      )}

      {activities.data && <AdvisoryPageFooter activities={activities.data} />}
    </div>
  );
}
