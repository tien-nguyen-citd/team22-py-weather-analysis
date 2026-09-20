import { useEffect, useRef, useState } from 'react'
import { Check, ChevronDown, Crosshair, LoaderCircle, MapPin, Search } from 'lucide-react'

import { useDebouncedValue } from '../hooks/useDebouncedValue'
import { useLocations } from '../hooks/useLocations'
import type { LocationItem } from '../types'

const SEARCH_DEBOUNCE_DELAY_MS = 100
const SEARCH_MAX_DELAY_MS = 500

interface UserLocationPickerProps {
  userLocation: LocationItem
  isDetecting: boolean
  errorMessage: string | null
  onSelect: (location: LocationItem) => void
  onDetect: () => Promise<void>
}

export function UserLocationPicker({
  userLocation,
  isDetecting,
  errorMessage,
  onSelect,
  onDetect,
}: UserLocationPickerProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [query, setQuery] = useState('')
  const containerRef = useRef<HTMLDivElement>(null)
  const searchInputRef = useRef<HTMLInputElement>(null)
  const debouncedQuery = useDebouncedValue(
    query,
    SEARCH_DEBOUNCE_DELAY_MS,
    SEARCH_MAX_DELAY_MS,
  )
  const locationsQuery = useLocations(debouncedQuery.trim())
  const locations = locationsQuery.data ?? []

  useEffect(() => {
    function closeOnOutsideClick(event: MouseEvent) {
      if (!containerRef.current?.contains(event.target as Node)) {
        setIsOpen(false)
        setQuery('')
      }
    }

    document.addEventListener('mousedown', closeOnOutsideClick)
    return () => document.removeEventListener('mousedown', closeOnOutsideClick)
  }, [])

  function close() {
    setIsOpen(false)
    setQuery('')
  }

  function select(location: LocationItem) {
    onSelect(location)
    close()
  }

  return (
    <div
      ref={containerRef}
      className="relative"
      onBlur={event => {
        if (!event.currentTarget.contains(event.relatedTarget as Node | null)) close()
      }}
      onKeyDown={event => {
        if (event.key === 'Escape') {
          close()
          event.currentTarget.querySelector<HTMLButtonElement>('[aria-haspopup="dialog"]')?.focus()
        }
      }}
    >
      <button
        type="button"
        aria-haspopup="dialog"
        aria-expanded={isOpen}
        aria-label={`Vị trí của tôi: ${userLocation.name}`}
        onClick={() => {
          setIsOpen(open => !open)
          window.setTimeout(() => searchInputRef.current?.focus(), 0)
        }}
        className="focus-ring inline-flex max-w-[220px] items-center gap-2 rounded-full border border-border bg-card px-3 py-2 text-[12.5px] font-semibold text-ink2 shadow-sh1 transition-colors hover:border-acc hover:text-acc"
      >
        <MapPin className="h-[14px] w-[14px] shrink-0 text-acc" aria-hidden="true" />
        <span className="truncate">{userLocation.name}</span>
        {isDetecting ? (
          <LoaderCircle className="h-[13px] w-[13px] shrink-0 animate-spin" aria-hidden="true" />
        ) : (
          <ChevronDown className="h-[13px] w-[13px] shrink-0" aria-hidden="true" />
        )}
      </button>

      {isOpen && (
        <div
          role="dialog"
          aria-label="Cập nhật vị trí của tôi"
          className="absolute top-[46px] right-0 z-50 w-[330px] max-w-[calc(100vw-44px)] rounded-[18px] border border-border bg-card p-2 shadow-sh3"
        >
          <div className="px-2 pt-1 pb-2">
            <p className="text-[11px] font-bold tracking-[0.08em] text-m3 uppercase">
              Vị trí của tôi
            </p>
            <div className="mt-2 flex items-center gap-2 rounded-xl border border-border bg-tint px-3 py-2.5 focus-within:border-acc">
              <Search className="h-[14px] w-[14px] shrink-0 text-m2" aria-hidden="true" />
              <input
                ref={searchInputRef}
                type="search"
                value={query}
                onChange={event => setQuery(event.target.value)}
                placeholder="Tìm tỉnh, thành phố…"
                aria-label="Tìm vị trí của tôi"
                className="min-w-0 flex-1 border-0 bg-transparent text-[13px] text-ink outline-none placeholder:text-m4"
              />
            </div>
          </div>

          <button
            type="button"
            disabled={isDetecting}
            onClick={() => void onDetect()}
            className="focus-ring flex w-full items-center gap-2 rounded-xl px-3 py-2.5 text-left text-[13px] font-semibold text-acc hover:bg-acc-soft disabled:cursor-wait disabled:opacity-60"
          >
            {isDetecting ? (
              <LoaderCircle className="h-[15px] w-[15px] animate-spin" aria-hidden="true" />
            ) : (
              <Crosshair className="h-[15px] w-[15px]" aria-hidden="true" />
            )}
            {isDetecting ? 'Đang xác định vị trí…' : 'Dùng vị trí hiện tại'}
          </button>

          {errorMessage && (
            <p role="alert" className="mx-3 my-2 text-[12px] leading-relaxed text-red-700">
              {errorMessage}
            </p>
          )}

          <div
            role="listbox"
            aria-label="Danh sách vị trí của tôi"
            className="mt-1 max-h-[280px] overflow-y-auto border-t border-border pt-1"
          >
            {locationsQuery.isFetching && locations.length === 0 ? (
              <p role="status" className="px-3 py-4 text-center text-[13px] text-m2">
                Đang tìm địa điểm…
              </p>
            ) : locations.length === 0 ? (
              <p className="px-3 py-4 text-center text-[13px] text-m2">
                Không tìm thấy địa điểm nào khớp.
              </p>
            ) : (
              locations.map(location => {
                const isSelected = location.slug === userLocation.slug
                return (
                  <button
                    key={location.slug}
                    type="button"
                    role="option"
                    aria-selected={isSelected}
                    onClick={() => select(location)}
                    className={`focus-ring flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left transition-colors ${
                      isSelected ? 'bg-acc-soft text-acc' : 'text-ink hover:bg-tint'
                    }`}
                  >
                    <span className="min-w-0 flex-1">
                      <span className="block truncate text-[13.5px] font-semibold">
                        {location.name}
                      </span>
                      <span className="block truncate text-[11px] text-m2">
                        {location.regionLabel}
                      </span>
                    </span>
                    {isSelected && <Check className="h-[15px] w-[15px] shrink-0" aria-hidden="true" />}
                  </button>
                )
              })
            )}
          </div>
        </div>
      )}
    </div>
  )
}
