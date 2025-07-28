from flask import Flask, render_template, request, jsonify
import googlemaps
from ultra_search import ultra_search_keywords
from distance_utils import filter_by_distance
import os
from dotenv import load_dotenv
import time
# ThreadPoolExecutor는 현재 사용하지 않지만 향후 확장을 위해 유지
# from concurrent.futures import ThreadPoolExecutor, as_completed

# Load environment variables
load_dotenv()

app = Flask(__name__)

# 🎯 검색 설정 - 여기서 한 번에 관리
SEARCH_RADIUS = 500  # meters - 여기서만 수정하면 모든 곳에 적용됨!

# Other Constants  
DEFAULT_LOCATION = "Tokyo, Japan"
DEFAULT_PORT = 5001
GOOGLE_API_DELAY = 2  # seconds
MAX_WORKERS = 5

# API Cost Constants (USD) - 2025년 최신 요금
PLACES_API_COST = 0.032  # Nearby Search: $32 per 1,000 requests = $0.032 per request
GEOCODING_API_COST = 0.005  # Geocoding은 기존 유지
DETAILS_API_COST = 0.017  # Details는 기존 유지  
USD_TO_KRW = 1380  # 2025년 1월 평균 환율

class UltraSearchService:
    def __init__(self):
        api_key = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not api_key:
            raise ValueError("Google Maps API key not found")
        self.gmaps = googlemaps.Client(key=api_key)
        
        # API cost tracking
        self.api_calls = 0
        self.cost_per_call = PLACES_API_COST
        self.geocoding_cost = GEOCODING_API_COST
        self.details_cost = DETAILS_API_COST
    
    def geocode_location(self, location_str: str) -> tuple:
        """Convert location string to lat/lng coordinates"""
        try:
            geocode_start = time.time()
            
            # GPS 좌표가 이미 있으면 바로 사용
            if ',' in location_str and len(location_str.split(',')) == 2:
                try:
                    parts = location_str.split(',')
                    lat_str = parts[0].strip()
                    lng_str = parts[1].strip()
                    lat, lng = float(lat_str), float(lng_str)
                    geocode_time = time.time() - geocode_start
                    print(f"[TIMING] GPS 좌표 사용: {geocode_time:.3f}초")
                    return (lat, lng)
                except ValueError:
                    # GPS 좌표가 아니면 에러
                    raise ValueError(f"잘못된 GPS 좌표 형식: {location_str}")
            
            result = self.gmaps.geocode(location_str)
            self.api_calls += 1  # Track geocoding call
            geocode_time = time.time() - geocode_start
            print(f"[TIMING] 지오코딩 API 호출: {geocode_time:.3f}초")
            
            if not result or len(result) == 0:
                raise ValueError(f"지오코딩 실패: {location_str}")
            
            try:
                loc = result[0]['geometry']['location']
                return (loc['lat'], loc['lng'])
            except (KeyError, IndexError) as e:
                raise ValueError(f"지오코딩 결과 파싱 실패: {e}")
        except Exception as e:
            raise ValueError(f"지오코딩 에러: {e}")
    
    # Place Details API removed to minimize costs
    # def get_place_details(self, place_id: str) -> dict:
    #     """Get detailed information about a place using Place Details API"""
    #     # This function is disabled to reduce API costs
    #     return {}
    
    def search_by_types(self, place_types: list, latlng: tuple, radius: int):
        """Search using Google Maps API type parameter"""
        all_results = []
        seen_places = set()
        
        for place_type in place_types:
            try:
                print(f"[DEBUG] places_nearby type 검색: {place_type}")
                places_result = self.gmaps.places_nearby(
                    location=latlng,
                    radius=radius,
                    type=place_type
                )
                self.api_calls += 1
                
                results = places_result.get('results', [])
                print(f"[DEBUG] {place_type} 1페이지 검색 결과: {len(results)}개")
                
                # next_page_token 처리 - 모든 페이지 가져오기
                next_token = places_result.get('next_page_token')
                page_count = 1
                
                while next_token:
                    time.sleep(GOOGLE_API_DELAY)
                    try:
                        next_result = self.gmaps.places_nearby(
                            page_token=next_token,
                            location=latlng,
                            radius=radius,
                            type=place_type
                        )
                        self.api_calls += 1
                        next_results = next_result.get('results', [])
                        results.extend(next_results)
                        next_token = next_result.get('next_page_token')
                        page_count += 1
                        print(f"[DEBUG] {place_type} {page_count}페이지: {len(next_results)}개 추가")
                    except Exception as e:
                        print(f"[ERROR] {place_type} next page error: {e}")
                        break
                
                for result in results:
                    place_id = result.get('place_id', '')
                    if place_id and place_id not in seen_places:
                        geometry = result.get('geometry', {})
                        location_data = geometry.get('location', {})
                        lat = location_data.get('lat')
                        lng = location_data.get('lng')
                        
                        if lat and lng and lat != 0 and lng != 0:
                            place_data = {
                                'name': result.get('name', 'Unknown'),
                                'rating': result.get('rating', 'N/A'),
                                'address': result.get('vicinity', result.get('formatted_address', 'Unknown')),
                                'lat': lat,
                                'lng': lng,
                                'types': result.get('types', []),
                                'price_level': result.get('price_level', 'N/A'),
                                'place_id': place_id,
                                'search_term': place_type,
                                'search_radius': radius,
                                'distance_meters': result.get('distance_meters', 'N/A')
                            }
                            all_results.append(place_data)
                            seen_places.add(place_id)
                            
            except Exception as e:
                print(f"[ERROR] {place_type} 검색 실패: {e}")
                continue
        
        return all_results
    
    def search_places_batch(self, queries: list, location: str = DEFAULT_LOCATION, radius: int = SEARCH_RADIUS, place_types: list = None):
        """Search for places using multiple keywords in optimized batches"""
        print(f"[DEBUG] search_places_batch 호출됨 - radius: {radius}m")
        latlng = self.geocode_location(location)
        
        # Use place_types if provided, otherwise use keyword search
        if place_types:
            print(f"[DEBUG] place_types로 검색: {place_types}")
            return self.search_by_types(place_types, latlng, radius)
        
        # Combine queries into a single search to reduce API calls
        if not queries:
            print(f"[DEBUG] 빈 queries 리스트 - 검색 스킵")
            return []
        combined_query = ' OR '.join(queries[:5])  # Limit to top 5 keywords
        
        all_results = []
        seen_places = set()
        
        try:
            # 1. places_nearby 검색 (페이지네이션 포함)
            all_api_results = []
            
            print(f"[DEBUG] places_nearby 호출: location={latlng}, radius={radius}, keyword='{combined_query}'")
            places_result = self.gmaps.places_nearby(
                location=latlng,
                radius=radius,
                keyword=combined_query
            )
            self.api_calls += 1
            nearby_results = places_result.get('results', [])
            all_api_results.extend(nearby_results)
            
            # next_page_token 처리 - 모든 페이지 가져오기
            next_token = places_result.get('next_page_token')
            page_count = 1
            
            while next_token:
                time.sleep(GOOGLE_API_DELAY)
                try:
                    next_result = self.gmaps.places_nearby(
                        page_token=next_token,
                        location=latlng,
                        radius=radius,
                        keyword=combined_query
                    )
                    self.api_calls += 1
                    next_results = next_result.get('results', [])
                    all_api_results.extend(next_results)
                    next_token = next_result.get('next_page_token')
                    page_count += 1
                except Exception as e:
                    print(f"Next page error: {e}")
                    break
            
            nearby_results = all_api_results
            
            # 2. places 텍스트 검색 (더 포괄적, 페이지네이션 포함)
            try:
                print(f"[DEBUG] places 텍스트 검색 호출: query='{combined_query}', location={latlng}, radius={radius}")
                text_result = self.gmaps.places(
                    query=combined_query,
                    location=latlng,
                    radius=radius
                )
                self.api_calls += 1
                text_results = text_result.get('results', [])
                
                # next_page_token 처리 for text search - 모든 페이지 가져오기
                next_token = text_result.get('next_page_token')
                page_count = 1
                
                while next_token:
                    time.sleep(GOOGLE_API_DELAY)
                    try:
                        next_result = self.gmaps.places(
                            page_token=next_token,
                            location=latlng,
                            radius=radius,
                            query=combined_query
                        )
                        self.api_calls += 1
                        next_page_results = next_result.get('results', [])
                        text_results.extend(next_page_results)
                        next_token = next_result.get('next_page_token')
                        page_count += 1
                    except Exception as e:
                        print(f"Text search next page error: {e}")
                        break
                
                # 두 결과 합치기
                all_api_results = nearby_results + text_results
            except:
                all_api_results = nearby_results
            
            # 🎯 거리 기준 필터링 적용
            center_lat, center_lng = latlng
            print(f"[FILTER] 중심 좌표: ({center_lat}, {center_lng}), 반경: {radius}m")
            print(f"[FILTER] 필터링 전 결과: {len(all_api_results)}개")
            
            filtered_results = filter_by_distance(all_api_results, center_lat, center_lng, radius)
            print(f"[FILTER] 필터링 후 결과: {len(filtered_results)}개")
            
            # 필터링된 결과의 거리 정보 출력
            if filtered_results:
                distances = [r.get('distance_meters', 'N/A') for r in filtered_results[:5]]
                print(f"[FILTER] 처음 5개 거리: {distances}m")
            
            results = filtered_results
            
            # Filter results with valid coordinates and remove duplicates
            for result in results:
                place_id = result.get('place_id', '')
                if place_id and place_id not in seen_places:
                    geometry = result.get('geometry', {})
                    location_data = geometry.get('location', {})
                    lat = location_data.get('lat')
                    lng = location_data.get('lng')
                    
                    if lat and lng and lat != 0 and lng != 0:
                        place_data = {
                            'name': result.get('name', 'Unknown'),
                            'rating': result.get('rating', 'N/A'),
                            'address': result.get('vicinity', result.get('formatted_address', 'Unknown')),
                            'lat': lat,
                            'lng': lng,
                            'types': result.get('types', []),
                            'price_level': result.get('price_level', 'N/A'),
                            'place_id': place_id,
                            'search_term': combined_query,
                            'search_radius': radius,
                            'distance_meters': result.get('distance_meters', 'N/A')  # 거리 정보 추가
                        }
                        all_results.append(place_data)
                        seen_places.add(place_id)
            
            valid_results = all_results
            
            return valid_results
        except Exception as e:
            print(f"Search error: {e}")
            return []




    
    def search_with_keywords(self, korean_text: str, location: str = DEFAULT_LOCATION, radius: int = SEARCH_RADIUS):
        """Search using ultra_search keywords with configurable radius and individual category searches"""
        try:
            total_search_start = time.time()
            
            # Reset API call counter for this search
            initial_api_calls = self.api_calls
            self.api_calls = 0
            
            # Get keywords from ultra_search
            keyword_start = time.time()
            try:
                keywords_result = ultra_search_keywords(korean_text)
                keyword_time = time.time() - keyword_start
                print(f"[TIMING] 키워드 생성 전체: {keyword_time:.3f}초")
                print(f"[DEBUG] 키워드 생성 결과: {keywords_result}")
            except Exception as e:
                print(f"[ERROR] 키워드 생성 실패: {e}")
                import traceback
                traceback.print_exc()
                return {"error": f"키워드 생성 실패: {str(e)}"}, []
            
            if not keywords_result.get("has_location_intent"):
                print("[DEBUG] 장소 검색 의도가 감지되지 않음")
                return {"error": "장소 검색 의도가 감지되지 않았습니다"}, []
            
            all_results = []
            seen_places = set()
            
            # 키워드별로 분리
            direct_keywords = keywords_result.get("direct_translation", [])
            abstract_keywords = keywords_result.get("abstract_translation", [])
            place_types = keywords_result.get("place_types", [])
            
            print(f"[DEBUG] Keywords result type: {type(keywords_result)}")
            print(f"[DEBUG] Direct keywords: {direct_keywords} (len: {len(direct_keywords)})")
            print(f"[DEBUG] Abstract keywords: {abstract_keywords} (len: {len(abstract_keywords)})")
            print(f"[DEBUG] Place types: {place_types} (len: {len(place_types)})")
            
            # 🎯 최적화된 검색 로직: 추상키워드 3,4,5개씩 + place_type 3개 = 총 9번 호출
            search_timings = {}
            
            # 추상키워드 3,4,5개씩 + place_type 3개 조합 검색
            if place_types and abstract_keywords:
                combo_start = time.time()
                print(f"[SEARCH] 6개씩 2번 검색: place_type 3개 × 2회 = 총 6번 호출 (pagination 포함 최대 18번)")
                
                # place_types를 3개로 제한
                limited_place_types = place_types[:3]
                print(f"[DEBUG] 사용할 place_types: {limited_place_types}")
                
                # 6개씩 2번 나누기
                chunk_1 = abstract_keywords[:6]  # 처음 6개
                chunk_2 = abstract_keywords[6:12] if len(abstract_keywords) > 6 else abstract_keywords[:6]  # 다음 6개 (없으면 처음 6개 재사용)
                chunks = [chunk_1, chunk_2]
                
                search_count = 0
                for round_num, chunk in enumerate(chunks, 1):
                    for place_type in limited_place_types:
                        search_count += 1
                        try:
                            print(f"[SEARCH {search_count}/6] {place_type} + 6개 키워드 ({round_num}차): {chunk[:6]}")
                            
                            # Place type으로 검색
                            type_results = self.search_by_types([place_type], self.geocode_location(location), radius)
                            
                            print(f"[RESULT {search_count}/6] {place_type}: {len(type_results)}개")
                            
                            for result in type_results:
                                if result['place_id'] not in seen_places:
                                    result['search_type'] = f'{place_type}_round{round_num}'
                                    all_results.append(result)
                                    seen_places.add(result['place_id'])
                                    
                        except Exception as exc:
                            print(f"[ERROR {search_count}/6] {place_type} 검색 실패: {exc}")
                
                combo_time = time.time() - combo_start
                search_timings['optimized_6x2_search'] = f"{combo_time:.3f}초"
                
                # 실제 API 호출 수 출력
                print(f"[API CALLS] 실제 호출 수: {self.api_calls}번 (geocoding 제외)")
                print(f"[API CALLS] 예상 최대: 18번, 실제: {self.api_calls}번")
            
            # Sort by distance if user location is coordinates
            if ',' in location:
                try:
                    user_lat, user_lng = map(float, location.split(','))
                    for result in all_results:
                        lat, lng = result['lat'], result['lng']
                        # Calculate distance
                        import math
                        R = 6371  # Earth's radius in km
                        dlat = math.radians(lat - user_lat)
                        dlon = math.radians(lng - user_lng)
                        a = (math.sin(dlat/2) * math.sin(dlat/2) + 
                             math.cos(math.radians(user_lat)) * math.cos(math.radians(lat)) * 
                             math.sin(dlon/2) * math.sin(dlon/2))
                        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
                        result['distance'] = R * c
                    
                    # Sort by distance
                    all_results.sort(key=lambda x: x.get('distance', float('inf')))
                except ValueError:
                    pass
            
            # Show all results without limit
            print(f"[TIMING] 총 {len(all_results)}개의 검색 결과 표시")
            
            # Calculate costs and timing
            geocoding_calls = 1 if ',' not in location else 0  # GPS 좌표면 지오코딩 안함
            total_cost = (self.api_calls * self.cost_per_call) + (geocoding_calls * self.geocoding_cost)
            total_search_time = time.time() - total_search_start
            
            print(f"[TIMING] 전체 검색 프로세스 완료: {total_search_time:.3f}초")
            print(f"[API SUMMARY] 검색 API: {self.api_calls}번, 지오코딩: {geocoding_calls}번, 총: {self.api_calls + geocoding_calls}번")
            print(f"[COST] 총 비용: ${round(total_cost, 4)} (약 {round(total_cost * USD_TO_KRW, 0)}원)")
            print(f"[COST] 세부: Places API {self.api_calls}회 × $0.032 + 지오코딩 {geocoding_calls}회 × $0.005")
            
            # Add cost and timing information to keywords_result
            keywords_result['api_calls'] = self.api_calls
            keywords_result['geocoding_calls'] = geocoding_calls
            keywords_result['total_api_calls'] = self.api_calls + geocoding_calls
            keywords_result['estimated_cost_usd'] = round(total_cost, 4)
            keywords_result['estimated_cost_krw'] = round(total_cost * USD_TO_KRW, 0)
            keywords_result['search_strategy'] = f'{radius}m Radius with Optimized 6x2 Search'
            
            # Add detailed timing information
            keywords_result['search_timing'] = {
                'total_search_time': round(total_search_time, 3),
                'keyword_generation_time': round(keyword_time, 3),
                'api_search_time': round(total_search_time - keyword_time, 3),
                'detailed_timings': search_timings
            }
            
            return keywords_result, all_results  # Return all results found
            
        except Exception as e:
            print(f"Keywords search error: {e}")
            return {"error": str(e)}, []
    
    def get_cost_info(self):
        """Get current API usage and cost information"""
        total_cost = (self.api_calls * self.cost_per_call)
        return {
            'api_calls': self.api_calls,
            'cost_usd': round(total_cost, 4),
            'cost_krw': round(total_cost * USD_TO_KRW, 0)
        }

