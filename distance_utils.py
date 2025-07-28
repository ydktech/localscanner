import math

def calculate_distance(lat1, lng1, lat2, lng2):
    """두 좌표 간의 거리를 미터 단위로 계산 (Haversine formula)"""
    R = 6371000  # 지구 반지름 (미터)
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lng = math.radians(lng2 - lng1)
    
    a = (math.sin(delta_lat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c

def filter_by_distance(results, center_lat, center_lng, max_distance_meters):
    """결과를 거리 기준으로 필터링"""
    filtered_results = []
    for result in results:
        try:
            place_lat = result['geometry']['location']['lat']
            place_lng = result['geometry']['location']['lng']
            distance = calculate_distance(center_lat, center_lng, place_lat, place_lng)
            
            if distance <= max_distance_meters:
                result['distance_meters'] = int(distance)  # 거리 정보 추가
                filtered_results.append(result)
            else:
                print(f"[FILTER] 제외: {result.get('name', 'Unknown')} - 거리: {int(distance)}m")
        except (KeyError, TypeError):
            # 좌표 정보가 없는 결과는 제외
            continue
    
    return filtered_results 