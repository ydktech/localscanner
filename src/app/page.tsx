import Link from 'next/link'

export default function Home() {
  return (
    <div className="bg-gradient-to-br from-blue-50 to-indigo-100 min-h-full">
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-4">
            LocalScanner AI 여행 어시스턴트
          </h1>
          <p className="text-lg text-gray-600">
            AI와 채팅으로 주변 맛집, 카페, 관광지를 발견해보세요
          </p>
        </div>
        
        <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
          <h2 className="text-2xl font-semibold mb-4 text-gray-800">
            🤖 AI 채팅으로 여행 계획하기
          </h2>
          <p className="text-gray-600 mb-6">
            현재 위치를 기반으로 AI가 맞춤형 추천을 해드립니다. 지도에서 바로 확인하세요!
          </p>
          
          <div className="text-center">
            <Link
              href="/chat"
              className="bg-blue-600 text-white px-8 py-4 rounded-lg hover:bg-blue-700 transition-colors inline-block text-lg font-semibold"
            >
              🗣️ AI와 채팅 시작하기
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}