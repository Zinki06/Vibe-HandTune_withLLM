"""
감정 분석 및 프리셋 선택 통합 테스트 스크립트입니다.
STT 결과 텍스트를 입력받아 감정 분석 후 해당 프리셋을 가져오는 과정을 테스트합니다.
"""

import os
import sys
import time

# 현재 디렉토리 경로가 src인 경우, 부모 디렉토리를 sys.path에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from src.emotion_analyzer import EmotionAnalyzer
from src.preset_loader import PresetLoader

def test_text_to_preset(text):
    """
    텍스트를 입력받아 감정 분석 후 해당 프리셋을 반환하는 통합 테스트 함수
    
    Parameters:
    -----------
    text : str
        분석할 텍스트
        
    Returns:
    --------
    dict
        선택된 프리셋 정보
    """
    # 모듈 초기화
    emotion_analyzer = EmotionAnalyzer()
    preset_loader = PresetLoader()
    
    # 단계 1: 감정 분석
    print(f"입력 텍스트: \"{text}\"")
    print("감정 분석 중...")
    start_time = time.time()
    emotion_number = emotion_analyzer.analyze_emotion(text)
    emotion_name = emotion_analyzer.get_emotion_name(emotion_number)
    analysis_time = time.time() - start_time
    
    print(f"감정 분석 결과: {emotion_number} ({emotion_name})")
    print(f"분석 소요 시간: {analysis_time:.2f}초")
    
    # 단계 2: 프리셋 로드
    print("\n프리셋 로드 중...")
    start_time = time.time()
    preset_info = preset_loader.get_preset_by_emotion(emotion_number)
    preset_load_time = time.time() - start_time
    
    print(f"프리셋 로드 소요 시간: {preset_load_time:.2f}초")
    
    # 결과 출력
    if preset_info:
        print("\n선택된 프리셋 정보:")
        print(f"감정: {preset_info['name']}")
        print("프리셋 속성:")
        for key, value in preset_info["preset"].items():
            print(f"  - {key}: {value}")
    
    return preset_info

def main():
    """
    메인 실행 함수
    """
    print("=== 감정 분석 및 프리셋 선택 테스트 ===\n")
    
    # 사용자 입력 없이 테스트 데이터 사용
    use_test_data = True
    print("테스트 데이터를 사용합니다.")
    
    if use_test_data:
        # 테스트 문장 목록
        test_texts = [
            "오늘은 정말 슬프고 우울한 하루였어...",
            "평화롭고 고요한 밤이야.",
            "그냥 보통 하루였어. 특별한 일은 없었어.",
            "와! 정말 즐겁고 신나는 여행이었어!",
            "너무 흥분되고 열정적인 공연이었다!"
        ]
        
        # 각 테스트 문장에 대해 처리
        for i, text in enumerate(test_texts, 1):
            print(f"\n테스트 케이스 {i}/{len(test_texts)}")
            print("-" * 50)
            preset_info = test_text_to_preset(text)
            print("-" * 50)
    else:
        # 사용자 직접 입력
        while True:
            text = input("\n분석할 텍스트를 입력하세요 (종료: 빈 입력): ")
            if not text.strip():
                break
                
            print("-" * 50)
            preset_info = test_text_to_preset(text)
            print("-" * 50)
    
    print("\n테스트 완료")

if __name__ == "__main__":
    main() 