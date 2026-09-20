import { afterEach, expect, it, vi } from 'vitest';
import { getAdvice, type AdvisoryRequest } from './advisory';

afterEach(() => vi.unstubAllGlobals());

const request: AdvisoryRequest = {
  locationSlug: 'ha-noi', activityId: 'wedding',
  time: { startMonth: '2027-01', endMonth: '2027-03' }, topK: 3,
};

it('gửi đủ tiêu chí và tín hiệu hủy để không giữ request cũ khi đổi lựa chọn', async () => {
  const fetchMock = vi.fn(async () => new Response('{}'));
  vi.stubGlobal('fetch', fetchMock);
  const controller = new AbortController();
  await getAdvice(request, controller.signal);
  expect(fetchMock).toHaveBeenCalledWith('/api/advisory', expect.objectContaining({
    method: 'POST', body: JSON.stringify(request), signal: controller.signal,
  }));
});

it('giữ thông báo thiếu dữ liệu của backend để giao diện giải thích và cho thử lại', async () => {
  vi.stubGlobal('fetch', vi.fn(async () => new Response(JSON.stringify({
    detail: 'Dữ liệu lịch sử chưa đủ ngày',
  }), { status: 502 })));
  await expect(getAdvice(request)).rejects.toThrow('Dữ liệu lịch sử chưa đủ ngày');
});
