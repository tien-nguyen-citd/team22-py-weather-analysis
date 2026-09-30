import { afterEach, describe, expect, it, vi } from 'vitest'

import { getForecast } from './forecast'

describe('getForecast', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('passes the abort signal to the forecast request', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ tempNow: 28 }), { status: 200 }),
    )
    vi.stubGlobal('fetch', fetchMock)
    const controller = new AbortController()

    await getForecast('ha-noi', controller.signal)

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/locations/ha-noi/forecast',
      expect.objectContaining({ signal: controller.signal }),
    )
  })
})
