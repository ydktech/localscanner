# CLAUDE.md

## 프로젝트 개요
LLM 기반 여행일정 자동 생성 Agent 웹앱

## 기술 스택
- **프레임워크**: Next.js 14 (App Router)
- **언어**: TypeScript
- **스타일링**: TailwindCSS
- **데이터베이스**: Supabase
- **호스팅**: Vercel
- **테스팅/디버깅**: Playwright MCP


## API 통합
- **LLM**: OpenAI API / Anthropic Claude
- **지도**: Google Maps API
- **이미지**: Unsplash API / Google Places Photos
- **경로**: Google Directions API
- **데이터베이스**: Supabase

## 디버깅
1. npm run dev를 nohup 등으로 background실행
2. playwright-mcp로 요구사항 디버깅
3. 스크린샷으로 UI 개선사항 파악
4. 개선 전략 수립
5. 개선 실행
6. 디버깅 종료 후 백그라운드 실행 종료
7. 이후 문제없을떄까지 반복

## 환경변수
.env 파일 내 OPENAI_API_KEY, NEXT_PUBLIC_GOOGLE_MAPS_API_KEY

## 핵심 기능
- AI 채팅
- 실시간 위치 기반 서비스
    - 현지에서 내 주변의 모든 것을 알려 드립니다!
- 주변 맛집/카페/관광지 정보
- 거리별 필터링 및 정렬
- 장소 상세 정보 및 리뷰

## 웹으로 디버깅
- playwright-mcp

## 기술 지침
- 기능 구현이 완료되면, 반드시 빌드한 결과물을 playwright-mcp로 실제 환경에서 스크린샷을 찍어 테스트하세요.
- UI의 레이아웃, 타이포그래피, 색상 구성, 반응성(responsiveness) 등 시각적 요소까지 꼼꼼하게 확인하여, 단순히 동작만 되는 수준이 아니라 사용자에게 직관적이고 세련된 경험을 제공할 수 있는지 판단해야 합니다. 판단 기준은 비슷한 종류의 웹이나 앱 디자인을 참고합니다.
- 단순한 구현 확인을 넘어서, 디자인 가이드나 브랜드 톤앤매너에 부합하는지까지 포함해 종합적으로 검토하는 것이 중요합니다.
