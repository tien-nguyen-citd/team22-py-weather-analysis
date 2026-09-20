import { useState, type FormEvent } from 'react';
import { Bot, FileText, MessageCircle, Send } from 'lucide-react';
import type { ActivityProfile } from '../api/advisory';
import { SAMPLE_QUESTIONS } from '../api/questionUnderstanding';

const STEPS = [
  'Lấy ra địa điểm, khoảng thời gian và hoạt động từ câu hỏi.',
  'Chấm điểm từng khoảng theo lịch sử khí hậu 10 năm.',
  'Trả về hai thời điểm đáng cân nhắc, kèm số liệu và lý do.',
];

interface AdvisoryChatBoxProps {
  activities: ActivityProfile[];
  notUnderstood: boolean;
  onAsk: (question: string) => void;
  onOpenForm: () => void;
}

export function AdvisoryChatBox({
  activities,
  notUnderstood,
  onAsk,
  onOpenForm,
}: AdvisoryChatBoxProps) {
  const [question, setQuestion] = useState('');

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const asked = question.trim();
    if (asked) onAsk(asked);
  }

  return (
    <div className="space-y-4">
      <section aria-label="Hỏi về thời tiết" className="rounded-[24px] bg-card p-6 shadow-sh2 sm:p-9">
        <div className="flex items-start gap-4">
          <span className="shrink-0 rounded-2xl bg-acc-soft p-3 text-acc">
            <Bot size={22} aria-hidden="true" />
          </span>
          <div>
            <h1 className="font-nunito text-2xl font-bold sm:text-[30px]">
              Bạn cần tư vấn thời tiết?
            </h1>
            <p className="mt-1.5 text-[15px] leading-relaxed text-m1">
              Hãy cứ hỏi một câu. Mỗi câu hỏi được trả lời độc lập, không cần nhớ câu trước.
            </p>
          </div>
        </div>

        <div className="mt-7 flex flex-col items-start gap-2.5">
          <span className="text-[11.5px] font-bold uppercase tracking-[0.06em] text-m1">
            Thử một câu
          </span>
          {SAMPLE_QUESTIONS.map(sample => (
            <button
              key={sample}
              type="button"
              onClick={() => {
                setQuestion(sample);
                onAsk(sample);
              }}
              className="focus-ring flex max-w-full items-center gap-2.5 rounded-full border border-border bg-card px-5 py-3 text-left text-[14.5px] text-ink2 hover:bg-acc-soft"
            >
              <MessageCircle size={15} className="shrink-0 text-acc" aria-hidden="true" />
              {sample}
            </button>
          ))}
        </div>

        <form className="mt-7" onSubmit={submit} noValidate>
          <label htmlFor="advisory-question" className="text-xs font-semibold text-m1">
            Câu hỏi của bạn
          </label>
          <input
            id="advisory-question"
            type="text"
            value={question}
            onChange={event => setQuestion(event.target.value)}
            placeholder="Ví dụ: tháng nào đi Nha Trang thì ít mưa nhất?"
            aria-describedby={notUnderstood ? 'advisory-question-error' : undefined}
            className="focus-ring mt-2 block w-full min-w-0 rounded-2xl border border-border bg-tint px-5 py-4 text-[15.5px] text-ink"
          />

          {notUnderstood && (
            <p
              id="advisory-question-error"
              role="alert"
              className="mt-3 rounded-2xl bg-tint px-4 py-3 text-sm leading-relaxed text-ink2"
            >
              Phần đọc câu hỏi tự do đang được xây dựng, hiện chỉ nhận đúng ba câu mẫu ở trên. Bạn
              bấm một câu mẫu, hoặc điền tiêu chí vào form để nhận tư vấn ngay.
            </p>
          )}

          <div className="mt-4 flex flex-wrap items-center justify-end gap-3">
            <button
              type="button"
              onClick={onOpenForm}
              className="focus-ring inline-flex items-center gap-2 rounded-xl px-3 py-3 text-sm font-semibold text-acc hover:bg-acc-soft"
            >
              <FileText size={15} aria-hidden="true" />
              Điền form thay vì hỏi
            </button>
            <button
              type="submit"
              className="focus-ring inline-flex min-h-12 items-center justify-center gap-2 rounded-2xl bg-acc px-6 py-3 text-sm font-semibold text-acc-ink"
            >
              Gửi câu hỏi
              <Send size={16} aria-hidden="true" />
            </button>
          </div>
        </form>
      </section>

      <div className="grid gap-4 lg:grid-cols-3">
        <section
          aria-label="Câu hỏi được xử lý thế nào"
          className="rounded-[20px] border border-border bg-card p-5 sm:p-6"
        >
          <h2 className="font-nunito text-[15.5px] font-bold">Câu hỏi được xử lý thế nào</h2>
          <ol className="mt-3.5 space-y-3.5">
            {STEPS.map((step, index) => (
              <li key={step} className="flex items-start gap-3">
                <span className="mt-0.5 flex h-[22px] w-[22px] shrink-0 items-center justify-center rounded-full bg-acc-soft font-nunito text-[11.5px] font-extrabold text-acc">
                  {index + 1}
                </span>
                <span className="text-[13px] leading-relaxed text-ink2">{step}</span>
              </li>
            ))}
          </ol>
        </section>

        <section
          aria-label="Hoạt động được tư vấn"
          className="rounded-[20px] border border-border bg-card p-5 sm:p-6"
        >
          <h2 className="font-nunito text-[15.5px] font-bold">Tư vấn được cho</h2>
          <div className="mt-3.5 flex flex-wrap gap-1.5">
            {activities.map(activity => (
              <span
                key={activity.id}
                className="rounded-full bg-tint px-3 py-1.5 text-[12.5px] text-ink2"
              >
                {activity.name}
              </span>
            ))}
          </div>
          <p className="mt-3 text-[12.5px] leading-relaxed text-m1">
            Không nêu hoạt động thì dùng nhu cầu chung.
          </p>
        </section>

        <section
          aria-label="Nguồn dữ liệu"
          className="rounded-[20px] border border-border bg-card p-5 sm:p-6"
        >
          <h2 className="font-nunito text-[15.5px] font-bold">Dựa trên dữ liệu nào</h2>
          <p className="mt-3 text-[13px] leading-relaxed text-ink2">
            Lượng mưa và nhiệt độ trung bình ngày trong 10 năm, từ{' '}
            <a
              href="https://open-meteo.com/en/docs/historical-weather-api"
              target="_blank"
              rel="noreferrer"
              className="focus-ring underline hover:text-acc"
            >
              Open-Meteo ERA5
            </a>
            .
          </p>
          <p className="mt-2 text-[13px] leading-relaxed text-m1">
            Là tham khảo từ lịch sử khí hậu, không phải dự báo cho một ngày cụ thể. Chưa xét gió,
            nắng, sóng biển hay độ ẩm.
          </p>
        </section>
      </div>
    </div>
  );
}
