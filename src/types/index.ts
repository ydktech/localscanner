export interface Location {
  lat: number
  lng: number
}

export interface Place {
  place_id: string
  name: string
  formatted_address?: string
  rating?: number
  price_level?: number
  types: string[]
  geometry: {
    location: Location
  }
  photos?: Array<{
    photo_reference: string
    height: number
    width: number
  }>
  opening_hours?: {
    open_now: boolean
  }
  user_ratings_total?: number
}

export interface PlaceDetails extends Place {
  formatted_phone_number?: string
  website?: string
  reviews?: Array<{
    author_name: string
    rating: number
    text: string
    time: number
  }>
  opening_hours?: {
    open_now: boolean
    weekday_text: string[]
  }
}

export interface ChatMessage {
  id: string
  content: string
  role: 'user' | 'assistant'
  timestamp: Date
}