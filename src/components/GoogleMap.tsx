'use client'

import { useEffect, useRef, useState } from 'react'
import { Loader } from '@googlemaps/js-api-loader'

interface GoogleMapProps {
  location: { lat: number; lng: number } | null
  keywords: string[]
}

export default function GoogleMap({ location, keywords }: GoogleMapProps) {
  const mapRef = useRef<HTMLDivElement>(null)
  const [map, setMap] = useState<google.maps.Map | null>(null)
  const [isLoaded, setIsLoaded] = useState(false)

  useEffect(() => {
    const initializeMap = async () => {
      const loader = new Loader({
        apiKey: process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY!,
        version: 'weekly',
        libraries: ['places']
      })

      const google = await loader.load()
      
      if (mapRef.current && location) {
        const mapInstance = new google.maps.Map(mapRef.current, {
          center: location,
          zoom: 15,
          styles: [
            {
              featureType: 'poi',
              elementType: 'labels',
              stylers: [{ visibility: 'on' }]
            }
          ]
        })

        // 현재 위치 마커
        new google.maps.Marker({
          position: location,
          map: mapInstance,
          title: '내 위치',
          icon: {
            url: 'https://maps.google.com/mapfiles/ms/icons/blue-dot.png'
          }
        })

        setMap(mapInstance)
        setIsLoaded(true)
      }
    }

    if (location && !isLoaded) {
      initializeMap()
    }
  }, [location, isLoaded])

  useEffect(() => {
    if (map && keywords.length > 0 && location) {
      // 기존 마커들 제거 (현재 위치 마커 제외)
      const service = new google.maps.places.PlacesService(map)
      
      keywords.forEach((keyword, index) => {
        const request = {
          query: keyword,
          location: location,
          radius: 2000,
          fields: ['name', 'geometry', 'formatted_address', 'rating']
        }

        service.textSearch(request, (results, status) => {
          if (status === google.maps.places.PlacesServiceStatus.OK && results) {
            results.slice(0, 5).forEach((place, placeIndex) => {
              if (place.geometry?.location) {
                const marker = new google.maps.Marker({
                  position: place.geometry.location,
                  map: map,
                  title: place.name,
                  icon: {
                    url: `https://maps.google.com/mapfiles/ms/icons/${
                      ['red', 'green', 'yellow', 'purple', 'orange'][index % 5]
                    }-pushpin.png`
                  }
                })

                const infoWindow = new google.maps.InfoWindow({
                  content: `
                    <div>
                      <h3 style="margin: 0 0 8px 0; font-weight: bold;">${place.name}</h3>
                      <p style="margin: 0 0 4px 0; color: #666;">${place.formatted_address || ''}</p>
                      ${place.rating ? `<p style="margin: 0; color: #f59e0b;">★ ${place.rating}</p>` : ''}
                    </div>
                  `
                })

                marker.addListener('click', () => {
                  infoWindow.open(map, marker)
                })
              }
            })
          }
        })
      })
    }
  }, [map, keywords, location])

  if (!location) {
    return (
      <div className="w-full h-96 bg-gray-100 rounded-lg flex items-center justify-center">
        <p className="text-gray-500">위치 정보가 필요합니다</p>
      </div>
    )
  }

  return (
    <div className="w-full h-96 bg-gray-100 rounded-lg overflow-hidden">
      <div ref={mapRef} className="w-full h-full" />
    </div>
  )
}