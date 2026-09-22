import { Fragment, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Compass, Info } from 'lucide-react';
import { getAdvisoryActivities } from '../api/advisory';
import { AdvisoryPageFooter } from '../components/AdvisoryPageFooter';
import { DestinationRanking } from '../components/DestinationRanking';
import { ErrorMessage } from '../components/ErrorMessage';
import {
  activityIcon,
  DEFAULT_DESTINATION_ACTIVITY,
  formatMonthChip,
  formatMonthTitle,
  upcomingMonths,
} from '../lib/destinations';

const MONTH_COUNT = 12;

export function DestinationPage() {
  const [months] = useState(() => upcomingMonths(MONTH_COUNT));
  const [month, setMonth] = useState(months[0]);
  const [activityId, setActivityId] = useState(DEFAULT_DESTINATION_ACTIVITY);

  const activities = useQuery({
    queryKey: ['advisory', 'activities'],
    queryFn: ({ signal }) => getAdvisoryActivities(signal),
    staleTime: 30 * 60 * 1000,
    retry: false,
  });
  const choices = activities.data ?? [];
  const selectedActivity = choices.find(activity => activity.id === activityId);

  return (
    <div className="mt-5 space-y-7">
      <section aria-label="Chọn tháng và hoạt động" className="rounded-[24px] bg-card p-5 shadow-sh2 sm:p-7">
        <p className="inline-flex items-center gap-2 text-sm font-semibold text-acc">
          <Compass size={17} aria-hidden="true" />
          Gợi ý điểm đến
        </p>
        <h1 className="mt-2 font-nunito text-2xl font-bold sm:text-[28px]">Tháng nào đi đâu?</h1>
        <p className="mt-1 text-sm text-m1">Xếp hạng 17 điểm du lịch theo lịch sử khí hậu 10 năm.</p>

        <div className="mt-6">
          <h2 className="text-[11px] font-semibold uppercase tracking-wide text-m3">Tháng</h2>
          <div className="mt-2 flex flex-wrap items-center gap-1.5">
            {months.map((item, index) => {
              const isActive = item === month;
              const startsNewYear = index > 0 && item.endsWith('-01');
              return (
                <Fragment key={item}>
                  {startsNewYear && <span className="mx-1 h-6 w-px bg-track" aria-hidden="true" />}
                  <button
                    type="button"
                    aria-pressed={isActive}
                    aria-label={formatMonthTitle(item)}
                    onClick={() => setMonth(item)}
                    className={`focus-ring cursor-pointer select-none rounded-[9px] px-2.5 py-[7px] text-[12px] tabular-nums transition-all duration-150 ${
                      isActive ? 'bg-acc font-semibold text-acc-ink shadow-xs' : 'bg-tint text-m1 hover:text-ink'}`}
                  >
                    {formatMonthChip(item)}
                  </button>
                </Fragment>
              );
            })}
          </div>
        </div>

        <div className="mt-5">
          <h2 className="text-[11px] font-semibold uppercase tracking-wide text-m3">Hoạt động</h2>
          {activities.isPending ? (
            <p role="status" className="mt-2 text-sm text-m1">Đang tải danh mục hoạt động…</p>
          ) : activities.isError && !activities.data ? (
            <ErrorMessage
              title="Chưa tải được hoạt động"
              message="Vui lòng thử lại để chọn hoạt động."
              onRetry={() => {
                void activities.refetch();
              }}
            />
          ) : (
            <>
              <div className="mt-2 flex flex-wrap gap-1.5">
                {choices.map(activity => {
                  const isActive = activity.id === activityId;
                  const Icon = activityIcon(activity.id);
                  return (
                    <button
                      key={activity.id}
                      type="button"
                      aria-pressed={isActive}
                      onClick={() => setActivityId(activity.id)}
                      className={`focus-ring inline-flex cursor-pointer select-none items-center gap-1.5 rounded-full border px-3 py-1.5 text-[13px] transition-all duration-150 ${
                        isActive
                          ? 'border-acc bg-acc-soft font-semibold text-acc'
                          : 'border-border bg-card text-ink2 hover:border-acc/40 hover:text-ink'}`}
                    >
                      <Icon size={15} aria-hidden="true" />
                      {activity.name}
                    </button>
                  );
                })}
              </div>
              {selectedActivity && (
                <p className="mt-4 flex items-start gap-2 rounded-2xl bg-tint px-4 py-3 text-sm text-ink2">
                  <Info size={16} className="mt-0.5 shrink-0 text-acc" aria-hidden="true" />
                  {selectedActivity.description}
                </p>
              )}
            </>
          )}
        </div>
      </section>

      <DestinationRanking month={month} activityId={activityId} />

      {activities.data && <AdvisoryPageFooter activities={activities.data} />}
    </div>
  );
}
