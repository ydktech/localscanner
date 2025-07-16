from flask import Flask, render_template, request, jsonify
import googlemaps
from ultra_search import ultra_search_keywords
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

class UltraSearchService:
    def __init__(self):
        api_key = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not api_key:
            raise ValueError("Google Maps API key not found")
        self.gmaps = googlemaps.Client(key=api_key)
        
        # API cost tracking
        self.api_calls = 0
        self.cost_per_call = 0.017  # $0.017 per Places API call
        self.geocoding_cost = 0.005  # $0.005 per Geocoding call
    
    def geocode_location(self, location_str: str) -> tuple:
        """Convert location string to lat/lng coordinates"""
        try:
            # Skip geocoding if already coordinates
            if ',' in location_str and len(location_str.split(',')) == 2:
                try:
                    lat, lng = map(float, location_str.split(','))
                    return (lat, lng)
                except ValueError:
                    pass
            
            result = self.gmaps.geocode(location_str)
            self.api_calls += 1  # Track geocoding call
            
            if not result:
                return (35.6762, 139.6503)  # Default Tokyo
            
            loc = result[0]['geometry']['location']
            return (loc['lat'], loc['lng'])
        except Exception as e:
            print(f"Geocoding error: {e}")
            return (35.6762, 139.6503)
    
    def search_places_batch(self, queries: list, location: str = "Tokyo, Japan", radius: int = 5000):
        """Search for places using multiple keywords in optimized batches"""
        latlng = self.geocode_location(location)
        
        # Combine queries into a single search to reduce API calls
        combined_query = ' OR '.join(queries[:5])  # Limit to top 5 keywords
        
        try:
            places_result = self.gmaps.places_nearby(
                location=latlng,
                radius=radius,
                keyword=combined_query
            )
            
            self.api_calls += 1  # Track API call
            
            results = places_result.get('results', [])
            
            # Filter results with valid coordinates
            valid_results = []
            for result in results:
                geometry = result.get('geometry', {})
                location_data = geometry.get('location', {})
                lat = location_data.get('lat')
                lng = location_data.get('lng')
                
                if lat and lng and lat != 0 and lng != 0:
                    place_data = {
                        'name': result.get('name', 'Unknown'),
                        'rating': result.get('rating', 'N/A'),
                        'address': result.get('vicinity', 'Unknown'),
                        'lat': lat,
                        'lng': lng,
                        'types': result.get('types', []),
                        'price_level': result.get('price_level', 'N/A'),
                        'place_id': result.get('place_id', ''),
                        'search_term': combined_query
                    }
                    valid_results.append(place_data)
            
            return valid_results
        except Exception as e:
            print(f"Search error: {e}")
            return []

    def search_places(self, query: str, location: str = "Tokyo, Japan", radius: int = 5000):
        """Search for places using Google Maps Places API"""
        latlng = self.geocode_location(location)
        
        try:
            places_result = self.gmaps.places_nearby(
                location=latlng,
                radius=radius,
                keyword=query
            )
            
            self.api_calls += 1  # Track API call
            
            results = places_result.get('results', [])
            
            # Filter results with valid coordinates
            valid_results = []
            for result in results:
                geometry = result.get('geometry', {})
                location_data = geometry.get('location', {})
                lat = location_data.get('lat')
                lng = location_data.get('lng')
                
                if lat and lng and lat != 0 and lng != 0:
                    place_data = {
                        'name': result.get('name', 'Unknown'),
                        'rating': result.get('rating', 'N/A'),
                        'address': result.get('vicinity', 'Unknown'),
                        'lat': lat,
                        'lng': lng,
                        'types': result.get('types', []),
                        'price_level': result.get('price_level', 'N/A'),
                        'place_id': result.get('place_id', '')
                    }
                    valid_results.append(place_data)
            
            return valid_results
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    def search_with_keywords(self, korean_text: str, location: str = "Tokyo, Japan", radius: int = 5000):
        """Search using ultra_search keywords with optimized batch processing"""
        try:
            # Reset API call counter for this search
            self.api_calls = 0
            
            # Get keywords from ultra_search
            keywords_result = ultra_search_keywords(korean_text)
            
            if not keywords_result.get("has_location_intent"):
                return {"error": "장소 검색 의도가 감지되지 않았습니다"}, []
            
            all_results = []
            
            # 1. Direct translation batch search
            direct_keywords = keywords_result.get("direct_translation", [])
            if direct_keywords:
                direct_results = self.search_places_batch(direct_keywords, location, radius)
                for result in direct_results:
                    result['search_type'] = 'Direct Translation'
                all_results.extend(direct_results)
            
            # 2. Abstract translation with filter keywords batch search
            abstract_keywords = keywords_result.get("abstract_translation", [])
            filter_keywords = keywords_result.get("filter_keywords", [])
            
            if abstract_keywords and filter_keywords:
                # Combine abstract keywords with filter keywords
                abstract_with_filter = []
                for abstract_kw in abstract_keywords:
                    for filter_kw in filter_keywords:
                        abstract_with_filter.append(f"{abstract_kw} {filter_kw}")
                
                abstract_results = self.search_places_batch(abstract_with_filter, location, radius)
                for result in abstract_results:
                    result['search_type'] = 'Abstract Translation + Filter'
                all_results.extend(abstract_results)
            
            # Remove duplicates by place_id
            unique_results = []
            seen_places = set()
            for result in all_results:
                place_id = result.get('place_id')
                if place_id and place_id not in seen_places:
                    seen_places.add(place_id)
                    unique_results.append(result)
            
            # Calculate costs
            total_cost = (self.api_calls * self.cost_per_call) + (1 * self.geocoding_cost)
            
            # Add cost information to keywords_result
            keywords_result['api_calls'] = self.api_calls
            keywords_result['estimated_cost_usd'] = round(total_cost, 4)
            keywords_result['estimated_cost_krw'] = round(total_cost * 1330, 0)  # USD to KRW
            
            return keywords_result, unique_results
            
        except Exception as e:
            print(f"Keywords search error: {e}")
            return {"error": str(e)}, []
    
    def get_cost_info(self):
        """Get current API usage and cost information"""
        total_cost = (self.api_calls * self.cost_per_call)
        return {
            'api_calls': self.api_calls,
            'cost_usd': round(total_cost, 4),
            'cost_krw': round(total_cost * 1330, 0)
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
    location = data.get('location', 'Tokyo, Japan')
    radius = data.get('radius', 5000)
    
    if not korean_text:
        return jsonify({'error': 'Korean text is required'}), 400
    
    keywords_result, places = search_service.search_with_keywords(korean_text, location, radius)
    
    return jsonify({
        'keywords': keywords_result,
        'places': places,
        'total_results': len(places)
    })

@app.route('/api/key')
def get_api_key():
    # For frontend Google Maps
    return jsonify({'api_key': os.getenv('GOOGLE_CLOUD_PROJECT')})

if __name__ == '__main__':
    app.run(debug=True, port=5000)