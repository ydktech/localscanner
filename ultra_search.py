import vertexai
from vertexai.generative_models import GenerativeModel, FunctionDeclaration, Tool
import os
import json
import time

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/Users/ydk/eastbase/google_test/hotba-456006-a2cf612b8582.json'

def ultra_search_keywords(korean_text):
    try:
        start_time = time.time()
        init_start = time.time()
        
        vertexai.init(project="hotba-456006", location="us-central1")
        model = GenerativeModel('gemini-2.5-flash')
        
        init_time = time.time() - init_start
        print(f"[TIMING] Vertex AI 초기화: {init_time:.3f}초")
        
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
                        "description": "직접적인 번역 키워드들 (5개)"
                    },
                    "abstract_translation": {
                        "type": "array", 
                        "items": {"type": "string"},
                        "description": "추상적/간접적 장소 유형 키워드들 (15개) - 관련성 높은 순서대로 정렬, 실제 목적 달성 가능성이 있는 곳들만"
                    },

                    "specific_names": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "사용자 입력에서 추출한 구체적인 장소명 (있다면 1-3개) - 예: CO-SIDE CAFE, 스타벅스, 맥도날드"
                    },
                    "place_types": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Google Maps API type 파라미터용 영어 키워드 (3-5개) - 예: restaurant, cafe, food, bakery, meal_takeaway"
                    }
                },
                "required": ["direct_translation", "abstract_translation", "specific_names", "place_types"]
            }
        )
        
        tool = Tool(function_declarations=[generate_keywords_func])
        
        prompt = f"""
당신은 20년의 경력을 가진 일본 현지 생활 전문가이자 Google Maps 검색 최적화 전문가입니다.
한국인이 일본 현지에서 원하는 목적을 달성할 수 있도록 일본어 키워드를 생성해주세요.

🚫 **절대 금지**: 한국어 키워드 생성 금지! 모든 출력은 100% 일본어만!
✅ **필수**: 히라가나(ひらがな), 가타카나(カタカナ), 한자(漢字)만 사용!

사용자 입력 : {korean_text}

1. **direct_translation**: 해당 목적을 달성할 수 있는 직접 번역 키워드 (3개)
   - 한국어를 일본어로 완전히 번역
   - 예시: 커피 한 잔 → コーヒー, 珈琲, 一杯のコーヒー, コーヒータイム, カフェドリンク

2. **abstract_translation**: 일본 현지에서 목적 달성 가능한 모든 추상적 간접 키워드 (12개)
   - 일본 현지인들이 실제로 자주 사용하는 검색어들
   - 일본 현지 문화와 실정을 고려한 다양한 장소 유형 포함
   - 가능한 모든 관련 키워드를 포함 (넓은 범위로 검색)
   - 해당 목적이 달성 가능할 확률이 높은 순서대로 출력
   - 예시: 커피→カフェ, 喫茶店, コーヒーショップ, 珈琲屋, カフェテリア, 喫茶, コーヒー専門店, カフェバー, コーヒースタンド, コーヒー, 珈琲, カフェレストラン, 飲食店
   - 예시: 아침식사→レストラン, カフェ, 喫茶店, ベーカリー, モーニング, ファミレス, ホテル

3. **place_types**: Google Maps API용 영어 장소 타입 (3개)
   - Google Maps API의 공식 type 파라미터에 사용할 영어 키워드
   - 목적 달성에 필요한 모든 장소 타입을 포함
   - 예시: 커피→cafe, restaurant, food
🔥 **최종 확인**: 한국어가 결과에 출력돼 있으면 실패! 100% 일본어만!
🎯 **핵심**: 일본 현지에서 실제로 목적을 달성할 수 있는 장소들만 선별!
generate_keywords 함수로 일본어 키워드만 반환하세요.
"""
        
        llm_start = time.time()
        response = model.generate_content(prompt, tools=[tool])
        llm_time = time.time() - llm_start
        print(f"[TIMING] LLM 키워드 생성: {llm_time:.3f}초")
        print(response)
        if (response.candidates and 
            len(response.candidates) > 0 and 
            response.candidates[0].content.parts and 
            len(response.candidates[0].content.parts) > 0 and 
            response.candidates[0].content.parts[0].function_call):
            
            function_call = response.candidates[0].content.parts[0].function_call
            args = function_call.args
            
            print(f"[DEBUG] LLM 응답 args: {args}")
            
            direct_translation = args.get('direct_translation', [])
            abstract_translation = args.get('abstract_translation', [])
            specific_names = args.get('specific_names', [])
            place_types = args.get('place_types', [])
            
            print(f"[DEBUG] direct_translation: {direct_translation}")
            print(f"[DEBUG] abstract_translation: {abstract_translation}")
            print(f"[DEBUG] specific_names: {specific_names}")
            print(f"[DEBUG] place_types: {place_types}")
            
            all_search_keywords = direct_translation + abstract_translation + specific_names
            
            if all_search_keywords:
                total_time = time.time() - start_time
                print(f"[TIMING] 전체 키워드 생성 완료: {total_time:.3f}초")
                
                return {
                    "has_location_intent": True,
                    "direct_translation": direct_translation,
                    "abstract_translation": abstract_translation,
                    "place_types": place_types,
                    "keywords": all_search_keywords,  # 기존 호환성
                    "original_korean": korean_text,  # 원본 한국어 텍스트 저장
                    "timing": {
                        "vertex_init_time": round(init_time, 3),
                        "llm_generation_time": round(llm_time, 3),
                        "total_time": round(total_time, 3)
                    }
                }
            else:
                total_time = time.time() - start_time
                return {
                    "has_location_intent": False, 
                    "direct_translation": [], 
                    "abstract_translation": [], 
                    "keywords": [],
                    "original_korean": korean_text,
                    "timing": {
                        "vertex_init_time": round(init_time, 3),
                        "llm_generation_time": round(llm_time, 3),
                        "total_time": round(total_time, 3)
                    }
                }
        else:
            total_time = time.time() - start_time
            return {
                "has_location_intent": False, 
                "direct_translation": [], 
                "abstract_translation": [], 
                "keywords": [],
                "original_korean": korean_text,
                "timing": {
                    "vertex_init_time": 0,
                    "llm_generation_time": 0,
                    "total_time": round(total_time, 3)
                }
            }
        
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
            else:
                print("❌ 장소 검색 의도가 감지되지 않았습니다.")
        except Exception as e:
            print(f"오류 발생: {e}")

if __name__ == "__main__":
    main()