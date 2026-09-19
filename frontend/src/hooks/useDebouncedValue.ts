import { useEffect, useRef, useState } from 'react'

export function useDebouncedValue<T>(
  value: T,
  delayMs: number,
  maxDelayMs?: number,
): T {
  const [debouncedValue, setDebouncedValue] = useState(value)
  const latestValueRef = useRef(value)
  const debounceTimeoutRef = useRef<number>(undefined)
  const maxDelayTimeoutRef = useRef<number>(undefined)

  useEffect(() => {
    latestValueRef.current = value

    const clearTimeouts = () => {
      window.clearTimeout(debounceTimeoutRef.current)
      window.clearTimeout(maxDelayTimeoutRef.current)
      debounceTimeoutRef.current = undefined
      maxDelayTimeoutRef.current = undefined
    }

    if (Object.is(value, debouncedValue)) {
      clearTimeouts()
      return
    }

    const updateDebouncedValue = () => {
      clearTimeouts()
      setDebouncedValue(latestValueRef.current)
    }

    window.clearTimeout(debounceTimeoutRef.current)
    debounceTimeoutRef.current = window.setTimeout(
      updateDebouncedValue,
      delayMs,
    )

    if (maxDelayMs !== undefined && maxDelayTimeoutRef.current === undefined) {
      maxDelayTimeoutRef.current = window.setTimeout(
        updateDebouncedValue,
        maxDelayMs,
      )
    }
  }, [debouncedValue, delayMs, maxDelayMs, value])

  useEffect(
    () => () => {
      window.clearTimeout(debounceTimeoutRef.current)
      window.clearTimeout(maxDelayTimeoutRef.current)
    },
    [],
  )

  return debouncedValue
}
