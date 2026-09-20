import { useState, type FormEvent } from 'react';
import { Bot, FileText, MessageCircle, Send } from 'lucide-react';

const SAMPLE_QUESTIONS = [
  'Mùa này đi Phú Quốc có hợp không?',
  'Đám cưới tháng mấy thì đẹp nhất?',
  'Sang năm cắm trại ở Đà Lạt vào tháng nào thì ít mưa?',
];

interface AdvisoryChatBoxProps {
  isAsking: boolean;
  onAsk: (question: string) => void;
  onOpenForm: () => void;
}

export function AdvisoryChatBox({
  isAsking,
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
              disabled={isAsking}
              onClick={() => {
                setQuestion(sample);
                onAsk(sample);
              }}
              className="focus-ring flex max-w-full items-center gap-2.5 rounded-full border border-border bg-card px-5 py-3 text-left text-[14.5px] text-ink2 hover:bg-acc-soft disabled:cursor-wait disabled:opacity-60"
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
            className="focus-ring mt-2 block w-full min-w-0 rounded-2xl border border-border bg-tint px-5 py-4 text-[15.5px] text-ink"
          />

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
              disabled={isAsking}
              className="focus-ring inline-flex min-h-12 items-center justify-center gap-2 rounded-2xl bg-acc px-6 py-3 text-sm font-semibold text-acc-ink disabled:cursor-wait disabled:opacity-60"
            >
              {isAsking ? 'Đang đọc câu hỏi…' : 'Gửi câu hỏi'}
              <Send size={16} aria-hidden="true" />
            </button>
          </div>
        </form>
      </section>

    </div>
  );
}
