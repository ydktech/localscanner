import OpenAI from 'openai'

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
})

// 1차 LLM: 키워드 추출용
export async function generateKeywords(
  message: string, 
  location?: { lat: number; lng: number },
  locationInfo?: { formatted_address: string; components: any[]; place_id: string } | null
) {
  try {
    let locationContext = ''
    
    if (location && locationInfo) {
      locationContext = `사용자 현재 위치 정보:
- 좌표: 위도 ${location.lat}, 경도 ${location.lng}
- 주소: ${locationInfo.formatted_address}

이 정확한 주소 기반으로 검색할 키워드를 생성해주세요.`
    } else if (location) {
      locationContext = `사용자 현재 위치: 위도 ${location.lat}, 경도 ${location.lng}`
    }

    const systemPrompt = `당신은 여행 검색 키워드를 생성하는 어시스턴트입니다. 사용자의 요청과 위치를 바탕으로 Google Places에서 검색할 키워드만 생성해주세요.

중요사항:
1. 제공된 주소 정보를 기반으로 해당 지역에서 검색할 키워드를 생성하세요
2. 사용자의 요청 (맛집, 카페, 관광지 등)에 맞는 키워드를 만드세요
3. 반드시 다음 형식으로만 응답하세요:

KEYWORDS: [키워드1, 키워드2, 키워드3]

예시: KEYWORDS: [신주쿠 라멘, 도쿄역 카페, 긴자 쇼핑]

${locationContext}`

    const completion = await openai.chat.completions.create({
      model: 'gpt-4',
      messages: [
        {
          role: 'system',
          content: systemPrompt
        },
        {
          role: 'user',
          content: message
        }
      ],
      max_tokens: 200,
      temperature: 0.7,
    })

    return completion.choices[0]?.message?.content || 'KEYWORDS: []'
  } catch (error) {
    console.error('OpenAI API error:', error)
    return 'KEYWORDS: []'
  }
}

// 2차 LLM: 검색 결과 기반 추천
export async function generateRecommendations(
  message: string,
  searchResults: any[],
  locationInfo?: { formatted_address: string } | null
) {
  try {
    const placesInfo = searchResults.map(place => `
장소명: ${place.name}
주소: ${place.formatted_address || place.vicinity || '주소 정보 없음'}
평점: ${place.rating || '평점 정보 없음'}
유형: ${place.types?.join(', ') || '유형 정보 없음'}
${place.opening_hours?.open_now !== undefined ? `영업상태: ${place.opening_hours.open_now ? '영업중' : '영업종료'}` : ''}
`).join('\n---\n')

    const systemPrompt = `당신은 한국어로 답변하는 여행 어시스턴트입니다. Google Places 검색 결과를 바탕으로 사용자에게 상세한 추천을 해주세요.

검색된 장소들 정보:
${placesInfo}

${locationInfo ? `사용자 위치: ${locationInfo.formatted_address}` : ''}

중요사항:
1. 검색된 실제 장소들을 바탕으로 상세한 추천을 해주세요
2. 각 장소의 특징, 평점, 영업상태 등을 포함해서 설명해주세요
3. 사용자의 요청에 가장 적합한 장소들을 우선순위로 정리해주세요
4. 친근하고 도움이 되는 톤으로 답변해주세요`

    const completion = await openai.chat.completions.create({
      model: 'gpt-4',
      messages: [
        {
          role: 'system',
          content: systemPrompt
        },
        {
          role: 'user',
          content: message
        }
      ],
      max_tokens: 1500,
      temperature: 0.7,
    })

    return completion.choices[0]?.message?.content || '죄송합니다. 추천을 생성할 수 없습니다.'
  } catch (error) {
    console.error('OpenAI API error:', error)
    return '죄송합니다. 요청을 처리하는 중 오류가 발생했습니다.'
  }
}

export function extractKeywords(response: string): string[] {
  const keywordMatch = response.match(/KEYWORDS:\s*\[(.*?)\]/);
  if (keywordMatch && keywordMatch[1]) {
    return keywordMatch[1].split(',').map(keyword => keyword.trim().replace(/['"]/g, ''));
  }
  return [];
}

export default openai