import { afterEach, describe, expect, it, vi } from 'vitest';
import { getLocationComparison, getLocationHistory } from './climateApi';

describe('climate API', () => {
  afterEach(() => vi.unstubAllGlobals());

  it('calls the history endpoint for a slug', async () => {
    const fetchMock = vi.fn(async () => new Response(JSON.stringify({
      recentPeriod: '09/2025–08/2026',
    })));
    vi.stubGlobal('fetch', fetchMock);

    await getLocationHistory('hà nội');

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/locations/h%C3%A0%20n%E1%BB%99i/history',
      expect.objectContaining({ headers: expect.any(Headers) }),
    );
  });

  it('calls comparison once with both slugs and selected month', async () => {
    const fetchMock = vi.fn(async () => new Response(JSON.stringify({
      month: 12,
    })));
    vi.stubGlobal('fetch', fetchMock);

    await getLocationComparison('ha-noi', 'da-lat', 12);

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/locations/compare?a=ha-noi&b=da-lat&month=12',
      expect.objectContaining({ headers: expect.any(Headers) }),
    );
  });
});
