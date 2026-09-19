export interface User {
  username: string
}

export interface LocationItem {
  name: string
  slug: string
  region: string
  regionLabel: string
  tempOffset: number
  lat: number
  lon: number
}

export interface LocationImportResult {
  importedCount: number
}

export interface SystemSetting {
  key: string
  category: string
  title: string
  description: string
  type: 'integer'
  value: number
  defaultValue: number
  minimum: number
  maximum: number
  isModified: boolean
}
