import { Fragment, useState, type FormEvent } from 'react';
import { Info, Search } from 'lucide-react';
import type { ActivityProfile } from '../api/advisory';
import {
  activityIcon,
  DEFAULT_DESTINATION_ACTIVITY,
  destinationActivities,
  formatMonthChip,
  formatMonthTitle,
  upcomingMonths,
  type DestinationQuery,
} from '../lib/destinations';

const MONTH_COUNT = 12;

interface DestinationQueryFormProps {
  activities: ActivityProfile[];
  initial: DestinationQuery;
  onSubmit: (query: DestinationQuery) => void;
}

export function DestinationQueryForm({ activities, initial, onSubmit }: DestinationQueryFormProps) {
  const choices = destinationActivities(activities);
  const [months] = useState(() => {
    const upcoming = upcomingMonths(MONTH_COUNT);
    // Tháng đang xem có thể nằm ngoài 12 tháng tới (VD hỏi "tháng này"), vẫn giữ để sửa tiếp.
    return upcoming.includes(initial.month) ? upcoming : [initial.month, ...upcoming].sort();
  });
  const [month, setMonth] = useState(initial.month);
  const [activityId, setActivityId] = useState(
    choices.some(activity => activity.id === initial.activityId)
      ? initial.activityId
      : DEFAULT_DESTINATION_ACTIVITY,
  );
  const selectedActivity = choices.find(activity => activity.id === activityId);

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    onSubmit({ month, activityId });
  }

  return (
    <form className="mt-5" onSubmit={submit} noValidate>
      <fieldset>
        <legend className="text-[11px] font-semibold uppercase tracking-wide text-m3">Tháng</legend>
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
      </fieldset>

      <fieldset className="mt-5">
        <legend className="text-[11px] font-semibold uppercase tracking-wide text-m3">Hoạt động</legend>
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
      </fieldset>

      <div className="mt-5 flex justify-end">
        <button
          type="submit"
          className="focus-ring inline-flex min-h-12 items-center justify-center gap-2 rounded-xl bg-acc px-4 py-3 text-sm font-semibold text-acc-ink"
        >
          <Search size={16} aria-hidden="true" />
          Tìm địa điểm phù hợp
        </button>
      </div>
    </form>
  );
}
