"""
설정 로드 유틸리티 모듈
환경 변수 및 설정 파일을 로드하는 함수들을 제공합니다.
"""

import os
import json
import dotenv
from typing import Dict, Any, Optional

def load_api_key() -> str:
    """
    .env 파일에서 OpenAI API 키를 로드합니다.
    
    Returns:
        API 키 문자열
    """
    # .env 파일 로드
    dotenv.load_dotenv()
    
    # 환경 변수에서 API 키 가져오기
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        raise ValueError("OPENAI_API_KEY가 .env 파일에 설정되어 있지 않습니다.")
    
    return api_key

def load_camera_settings(custom_path: Optional[str] = None) -> Dict[str, Any]:
    """
    카메라 설정 파일을 로드합니다.
    
    Args:
        custom_path: 사용자 지정 설정 파일 경로 (선택 사항)
        
    Returns:
        카메라 설정 딕셔너리
    """
    # 기본 설정 값 정의
    default_settings = {
        "camera_id": -1,  # 자동 감지
        "width": 640,
        "height": 480,
        "flip_horizontal": True,
        "min_detection_confidence": 0.7,
        "min_tracking_confidence": 0.5,
        "max_hands": 2,
        "smooth_landmarks": True
    }
    
    # 설정 파일 경로 결정
    if custom_path:
        settings_path = custom_path
    else:
        # 현재 모듈 경로 기준으로 config/camera_settings.json 경로 설정
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        settings_path = os.path.join(project_root, "config", "camera_settings.json")
    
    # 파일 존재 여부 확인
    if not os.path.exists(settings_path):
        print(f"카메라 설정 파일을 찾을 수 없습니다: {settings_path}")
        print("기본 설정을 사용합니다.")
        return default_settings
    
    try:
        # 설정 파일 로드
        with open(settings_path, 'r', encoding='utf-8') as f:
            settings = json.load(f)
        
        # comments 필드 제거 (사용하지 않음)
        if 'comments' in settings:
            del settings['comments']
            
        # 기본 설정과 병합 (누락된 설정은 기본값 사용)
        for key, value in default_settings.items():
            if key not in settings:
                settings[key] = value
        
        return settings
        
    except Exception as e:
        print(f"카메라 설정 파일 로드 중 오류 발생: {e}")
        print("기본 설정을 사용합니다.")
        return default_settings

# 간단한 테스트 코드 (main 블록 내)
if __name__ == '__main__':
    try:
        key = load_api_key()
        print("API Key loaded successfully.")
    except ValueError as e:
        print(e) 