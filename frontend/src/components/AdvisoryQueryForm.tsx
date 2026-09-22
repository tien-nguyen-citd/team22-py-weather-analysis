import { useState, type FormEvent } from 'react';
import { ArrowLeft, Search } from 'lucide-react';
import type { ActivityProfile } from '../api/advisory';
import {
  formatAdvisoryNumber,
  validateAdvisoryRange,
  type AdvisoryQuery,
} from '../lib/advisory';
import type { LocationItem } from '../types';

const FIELD_CLASS =
  'focus-ring mt-2 block w-full min-w-0 rounded-xl border border-border bg-tint px-3 py-3 text-sm text-ink';

interface AdvisoryQueryFormProps {
  locations: LocationItem[];
  activities: ActivityProfile[];
  initial: AdvisoryQuery;
  onSubmit: (query: AdvisoryQuery) => void;
  onBackToChat: () => void;
}

export function AdvisoryQueryForm({
  locations,
  activities,
  initial,
  onSubmit,
  onBackToChat,
}: AdvisoryQueryFormProps) {
  const [query, setQuery] = useState<AdvisoryQuery>(initial);
  const [validationError, setValidationError] = useState<string | null>(null);
  const profile = activities.find(activity => activity.id === query.activityId);

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const error =
      validateAdvisoryRange(query.time) ??
      (!locations.some(location => location.slug === query.locationSlug)
        ? 'Vui lòng chọn địa điểm trong danh mục.'
        : null) ??
      (!profile ? 'Vui lòng chọn hoạt động trong danh mục.' : null);
    setValidationError(error);
    if (!error) onSubmit(query);
  }

  return (
    <section aria-label="Điền tiêu chí tư vấn" className="rounded-[24px] bg-card p-5 shadow-sh2 sm:p-7">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="font-nunito text-2xl font-bold">Điền tiêu chí tư vấn</h1>
          <p className="mt-1 text-sm leading-relaxed text-m1">
            Chọn địa điểm, hoạt động và khoảng tháng muốn tìm.
          </p>
        </div>
        <button
          type="button"
          onClick={onBackToChat}
          className="focus-ring inline-flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-semibold text-acc hover:bg-acc-soft"
        >
          <ArrowLeft size={16} aria-hidden="true" />
          Quay lại hỏi bằng câu
        </button>
      </div>

      <form className="mt-5" onSubmit={submit} noValidate>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-[1fr_1.2fr_1fr_1fr_auto] lg:items-end">
          <div className="min-w-0 text-sm font-semibold">
            <label htmlFor="advisory-query-location">Địa điểm</label>
            <select
              id="advisory-query-location"
              className={FIELD_CLASS}
              value={query.locationSlug}
              onChange={event => setQuery({ ...query, locationSlug: event.target.value })}
            >
              <option value="" disabled>
                Chọn địa điểm
              </option>
              {locations.map(location => (
                <option key={location.slug} value={location.slug}>
                  {location.name}
                </option>
              ))}
            </select>
          </div>

          <div className="min-w-0 text-sm font-semibold">
            <label htmlFor="advisory-query-activity">Hoạt động</label>
            <select
              id="advisory-query-activity"
              className={FIELD_CLASS}
              value={query.activityId}
              onChange={event => setQuery({ ...query, activityId: event.target.value })}
            >
              <option value="" disabled>
                Chọn hoạt động
              </option>
              {activities.map(activity => (
                <option key={activity.id} value={activity.id}>
                  {activity.name}
                </option>
              ))}
            </select>
          </div>

          <div className="min-w-0 text-sm font-semibold">
            <label htmlFor="advisory-query-start">Từ tháng</label>
            <input
              id="advisory-query-start"
              type="month"
              className={FIELD_CLASS}
              value={query.time.startMonth}
              min="0001-01"
              max="9999-12"
              aria-describedby={validationError ? 'advisory-query-error' : 'advisory-query-hint'}
              aria-invalid={!!validationError}
              onChange={event =>
                setQuery({ ...query, time: { ...query.time, startMonth: event.target.value } })
              }
            />
          </div>

          <div className="min-w-0 text-sm font-semibold">
            <label htmlFor="advisory-query-end">Đến tháng</label>
            <input
              id="advisory-query-end"
              type="month"
              className={FIELD_CLASS}
              value={query.time.endMonth}
              min="0001-01"
              max="9999-12"
              aria-describedby={validationError ? 'advisory-query-error' : 'advisory-query-hint'}
              aria-invalid={!!validationError}
              onChange={event =>
                setQuery({ ...query, time: { ...query.time, endMonth: event.target.value } })
              }
            />
          </div>

          <button
            type="submit"
            className="focus-ring inline-flex min-h-12 items-center justify-center gap-2 rounded-xl bg-acc px-4 py-3 text-sm font-semibold text-acc-ink"
          >
            <Search size={16} aria-hidden="true" />
            Tìm thời điểm phù hợp
          </button>
        </div>

        <p id="advisory-query-hint" className="mt-3 text-xs text-m1">
          Chọn tối đa 12 tháng. Với khoảng 1–2 tháng, kết quả chi tiết đến đầu, giữa và cuối tháng.
        </p>
        {validationError && (
          <p id="advisory-query-error" role="alert" className="mt-3 text-sm text-red-700">
            {validationError}
          </p>
        )}
        {profile && (
          <div className="mt-4 rounded-2xl bg-tint px-4 py-3 text-sm leading-relaxed text-ink2">
            <p>{profile.description}</p>
            <p className="mt-1 text-xs text-m1">
              Mức ưu tiên: ít mưa {formatAdvisoryNumber(profile.rainWeight * 100)}% · nhiệt độ{' '}
              {formatAdvisoryNumber(profile.temperatureWeight * 100)}%.
            </p>
          </div>
        )}
      </form>
    </section>
  );
}
