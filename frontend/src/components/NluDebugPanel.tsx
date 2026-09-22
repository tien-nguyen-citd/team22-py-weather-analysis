import { Bug } from 'lucide-react';
import type { NluDebug, NluDecision, QuestionUnderstanding } from '../api/nlu';
import { DECISION_SOURCE_LABELS } from '../lib/nluDebug';

interface NluDebugPanelProps {
  question: string;
  understanding: QuestionUnderstanding & { debug: NluDebug };
}

function DecisionDetail({ title, result, decision }: {
  title: string;
  result: string;
  decision: NluDecision;
}) {
  return (
    <div className="space-y-2">
      <p>
        <span className="font-semibold text-ink">{title}:</span>{' '}
        <code className="rounded bg-bg px-1.5 py-0.5">{result}</code>{' '}
        <span className="text-m1">
          ← {DECISION_SOURCE_LABELS[decision.source]}
          {decision.matchedText && <> “{decision.matchedText}”</>}
        </span>
      </p>
      {decision.neighbors.length > 0 && (
        <table className="w-full text-left text-[13px]">
          <thead className="text-m1">
            <tr>
              <th className="py-1 pr-3 font-medium">Nhãn</th>
              <th className="py-1 pr-3 font-medium">Câu mẫu</th>
              <th className="py-1 text-right font-medium">Similarity</th>
            </tr>
          </thead>
          <tbody>
            {decision.neighbors.map((neighbor, index) => (
              <tr key={index} className="border-t border-border">
                <td className="py-1 pr-3">
                  <code>{neighbor.label ?? 'general'}</code>
                </td>
                <td className="py-1 pr-3">{neighbor.text}</td>
                <td className="py-1 text-right tabular-nums">{neighbor.similarity.toFixed(3)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

export function NluDebugPanel({ question, understanding }: NluDebugPanelProps) {
  const { debug } = understanding;
  return (
    <section
      aria-label="Chi tiết phân tích NLU"
      className="space-y-4 rounded-2xl border border-dashed border-border bg-card p-5 text-sm text-ink2"
    >
      <h3 className="flex items-center gap-2 font-semibold text-acc">
        <Bug size={16} aria-hidden="true" />
        Chi tiết phân tích NLU
        <span className="ml-auto text-xs font-normal text-m1">Ctrl + Alt + Backspace để ẩn</span>
      </h3>
      <dl className="grid grid-cols-[max-content_1fr] gap-x-3 gap-y-1">
        <dt className="text-m1">Câu hỏi</dt>
        <dd>{question}</dd>
        <dt className="text-m1">Địa điểm khớp</dt>
        <dd>{debug.locationText ?? '—'}</dd>
        <dt className="text-m1">MiniLM đọc</dt>
        <dd>
          <code className="rounded bg-bg px-1.5 py-0.5">{debug.embeddingText.trim() || '(trống)'}</code>
        </dd>
      </dl>
      <DecisionDetail title="Ý định" result={understanding.intent} decision={debug.intent} />
      <DecisionDetail
        title="Hoạt động"
        result={understanding.activityId ?? 'general'}
        decision={debug.activity}
      />
    </section>
  );
}
