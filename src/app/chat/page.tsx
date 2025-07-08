import ChatInterface from '@/components/ChatInterface'

export default function ChatPage() {
  return (
    <div className="h-full bg-gray-50">
      <div className="max-w-6xl mx-auto px-4 py-8">
        <div className="text-center mb-6">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">AI 여행 어시스턴트</h1>
          <p className="text-gray-600">
            맛집, 관광지, 로컬 체험에 대한 맞춤형 추천을 받아보세요
          </p>
        </div>
        
        <div className="bg-white rounded-lg shadow-lg h-[600px]">
          <ChatInterface />
        </div>
      </div>
    </div>
  )
}