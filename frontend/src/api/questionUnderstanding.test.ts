import { describe, expect, it } from 'vitest';
import { SAMPLE_QUESTIONS, understandQuestion } from './questionUnderstanding';

// 12:00 ngày 20/09/2026 giờ Việt Nam, nên tháng kế tiếp là 10/2026.
const NOW = new Date('2026-09-20T05:00:00Z');

describe('Đọc câu hỏi tư vấn', () => {
  it('đủ ba câu mẫu để khung chat và bản mock không lệch nhau', () => {
    expect(SAMPLE_QUESTIONS).toHaveLength(3);
  });

  it('câu hỏi tháng mấy lấy trọn 12 tháng kể từ tháng kế tiếp', async () => {
    await expect(understandQuestion(SAMPLE_QUESTIONS[0], NOW)).resolves.toEqual({
      locationSlug: 'ha-noi',
      activityId: 'wedding',
      time: { startMonth: '2026-10', endMonth: '2027-09' },
    });
  });

  it('câu hỏi nửa năm tới lấy 6 tháng kể từ tháng kế tiếp', async () => {
    await expect(understandQuestion(SAMPLE_QUESTIONS[1], NOW)).resolves.toEqual({
      locationSlug: 'phu-quoc',
      activityId: 'travel',
      time: { startMonth: '2026-10', endMonth: '2027-03' },
    });
  });

  it('câu hỏi sang năm lấy trọn năm sau chứ không tính từ tháng kế tiếp', async () => {
    await expect(understandQuestion(SAMPLE_QUESTIONS[2], NOW)).resolves.toEqual({
      locationSlug: 'da-lat',
      activityId: 'camping',
      time: { startMonth: '2027-01', endMonth: '2027-12' },
    });
  });

  it('bỏ qua khác biệt hoa thường và khoảng trắng thừa khi so khớp', async () => {
    const typed = `  ĐÁM CƯỚI   ở hà nội tháng mấy thì đẹp nhất?  `;
    await expect(understandQuestion(typed, NOW)).resolves.not.toBeNull();
  });

  it.each([
    'Ngày mai Hà Nội có mưa không?',
    'tháng nào đi Nha Trang thì ít mưa nhất?',
    '',
  ])('trả null cho câu chưa đọc được: %s', async question => {
    await expect(understandQuestion(question, NOW)).resolves.toBeNull();
  });
});
