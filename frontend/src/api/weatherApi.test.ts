import { afterEach, describe, expect, it, vi } from 'vitest';
import { fetchCurrentTemperatures } from './weatherApi';

describe('fetchCurrentTemperatures', () => {
  afterEach(() => vi.unstubAllGlobals());

  it('loads location temperatures through the backend', async () => {
    const fetchMock = vi.fn(async () => new Response(JSON.stringify({
      'ha-noi': 28.5,
      'da-nang': 30.2,
    }), { status: 200 }));
    vi.stubGlobal('fetch', fetchMock);

    await expect(fetchCurrentTemperatures()).resolves.toEqual({
      'ha-noi': 28.5,
      'da-nang': 30.2,
    });
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/locations/temperatures',
      expect.any(Object),
    );
  });
});
