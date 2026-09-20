import { useCallback, useEffect, useRef, useState } from 'react'

import { findNearestLocation } from '../api/locations'
import type { LocationItem } from '../types'

export const USER_LOCATION_STORAGE_KEY = 'nang_mua_user_location'

interface ReadableStorage {
  getItem(key: string): string | null
}

interface WritableStorage {
  setItem(key: string, value: string): void
}

interface UserLocationState {
  userLocation: LocationItem | undefined
  isInitialized: boolean
  isDetecting: boolean
  errorMessage: string | null
  selectUserLocation: (location: LocationItem) => void
  detectUserLocation: () => Promise<void>
}

export function readUserLocationSlug(
  storage: ReadableStorage = window.localStorage,
): string | null {
  try {
    const value = storage.getItem(USER_LOCATION_STORAGE_KEY)?.trim()
    return value || null
  } catch {
    return null
  }
}

export function writeUserLocationSlug(
  slug: string,
  storage: WritableStorage = window.localStorage,
): boolean {
  try {
    storage.setItem(USER_LOCATION_STORAGE_KEY, slug)
    return true
  } catch {
    return false
  }
}

export function findStoredUserLocation(
  locations: LocationItem[],
  storedSlug: string | null,
): LocationItem | undefined {
  if (!storedSlug) return undefined
  return locations.find(location => location.slug === storedSlug)
}

export function detectNearestLocation(
  locations: LocationItem[],
  geolocation: Pick<Geolocation, 'getCurrentPosition'>,
): Promise<LocationItem> {
  return new Promise((resolve, reject) => {
    geolocation.getCurrentPosition(
      position => {
        const nearest = findNearestLocation(
          locations,
          position.coords.latitude,
          position.coords.longitude,
        )
        if (nearest) resolve(nearest)
        else reject(new Error('Danh sách địa điểm đang trống.'))
      },
      reject,
      { timeout: 5000, maximumAge: 5 * 60 * 1000 },
    )
  })
}

function geolocationErrorMessage(): string {
  return 'Không xác định được vị trí. Hãy kiểm tra quyền truy cập vị trí của trình duyệt.'
}

export function useUserLocation(
  locations: LocationItem[],
  fallbackLocation: LocationItem | undefined,
): UserLocationState {
  const [userLocationSlug, setUserLocationSlug] = useState<string | null>(() =>
    readUserLocationSlug(),
  )
  const [initializationFinished, setInitializationFinished] = useState(false)
  const [isDetectingManually, setIsDetectingManually] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const initializationStarted = useRef(false)
  const hasUserSelection = useRef(false)
  const mounted = useRef(true)
  const storedLocation = findStoredUserLocation(locations, userLocationSlug)
  const isInitialized = storedLocation !== undefined || initializationFinished
  const isDetectingAutomatically =
    locations.length > 0 && fallbackLocation !== undefined && !isInitialized

  useEffect(() => {
    mounted.current = true
    return () => {
      mounted.current = false
    }
  }, [])

  const saveLocation = useCallback((location: LocationItem) => {
    setUserLocationSlug(location.slug)
    writeUserLocationSlug(location.slug)
  }, [])

  useEffect(() => {
    if (locations.length === 0 || !fallbackLocation || initializationStarted.current) {
      return
    }
    initializationStarted.current = true

    if (storedLocation) {
      return
    }

    const applyFallback = () => {
      if (!mounted.current || hasUserSelection.current) return
      saveLocation(fallbackLocation)
      setInitializationFinished(true)
    }

    const detection = 'geolocation' in navigator
      ? detectNearestLocation(locations, navigator.geolocation)
      : Promise.reject(new Error('Trình duyệt không hỗ trợ định vị.'))
    void detection.then(
      location => {
        if (!mounted.current || hasUserSelection.current) return
        saveLocation(location)
        setInitializationFinished(true)
      },
      applyFallback,
    )
  }, [fallbackLocation, locations, saveLocation, storedLocation])

  const selectUserLocation = useCallback(
    (location: LocationItem) => {
      hasUserSelection.current = true
      saveLocation(location)
      setErrorMessage(null)
      setInitializationFinished(true)
    },
    [saveLocation],
  )

  const detectUserLocation = useCallback(async () => {
    hasUserSelection.current = true
    setInitializationFinished(true)
    setErrorMessage(null)
    if (!('geolocation' in navigator)) {
      setErrorMessage('Trình duyệt này không hỗ trợ định vị.')
      return
    }

    setIsDetectingManually(true)
    try {
      const location = await detectNearestLocation(locations, navigator.geolocation)
      if (mounted.current) saveLocation(location)
    } catch {
      if (mounted.current) setErrorMessage(geolocationErrorMessage())
    } finally {
      if (mounted.current) setIsDetectingManually(false)
    }
  }, [locations, saveLocation])

  return {
    userLocation:
      storedLocation ?? fallbackLocation,
    isInitialized,
    isDetecting: isDetectingAutomatically || isDetectingManually,
    errorMessage,
    selectUserLocation,
    detectUserLocation,
  }
}
