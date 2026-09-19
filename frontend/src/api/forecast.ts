import { requestJson } from './client'
import type { LocationItem } from '../types'

export interface BestWindowItem {
  range: string
  score: number
  start: number
  len: number
  tag: string
  note: string
}

export interface HourForecastItem {
  hour: number
  temp: number
  rainProb: number
  uv: number
  humidity: number
  wind: number
  score: number
}

export interface FactorItem {
  label: string
  value: number
  note: string
}

export interface WeatherDetails {
  sunrise: string
  sunset: string
  sunshineHours: number | null
  aqi: number | null
  aqiLabel: string | null
  rainSum: number
  rainWindow: string
  dewPoint: number
}

export interface DayForecastItem {
  date: string
  dayLabel: string
  tempMax: number
  tempMin: number
  rainProb: number
  rainSum: number
}

export interface ActivityWindowItem {
  id: string
  name: string
  score: number
  range: string
  note: string
  hasWindow: boolean
}

export interface LocationForecast {
  location: LocationItem
  updatedAt: string
  tempNow: number
  apparentTempNow: number
  tempMax: number
  tempMin: number
  conditionDesc: string
  humidityNow: number
  windNow: number
  rainProbNow: number
  uvNow: number
  dayScore: number
  verdict: string
  why: string
  bestWindows: BestWindowItem[]
  hourly: HourForecastItem[]
  factors: FactorItem[]
  details: WeatherDetails
  daily7: DayForecastItem[]
  activities: ActivityWindowItem[]
}

export function getForecast(slug: string): Promise<LocationForecast> {
  return requestJson<LocationForecast>(
    `/api/locations/${encodeURIComponent(slug)}/forecast`,
  )
}
