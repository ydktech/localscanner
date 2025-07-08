import { searchNearbyPlaces } from './googlemaps'

export async function searchPlacesByKeywords(
  keywords: string[],
  location: { lat: number; lng: number },
  radius: number = 2000
) {
  const allResults: any[] = []
  
  for (const keyword of keywords) {
    try {
      // Google Places Text Search 사용
      const response = await fetch(`https://maps.googleapis.com/maps/api/place/textsearch/json?query=${encodeURIComponent(keyword)}&location=${location.lat},${location.lng}&radius=${radius}&key=${process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY}&language=ko`)
      
      if (response.ok) {
        const data = await response.json()
        if (data.results) {
          allResults.push(...data.results.slice(0, 5)) // 각 키워드당 최대 5개
        }
      }
    } catch (error) {
      console.error(`Error searching for keyword: ${keyword}`, error)
    }
  }
  
  // 중복 제거 (place_id 기준)
  const uniqueResults = allResults.filter((place, index, self) => 
    index === self.findIndex(p => p.place_id === place.place_id)
  )
  
  return uniqueResults.slice(0, 15) // 최대 15개 결과 반환
}