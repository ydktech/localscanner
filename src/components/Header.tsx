'use client'

import { useState } from 'react'
import Link from 'next/link'
import { MapPin, MessageCircle, Search, Menu, X } from 'lucide-react'

export default function Header() {
  const [isMenuOpen, setIsMenuOpen] = useState(false)

  return (
    <header className="bg-white shadow-sm border-b">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center py-4">
          <div className="flex items-center">
            <Link href="/" className="text-2xl font-bold text-blue-600">
              LocalScanner
            </Link>
          </div>

          <nav className="hidden md:flex space-x-8">
            <Link
              href="/chat"
              className="flex items-center space-x-1 text-gray-700 hover:text-blue-600"
            >
              <MessageCircle size={20} />
              <span>AI 채팅</span>
            </Link>
          </nav>

          <div className="md:hidden">
            <button
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className="text-gray-700 hover:text-blue-600"
            >
              {isMenuOpen ? <X size={24} /> : <Menu size={24} />}
            </button>
          </div>
        </div>

        {isMenuOpen && (
          <div className="md:hidden">
            <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3">
              <Link
                href="/chat"
                className="flex items-center space-x-2 text-gray-700 hover:text-blue-600 block px-3 py-2 rounded-md text-base font-medium"
              >
                <MessageCircle size={20} />
                <span>AI 채팅</span>
              </Link>
            </div>
          </div>
        )}
      </div>
    </header>
  )
}