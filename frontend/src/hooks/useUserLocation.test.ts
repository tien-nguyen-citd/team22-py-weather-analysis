import { describe, expect, it, vi } from 'vitest'

import type { LocationItem } from '../types'
import {
  USER_LOCATION_STORAGE_KEY,
  detectNearestLocation,
  findStoredUserLocation,
  readUserLocationSlug,
  writeUserLocationSlug,
} from './useUserLocation'

const locations: LocationItem[] = [
  {
    name: 'Hà Nội',
    slug: 'ha-noi',
    region: 'dbbb',
    regionLabel: 'Đồng bằng Bắc Bộ',
    tempOffset: 0,
    lat: 21.0285,
    lon: 105.8542,
  },
  {
    name: 'Đà Nẵng',
    slug: 'da-nang',
    region: 'trungtrung',
    regionLabel: 'Trung Trung Bộ',
    tempOffset: 0,
    lat: 16.0544,
    lon: 108.2022,
  },
]

describe('user location storage', () => {
  it('đọc slug đã lưu và bỏ qua giá trị trống', () => {
    expect(readUserLocationSlug({ getItem: () => ' da-nang ' })).toBe('da-nang')
    expect(readUserLocationSlug({ getItem: () => '  ' })).toBeNull()
  })

  it('không làm hỏng ứng dụng khi storage báo lỗi', () => {
    expect(
      readUserLocationSlug({
        getItem: () => {
          throw new Error('storage bị chặn')
        },
      }),
    ).toBeNull()
    expect(
      writeUserLocationSlug('ha-noi', {
        setItem: () => {
          throw new Error('storage bị chặn')
        },
      }),
    ).toBe(false)
  })

  it('ghi đúng khóa và chỉ nhận slug còn trong danh mục', () => {
    const setItem = vi.fn()
    expect(writeUserLocationSlug('da-nang', { setItem })).toBe(true)
    expect(setItem).toHaveBeenCalledWith(USER_LOCATION_STORAGE_KEY, 'da-nang')
    expect(findStoredUserLocation(locations, 'da-nang')?.name).toBe('Đà Nẵng')
    expect(findStoredUserLocation(locations, 'khong-ton-tai')).toBeUndefined()
  })
})

describe('user geolocation', () => {
  it('chọn địa điểm gần tọa độ trình duyệt nhất', async () => {
    const geolocation = {
      getCurrentPosition: (success: PositionCallback) => {
        success({
          coords: { latitude: 16.05, longitude: 108.2 },
        } as GeolocationPosition)
      },
    } as Pick<Geolocation, 'getCurrentPosition'>

    await expect(detectNearestLocation(locations, geolocation)).resolves.toMatchObject({
      slug: 'da-nang',
    })
  })

  it('giữ lỗi từ trình duyệt để caller xử lý fallback', async () => {
    const denied: GeolocationPositionError = {
      code: 1,
      message: 'permission denied',
      PERMISSION_DENIED: 1,
      POSITION_UNAVAILABLE: 2,
      TIMEOUT: 3,
    }
    const geolocation = {
      getCurrentPosition: (_success: PositionCallback, error?: PositionErrorCallback) => {
        error?.(denied)
      },
    } as Pick<Geolocation, 'getCurrentPosition'>

    await expect(detectNearestLocation(locations, geolocation)).rejects.toBe(denied)
  })
})
