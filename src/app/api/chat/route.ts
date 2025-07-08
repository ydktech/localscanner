import { NextRequest, NextResponse } from 'next/server'
import { generateKeywords, generateRecommendations, extractKeywords } from '@/lib/openai'
import { reverseGeocode } from '@/lib/googlemaps'
import { searchPlacesByKeywords } from '@/lib/places-search'

export async function POST(request: NextRequest) {
  try {
    const { message, location } = await request.json()
    
    if (!message) {
      return NextResponse.json({ error: 'Message is required' }, { status: 400 })
    }

    let locationInfo = null
    
    // 1. 위치 정보가 있으면 Google Geocoding API로 주소 변환
    if (location) {
      locationInfo = await reverseGeocode(location.lat, location.lng)
    }

    // 2. 1차 LLM: 키워드 생성
    const keywordResponse = await generateKeywords(message, location, locationInfo)
    const keywords = extractKeywords(keywordResponse)
    
    if (keywords.length === 0) {
      return NextResponse.json({ 
        response: '죄송합니다. 검색 키워드를 생성할 수 없습니다.',
        keywords: [],
        places: []
      })
    }

    // 3. Google Places API로 실제 장소 검색
    const searchResults = location ? await searchPlacesByKeywords(keywords, location) : []
    
    // 4. 2차 LLM: 검색 결과 기반 상세 추천
    const finalResponse = await generateRecommendations(message, searchResults, locationInfo)
    
    return NextResponse.json({ 
      response: finalResponse,
      keywords,
      places: searchResults,
      locationInfo
    })
  } catch (error) {
    console.error('Chat API error:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}