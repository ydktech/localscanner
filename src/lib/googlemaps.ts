import { Client } from '@googlemaps/google-maps-services-js'
import { Loader } from '@googlemaps/js-api-loader'

const client = new Client({})

export const googleMapsApiKey = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY!

export const loader = new Loader({
  apiKey: googleMapsApiKey,
  version: 'weekly',
  libraries: ['places', 'geometry']
})

export async function searchNearbyPlaces(
  location: { lat: number; lng: number },
  radius: number = 1000,
  type: string = 'restaurant'
) {
  try {
    const response = await client.placesNearby({
      params: {
        location: location,
        radius: radius,
        type: type,
        key: googleMapsApiKey,
      },
    })
    
    return response.data.results
  } catch (error) {
    console.error('Google Places API error:', error)
    return []
  }
}

export async function getPlaceDetails(placeId: string) {
  try {
    const response = await client.placeDetails({
      params: {
        place_id: placeId,
        key: googleMapsApiKey,
      },
    })
    
    return response.data.result
  } catch (error) {
    console.error('Google Place Details API error:', error)
    return null
  }
}

export async function geocodeAddress(address: string) {
  try {
    const response = await client.geocode({
      params: {
        address: address,
        key: googleMapsApiKey,
      },
    })
    
    return response.data.results[0]?.geometry.location
  } catch (error) {
    console.error('Geocoding API error:', error)
    return null
  }
}

export async function reverseGeocode(lat: number, lng: number) {
  try {
    const response = await client.reverseGeocode({
      params: {
        latlng: { lat, lng },
        key: googleMapsApiKey,
        language: 'ko', // 한국어로 결과 받기
      },
    })
    
    if (response.data.results && response.data.results.length > 0) {
      const result = response.data.results[0]
      return {
        formatted_address: result.formatted_address,
        components: result.address_components,
        place_id: result.place_id
      }
    }
    
    return null
  } catch (error) {
    console.error('Reverse Geocoding API error:', error)
    return null
  }
}