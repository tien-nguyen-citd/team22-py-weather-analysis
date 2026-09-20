import { useState } from 'react';
import { skipToken, useQuery } from '@tanstack/react-query';
import { LoaderCircle, PencilLine } from 'lucide-react';
import { getAdvice, getAdvisoryActivities } from '../api/advisory';
import { getNluHealth, understandQuestion } from '../api/nlu';
import { AdvisoryChatBox } from '../components/AdvisoryChatBox';
import { AdvisoryQueryForm } from '../components/AdvisoryQueryForm';
import { AdvisoryResults } from '../components/AdvisoryResults';
import { ErrorMessage } from '../components/ErrorMessage';
import {
  defaultAdvisoryRange,
  formatAdvisoryDate,
  toAdvisoryQuery,
  vietnamToday,
  type AdvisoryQuery,
} from '../lib/advisory';
import type { LocationItem } from '../types';

const TOP_K = 2;

interface AdvisoryPageV2Props {
  locations: LocationItem[];
  currentLocationSlug: string;
}

export function AdvisoryPageV2({ locations, currentLocationSlug }: AdvisoryPageV2Props) {
  const [showForm, setShowForm] = useState(false);
  const [isAsking, setIsAsking] = useState(false);
  const [query, setQuery] = useState<AdvisoryQuery | null>(null);
  const [askedByQuestion, setAskedByQuestion] = useState(false);

  const activities = useQuery({
    queryKey: ['advisory', 'activities'],
    queryFn: ({ signal }) => getAdvisoryActivities(signal),
    staleTime: 30 * 60 * 1000,
    retry: false,
  });
  const nluHealth = useQuery({
    queryKey: ['nlu', 'health'],
    queryFn: ({ signal }) => getNluHealth(signal),
    staleTime: Infinity,
    retry: false,
  });
  const advice = useQuery({
    queryKey: ['advisory', 'v2', query],
    queryFn: query
      ? ({ signal }) => getAdvice({ ...query, topK: TOP_K }, signal)
      : skipToken,
    staleTime: 30 * 60 * 1000,
    retry: false,
  });

  async function ask(question: string) {
    setIsAsking(true);
    try {
      const now = new Date();
      const understood = await understandQuestion({
        question,
        currentLocationSlug,
        today: vietnamToday(now),
      });
      setQuery(toAdvisoryQuery(understood, currentLocationSlug, now));
      setAskedByQuestion(true);
      setShowForm(false);
    } catch {
      setShowForm(true);
    } finally {
      setIsAsking(false);
    }
  }

  function runFormQuery(next: AdvisoryQuery) {
    setQuery(next);
    setAskedByQuestion(false);
    setShowForm(false);
  }

  function exploreMonth(month: string) {
    if (!query) return;
    setQuery({ ...query, time: { startMonth: month, endMonth: month } });
  }

  const locationName = (slug: string) =>
    locations.find(location => location.slug === slug)?.name ?? slug;
  const activityName = (id: string) =>
    activities.data?.find(activity => activity.id === id)?.name ?? id;

  return (
    <div className="mt-5 space-y-7">
      {activities.isPending || nluHealth.isPending ? (
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
      ) : showForm || !nluHealth.isSuccess ? (
        <AdvisoryQueryForm
          locations={locations}
          activities={activities.data ?? []}
          initial={
            query ?? {
              locationSlug: currentLocationSlug,
              activityId: 'general',
              time: defaultAdvisoryRange(),
            }
          }
          onSubmit={runFormQuery}
          onBackToChat={nluHealth.isSuccess ? () => setShowForm(false) : undefined}
        />
      ) : (
        <AdvisoryChatBox
          activities={activities.data ?? []}
          isAsking={isAsking}
          onAsk={question => void ask(question)}
          onOpenForm={() => setShowForm(true)}
        />
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
          <span className="font-semibold text-acc">Hiểu là</span>
          <span>
            {locationName(query.locationSlug)} · {formatAdvisoryDate(query.time.startMonth)} –{' '}
            {formatAdvisoryDate(query.time.endMonth)} · {activityName(query.activityId)}
          </span>
          <button
            type="button"
            onClick={() => setShowForm(true)}
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
    </div>
  );
}
