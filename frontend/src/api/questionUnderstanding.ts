import type { MonthRange } from './advisory';
import { upcomingMonthRange, vietnamYearMonth, type AdvisoryQuery } from '../lib/advisory';

// Bản tạm: chỉ nhận đúng các câu mẫu bên dưới. Việc đọc câu hỏi tự do thuộc về
// dịch vụ chatbot; khi dịch vụ đó sẵn sàng, hàm understandQuestion gọi API thay
// cho bảng câu mẫu này, phần còn lại của giao diện không đổi.

interface SampleQuestion {
  text: string;
  understand: (now: Date) => AdvisoryQuery;
}

function nextYearRange(now: Date): MonthRange {
  const year = vietnamYearMonth(now).year + 1;
  return { startMonth: `${year}-01`, endMonth: `${year}-12` };
}

const SAMPLES: SampleQuestion[] = [
  {
    text: 'Đám cưới ở Hà Nội tháng mấy thì đẹp nhất?',
    understand: now => ({
      locationSlug: 'ha-noi',
      activityId: 'wedding',
      time: upcomingMonthRange(12, now),
    }),
  },
  {
    text: 'Nửa năm tới, đi Phú Quốc lúc nào là hợp nhất?',
    understand: now => ({
      locationSlug: 'phu-quoc',
      activityId: 'travel',
      time: upcomingMonthRange(6, now),
    }),
  },
  {
    text: 'Sang năm cắm trại ở Đà Lạt vào tháng nào thì ít mưa?',
    understand: now => ({
      locationSlug: 'da-lat',
      activityId: 'camping',
      time: nextYearRange(now),
    }),
  },
];

export const SAMPLE_QUESTIONS: string[] = SAMPLES.map(sample => sample.text);

function normalize(question: string): string {
  return question.trim().replace(/\s+/g, ' ').toLowerCase();
}

/** Trả `null` khi chưa đọc được câu hỏi. */
export function understandQuestion(
  question: string,
  now = new Date(),
): Promise<AdvisoryQuery | null> {
  const asked = normalize(question);
  const sample = SAMPLES.find(item => normalize(item.text) === asked);
  return Promise.resolve(sample ? sample.understand(now) : null);
}
