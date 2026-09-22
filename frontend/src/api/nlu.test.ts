import { afterEach, expect, it, vi } from 'vitest';
import { understandQuestion, type UnderstandRequest } from './nlu';

afterEach(() => vi.unstubAllGlobals());

const request: UnderstandRequest = {
  question: 'Mùa này đi Phú Quốc có hợp không?',
  currentLocationSlug: 'ha-noi',
  today: '2026-09-20',
};

it('gửi đủ câu hỏi, địa điểm hiện tại, ngày tham chiếu và tín hiệu hủy', async () => {
  const fetchMock = vi.fn(async () => new Response('{}'));
  vi.stubGlobal('fetch', fetchMock);
  const controller = new AbortController();

  await understandQuestion(request, controller.signal);

  expect(fetchMock).toHaveBeenCalledWith('/nlu/understand', expect.objectContaining({
    method: 'POST', body: JSON.stringify(request), signal: controller.signal,
  }));
});

it('giữ thông báo lỗi của dịch vụ để client dùng thống nhất', async () => {
  vi.stubGlobal('fetch', vi.fn(async () => new Response(JSON.stringify({
    detail: 'Câu hỏi không được để trống',
  }), { status: 422 })));

  await expect(understandQuestion(request)).rejects.toThrow('Câu hỏi không được để trống');
});