# Initialize service
search_service = UltraSearchService()

@app.route('/')
def index():
    return render_template('ultra_search.html')

@app.route('/search', methods=['POST'])
def search():
    data = request.json
    korean_text = data.get('korean_text', '')
    location = data.get('location', DEFAULT_LOCATION)
    radius = data.get('radius', SEARCH_RADIUS)
    
    print(f"[DEBUG] 받은 요청 데이터: {data}")
    print(f"[DEBUG] Korean text: '{korean_text}'")
    print(f"[DEBUG] Location: '{location}'")
    print(f"[DEBUG] Radius: {radius} (type: {type(radius)})")
    
    if not korean_text:
        return jsonify({'error': 'Korean text is required'}), 400
    
    try:
        keywords_result, places = search_service.search_with_keywords(korean_text, location, radius)
        
        return jsonify({
            'keywords': keywords_result,
            'places': places,
            'total_results': len(places)
        })
    except Exception as e:
        print(f"[ERROR] search_with_keywords 실행 중 에러: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': 'Search failed',
            'message': str(e),
            'keywords': {},
            'places': [],
            'total_results': 0
        }), 500

@app.route('/api/key')
def get_api_key():
    # For frontend Google Maps
    return jsonify({'api_key': os.getenv('GOOGLE_CLOUD_PROJECT')})

if __name__ == '__main__':
    app.run(debug=True, port=DEFAULT_PORT)