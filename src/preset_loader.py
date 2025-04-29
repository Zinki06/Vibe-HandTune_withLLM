"""
베이스 멜로디 프리셋 로더 모듈입니다.
config/bass_presets.json 파일에서 감정별 베이스 멜로디 프리셋을 로드하고 관리합니다.
"""

import os
import json

class PresetLoader:
    """
    베이스 멜로디 프리셋 로더 클래스입니다.
    """
    
    def __init__(self, preset_file_path=None):
        """
        PresetLoader 클래스 초기화
        
        Parameters:
        -----------
        preset_file_path : str or None
            프리셋 JSON 파일 경로. None이면 기본 경로 사용
        """
        if preset_file_path is None:
            # 현재 모듈 경로 기준으로 config/bass_presets.json 경로 설정
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            self.preset_file_path = os.path.join(project_root, "config", "bass_presets.json")
        else:
            self.preset_file_path = preset_file_path
        
        # 프리셋 데이터 저장 변수
        self.presets = None
        
        # 파일 로드
        self.load_presets()
    
    def load_presets(self):
        """
        프리셋 JSON 파일을 로드합니다.
        
        Returns:
        --------
        bool
            로드 성공 여부
        """
        try:
            if not os.path.exists(self.preset_file_path):
                print(f"프리셋 파일이 존재하지 않습니다: {self.preset_file_path}")
                return False
            
            with open(self.preset_file_path, 'r', encoding='utf-8') as f:
                self.presets = json.load(f)
            
            # 기본 구조 확인
            if not isinstance(self.presets, dict) or "emotions" not in self.presets:
                print("프리셋 파일 구조가 유효하지 않습니다.")
                return False
            
            print(f"프리셋을 성공적으로 로드했습니다: {len(self.presets['emotions'])} 감정")
            return True
            
        except json.JSONDecodeError as e:
            print(f"JSON 파싱 오류: {str(e)}")
            return False
        except Exception as e:
            print(f"프리셋 로드 중 오류 발생: {str(e)}")
            return False
    
    def get_preset_by_emotion(self, emotion_number):
        """
        감정 번호에 해당하는 프리셋을 반환합니다.
        
        Parameters:
        -----------
        emotion_number : int or str
            감정 번호 (1-5)
            
        Returns:
        --------
        dict or None
            프리셋 정보 딕셔너리 또는 None(감정 번호가 유효하지 않을 경우)
        """
        if self.presets is None:
            print("프리셋이 로드되지 않았습니다.")
            return None
        
        # 문자열로 변환 (숫자 입력도 처리하기 위함)
        emotion_key = str(emotion_number)
        
        # 감정 번호 유효성 검사
        if emotion_key not in self.presets["emotions"]:
            print(f"유효하지 않은 감정 번호입니다: {emotion_number}")
            # 기본값으로 중립(3) 반환
            emotion_key = "3"
            print(f"기본 감정(중립) 프리셋을 사용합니다.")
        
        return self.presets["emotions"][emotion_key]
    
    def get_emotion_names(self):
        """
        모든 감정 이름 목록을 반환합니다.
        
        Returns:
        --------
        dict or None
            감정 번호를 키로, 이름을 값으로 하는 딕셔너리
        """
        if self.presets is None:
            print("프리셋이 로드되지 않았습니다.")
            return None
        
        return {k: v["name"] for k, v in self.presets["emotions"].items()}
    
    def get_all_emotions(self):
        """
        모든 감정 정보를 반환합니다.
        
        Returns:
        --------
        dict or None
            감정 정보 딕셔너리
        """
        if self.presets is None:
            print("프리셋이 로드되지 않았습니다.")
            return None
        
        return self.presets["emotions"]

# 간단한 테스트 코드
if __name__ == "__main__":
    # 프리셋 로더 생성
    preset_loader = PresetLoader()
    
    # 모든 감정 출력
    emotion_names = preset_loader.get_emotion_names()
    if emotion_names:
        print("\n감정 목록:")
        for num, name in emotion_names.items():
            print(f"{num}: {name}")
    
    # 테스트: 각 감정별 프리셋 정보 가져오기
    for emotion_num in range(1, 6):
        preset_info = preset_loader.get_preset_by_emotion(emotion_num)
        if preset_info:
            print(f"\n감정 {emotion_num} ({preset_info['name']}) 프리셋:")
            for key, value in preset_info["preset"].items():
                print(f"  - {key}: {value}")
    
    # 테스트: 잘못된 감정 번호
    preset_info = preset_loader.get_preset_by_emotion(10)
    if preset_info:
        print(f"\n잘못된 감정 번호 테스트 결과: {preset_info['name']}") 