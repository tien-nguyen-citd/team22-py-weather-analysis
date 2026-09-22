import type { ReactNode } from 'react';
import { ArrowLeft, CalendarSearch, MapPinned, type LucideIcon } from 'lucide-react';

/** Hai nhu cầu khi điền form: tìm thời điểm tại một nơi hoặc tìm nơi cho một tháng. */
export type AdvisoryFormMode = 'time' | 'place';

const MODES: { key: AdvisoryFormMode; label: string; hint: string; icon: LucideIcon }[] = [
  {
    key: 'time',
    label: 'Tìm thời điểm',
    hint: 'Chọn địa điểm, hoạt động và khoảng tháng muốn tìm.',
    icon: CalendarSearch,
  },
  {
    key: 'place',
    label: 'Tìm địa điểm',
    hint: 'Chọn tháng và hoạt động để xếp hạng các điểm du lịch theo lịch sử khí hậu 10 năm.',
    icon: MapPinned,
  },
];

interface AdvisoryFormPanelProps {
  mode: AdvisoryFormMode;
  onChangeMode: (mode: AdvisoryFormMode) => void;
  onBackToChat: () => void;
  children: ReactNode;
}

export function AdvisoryFormPanel({ mode, onChangeMode, onBackToChat, children }: AdvisoryFormPanelProps) {
  const current = MODES.find(item => item.key === mode) ?? MODES[0];

  return (
    <section aria-label="Điền tiêu chí tư vấn" className="rounded-[24px] bg-card p-5 shadow-sh2 sm:p-7">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="font-nunito text-2xl font-bold">Điền tiêu chí tư vấn</h1>
          <p className="mt-1 text-sm leading-relaxed text-m1">{current.hint}</p>
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

      <div role="group" aria-label="Nhu cầu" className="mt-5 inline-flex max-w-full flex-wrap gap-1 rounded-2xl bg-tint p-1">
        {MODES.map(item => {
          const isActive = item.key === mode;
          const Icon = item.icon;
          return (
            <button
              key={item.key}
              type="button"
              aria-pressed={isActive}
              onClick={() => onChangeMode(item.key)}
              className={`focus-ring inline-flex cursor-pointer select-none items-center gap-2 rounded-xl px-4 py-2 text-sm transition-all duration-150 ${
                isActive ? 'bg-card font-semibold text-acc shadow-xs' : 'text-m1 hover:text-ink'}`}
            >
              <Icon size={16} aria-hidden="true" />
              {item.label}
            </button>
          );
        })}
      </div>

      {children}
    </section>
  );
}
