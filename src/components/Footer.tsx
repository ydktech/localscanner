export default function Footer() {
  return (
    <footer className="bg-gray-50 border-t">
      <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        <div className="text-center">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">LocalScanner AI 여행 어시스턴트</h3>
            <p className="text-gray-600">
              AI 채팅으로 주변 맛집, 카페, 관광지를 쉽게 발견하고 지도에서 확인하세요
            </p>
          </div>
        </div>
        <div className="mt-8 pt-8 border-t border-gray-200">
          <p className="text-center text-gray-500">
            © 2024 LocalScanner. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  )
}