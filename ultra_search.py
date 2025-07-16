import vertexai
from vertexai.generative_models import GenerativeModel, FunctionDeclaration, Tool
import os
import json

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/Users/ydk/eastbase/google_test/hotba-456006-a2cf612b8582.json'

def ultra_search_keywords(korean_text):
    try:
        vertexai.init(project="hotba-456006", location="us-central1")
        model = GenerativeModel('gemini-2.5-flash')
        
        # Function declaration
        generate_keywords_func = FunctionDeclaration(
            name="generate_keywords",
            description="Generate Japanese keywords for Google Maps search",
            parameters={
                "type": "object",
                "properties": {
                    "direct_translation": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "직접적인 번역 키워드들"
                    },
                    "abstract_translation": {
                        "type": "array", 
                        "items": {"type": "string"},
                        "description": "추상적/간접적 장소 유형 키워드들 - 관련성 높은 순서대로 정렬, 실제 목적 달성 가능성이 있는 곳들만"
                    },
                    "filter_keywords": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Google Maps 상세검색 필터용 키워드들 - 실제 검색에 도움되는 것들만 (예: 食事, ランチ, テーブル サービス, 軽食, 人気, ランチに人気)"
                    }
                },
                "required": ["direct_translation", "abstract_translation", "filter_keywords"]
            }
        )
        
        tool = Tool(function_declarations=[generate_keywords_func])
        
        prompt = f"""
사용자가 찾고자 하는 장소를 Google Maps/Places API에서 검색할 일본어 키워드를 생성해 주세요.

1. **direct_translation**: 사용자가 말한 것에 대해 직접 번역(의역)되는 키워드들 (5-8개)
    - 부가적인 조건(예: 고양이, 낮잠 등)은 제거하고, 장소 유형 중심으로 정리
    - 예:
        - 고양이가 출몰하는 공원 → 公園
        - 낮잠 잘 수 있는 곳 → お昼寝スペース, 休憩スペース
2. **abstract_translation**: 해당 목적을 달성할 수 있는 간접적인 장소 유형들 (8-12개)
   - 직접 번역에 포함되지 않는 것만 출력
   - 관련성이 높은 순서대로 정렬해서 출력
   - 맛집이면 그냥 음식점을 출력하는 게 아니라 다양한 식사 가능한 곳들
   - 카페면 디저트 카페, 브런치 카페, 로스터리, 티룸 등 다양한 카페 유형들
   - 실제로 해당 목적을 달성할 가능성이 높고 구글 맵에 있을거 같은 검색 가능한 구체적인 장소 유형들만
3. **filter_keywords**: 실제 장소 검색에 도움되는 가장 적절한 필터 (1개)
   - 예: 食事, ランチ, テーブル サービス, 軽食, 人気, ランチに人気, サービス 등
   - 예약, 개실 같은 부차적인 것들 말고 실제 검색 결과에 영향주는 것

사용자 입력: 「{korean_text}」

최대한 많은 키워드를 생성해서 검색 누락을 방지하세요. generate_keywords 함수를 호출해서 결과를 반환하세요.
"""
        
        response = model.generate_content(prompt, tools=[tool])
        
        if response.candidates[0].content.parts[0].function_call:
            function_call = response.candidates[0].content.parts[0].function_call
            args = function_call.args
            
            direct_translation = args.get('direct_translation', [])
            abstract_translation = args.get('abstract_translation', [])
            filter_keywords = args.get('filter_keywords', [])
            
            all_search_keywords = direct_translation + abstract_translation
            
            if all_search_keywords:
                return {
                    "has_location_intent": True,
                    "direct_translation": direct_translation,
                    "abstract_translation": abstract_translation,
                    "filter_keywords": filter_keywords,
                    "keywords": all_search_keywords  # 기존 호환성
                }
            else:
                return {"has_location_intent": False, "direct_translation": [], "abstract_translation": [], "filter_keywords": [], "keywords": []}
        else:
            return {"has_location_intent": False, "direct_translation": [], "abstract_translation": [], "filter_keywords": [], "keywords": []}
        
    except Exception as e:
        raise e

def main():
    print("🚀 Ultra Search - 절대 놓치지 않는 검색기")
    print("종료하려면 'quit' 입력")
    print("-" * 50)
    
    while True:
        try:
            korean_input = input("\n한국어 검색어: ")
        except (EOFError, KeyboardInterrupt):
            break
        
        if korean_input.lower() == 'quit':
            break
            
        try:
            result = ultra_search_keywords(korean_input)
            if result["has_location_intent"]:
                print(f"\n🎯 직접 번역 ({len(result['direct_translation'])}개):")
                print(result['direct_translation'])
                print(f"\n🔄 추상적 번역 ({len(result['abstract_translation'])}개):")
                print(result['abstract_translation'])
                print(f"\n🔧 필터 키워드 ({len(result['filter_keywords'])}개):")
                print(result['filter_keywords'])
            else:
                print("❌ 장소 검색 의도가 감지되지 않았습니다.")
        except Exception as e:
            print(f"오류 발생: {e}")

if __name__ == "__main__":
    main()