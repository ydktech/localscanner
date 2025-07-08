'use client'

import { useState, useEffect } from 'react'
import { Send, Bot, User, MapPin } from 'lucide-react'
import { ChatMessage } from '@/types'
import GoogleMap from './GoogleMap'

export default function ChatInterface() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [location, setLocation] = useState<{ lat: number; lng: number } | null>(null)
  const [keywords, setKeywords] = useState<string[]>([])

  useEffect(() => {
    // 위치 정보 가져오기
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setLocation({
            lat: position.coords.latitude,
            lng: position.coords.longitude,
          })
        },
        (error) => {
          console.error('위치 정보를 가져올 수 없습니다:', error)
        }
      )
    }
  }, [])

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      content: input,
      role: 'user',
      timestamp: new Date(),
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: input, location }),
      })

      const data = await response.json()

      if (response.ok) {
        const assistantMessage: ChatMessage = {
          id: (Date.now() + 1).toString(),
          content: data.response,
          role: 'assistant',
          timestamp: new Date(),
        }
        setMessages(prev => [...prev, assistantMessage])
        
        // 키워드가 있으면 지도에 표시
        if (data.keywords && data.keywords.length > 0) {
          setKeywords(data.keywords)
        }
        
        // 검색 결과와 주소 정보 로깅 (디버깅용)
        if (data.locationInfo) {
          console.log('위치 정보:', data.locationInfo.formatted_address)
        }
        if (data.places) {
          console.log('검색된 장소들:', data.places.length, '개')
        }
      } else {
        console.error('API error:', data.error)
      }
    } catch (error) {
      console.error('Error sending message:', error)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-full">
      {/* 채팅 영역 */}
      <div className="flex flex-col h-full">
        <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-white rounded-lg">
          {location && (
            <div className="bg-blue-50 p-3 rounded-lg mb-4">
              <div className="flex items-center space-x-2 text-blue-800">
                <MapPin size={16} />
                <span className="text-sm">위치: {location.lat.toFixed(4)}, {location.lng.toFixed(4)}</span>
              </div>
            </div>
          )}
          
          {messages.length === 0 ? (
            <div className="text-center text-gray-500 py-8">
              <Bot className="mx-auto mb-4" size={48} />
              <p>AI 여행 어시스턴트와 대화를 시작해보세요!</p>
              <p className="text-sm mt-2">예: "주변 맛집 추천해주세요" 또는 "근처 관광지 알려주세요"</p>
            </div>
          ) : (
            messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-3xl px-4 py-2 rounded-lg ${
                    message.role === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-800'
                  }`}
                >
                  <div className="flex items-start space-x-2">
                    {message.role === 'assistant' && <Bot size={20} className="mt-1" />}
                    {message.role === 'user' && <User size={20} className="mt-1" />}
                    <div className="flex-1">
                      <p className="whitespace-pre-wrap">{message.content}</p>
                    </div>
                  </div>
                </div>
              </div>
            ))
          )}
          {isLoading && (
            <div className="flex justify-start">
              <div className="max-w-3xl px-4 py-2 rounded-lg bg-gray-100 text-gray-800">
                <div className="flex items-center space-x-2">
                  <Bot size={20} />
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        <form onSubmit={sendMessage} className="border-t p-4">
          <div className="flex space-x-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="근처 맛집, 관광지, 여행 팁에 대해 물어보세요..."
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={isLoading}
            />
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Send size={20} />
            </button>
          </div>
        </form>
      </div>

      {/* 지도 영역 */}
      <div className="flex flex-col h-full">
        <div className="bg-white rounded-lg p-4 h-full">
          <h3 className="text-lg font-semibold mb-4 text-gray-800">추천 장소 지도</h3>
          {keywords.length > 0 && (
            <div className="mb-4">
              <p className="text-sm text-gray-600 mb-2">검색 키워드:</p>
              <div className="flex flex-wrap gap-2">
                {keywords.map((keyword, index) => (
                  <span key={index} className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                    {keyword}
                  </span>
                ))}
              </div>
            </div>
          )}
          <GoogleMap location={location} keywords={keywords} />
        </div>
      </div>
    </div>
  )
}