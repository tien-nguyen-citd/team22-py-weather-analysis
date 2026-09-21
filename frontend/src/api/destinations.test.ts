import { afterEach, expect, it, vi } from 'vitest';
import { getDestinationRanking, type DestinationRequest } from './destinations';

afterEach(() => vi.unstubAllGlobals());

const request: DestinationRequest = { month: '2026-12', activityId: 'beach' };

it('gửi tháng, hoạt động và tín hiệu hủy tới API xếp hạng điểm đến', async () => {
  const fetchMock = vi.fn(async () => new Response('{}'));
  vi.stubGlobal('fetch', fetchMock);
  const controller = new AbortController();
  await getDestinationRanking(request, controller.signal);
  expect(fetchMock).toHaveBeenCalledWith('/api/advisory/destinations', expect.objectContaining({
    method: 'POST', body: JSON.stringify(request), signal: controller.signal,
  }));
});

it('giữ thông báo lỗi của backend để giao diện hiển thị và cho thử lại', async () => {
  vi.stubGlobal('fetch', vi.fn(async () => new Response(JSON.stringify({
    detail: 'Chưa nạp đủ lịch sử khí hậu',
  }), { status: 502 })));
  await expect(getDestinationRanking(request)).rejects.toThrow('Chưa nạp đủ lịch sử khí hậu');
});
