"""
제스처 인식 모듈 테스트 스크립트
웹캠을 통한 손 제스처 인식 및 시각화 테스트
"""

import os
import sys
import time
import numpy as np
import argparse

# 프로젝트 루트 경로를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.gesture_recognizer import GestureRecognizer

def test_gesture_recognition(webcam_id=-1):
    """
    GestureRecognizer 모듈 테스트 및 데모
    
    Args:
        webcam_id: 사용할 웹캠 ID (-1: 자동 감지)
    """
    print("===== 제스처 인식 모듈 테스트 =====")
    print("웹캠을 통해 손 제스처를 인식하고 관련 데이터를 추출합니다.")
    print("- 웹캠 화면에 손 랜드마크와 제스처 데이터가 표시됩니다.")
    print("- 콘솔에는 주요 제스처 값이 실시간으로 출력됩니다.")
    print("- 종료하려면 'q' 키를 누르세요.")
    print("=" * 35)
    
    # 사용 가능한 카메라 확인
    temp_recognizer = GestureRecognizer()
    available_cameras = temp_recognizer.detect_available_cameras()
    print(f"사용 가능한 카메라 ID: {available_cameras}")
    del temp_recognizer
    
    # 최근 값 추적용 변수
    recent_values = {
        'left_thumb_index': [],
        'right_thumb_index': [],
        'hands_distance': []
    }
    max_recent = 10  # 최근 10개 값 저장
    
    # 콜백 함수 - 제스처 데이터 출력 및 통계 수집
    def process_gesture_data(gesture_data):
        # 왼손 정보
        if gesture_data['left_hand']['detected']:
            left_dist = gesture_data['left_hand']['thumb_index_distance']
            left_y = gesture_data['left_hand']['y_position']
            print(f"왼손 - 엄지-검지: {left_dist:.2f}, Y위치: {left_y:.2f}")
            
            # 최근 값 추적
            recent_values['left_thumb_index'].append(left_dist)
            if len(recent_values['left_thumb_index']) > max_recent:
                recent_values['left_thumb_index'].pop(0)
                
        # 오른손 정보
        if gesture_data['right_hand']['detected']:
            right_dist = gesture_data['right_hand']['thumb_index_distance']
            right_y = gesture_data['right_hand']['y_position']
            print(f"오른손 - 엄지-검지: {right_dist:.2f}, Y위치: {right_y:.2f}")
            
            # 최근 값 추적
            recent_values['right_thumb_index'].append(right_dist)
            if len(recent_values['right_thumb_index']) > max_recent:
                recent_values['right_thumb_index'].pop(0)
        
        # 양손 정보
        if gesture_data['both_hands_detected']:
            hands_dist = gesture_data['hands_distance']
            print(f"양손 거리: {hands_dist:.2f}")
            
            # 최근 값 추적
            recent_values['hands_distance'].append(hands_dist)
            if len(recent_values['hands_distance']) > max_recent:
                recent_values['hands_distance'].pop(0)
                
        # 빈 줄로 출력 구분
        print()
    
    # 제스처 인식기 초기화 및 실행
    recognizer = GestureRecognizer(
        max_hands=2,                   # 최대 2개 손 감지
        min_detection_confidence=0.7,  # 감지 신뢰도 임계값
        min_tracking_confidence=0.5,   # 추적 신뢰도 임계값
        smooth_landmarks=True,         # 스무딩 적용
        webcam_id=webcam_id,           # 지정된 웹캠 ID 또는 자동 감지(-1)
        width=640,                     # 프레임 너비
        height=480                     # 프레임 높이
    )
    
    # 제스처 인식 실행
    recognizer.run(show_window=True, callback=process_gesture_data)
    
    # 통계 출력
    print("\n===== 제스처 인식 통계 =====")
    if recent_values['left_thumb_index']:
        avg_left = np.mean(recent_values['left_thumb_index'])
        print(f"왼손 엄지-검지 평균 거리: {avg_left:.4f}")
    
    if recent_values['right_thumb_index']:
        avg_right = np.mean(recent_values['right_thumb_index'])
        print(f"오른손 엄지-검지 평균 거리: {avg_right:.4f}")
    
    if recent_values['hands_distance']:
        avg_dist = np.mean(recent_values['hands_distance'])
        print(f"양손 평균 거리: {avg_dist:.4f}")

def main():
    """
    메인 함수
    """
    # 명령행 인자 처리
    parser = argparse.ArgumentParser(description='제스처 인식 테스트')
    parser.add_argument('--camera', type=int, default=-1, 
                       help='사용할 카메라 ID (기본값: -1 자동 감지)')
    args = parser.parse_args()
    
    try:
        # 테스트 실행
        test_gesture_recognition(webcam_id=args.camera)
    except KeyboardInterrupt:
        print("\n사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n오류 발생: {e}")
        
        # 오류 발생 시 카메라 ID 정보 출력
        try:
            temp_recognizer = GestureRecognizer()
            available_cameras = temp_recognizer.detect_available_cameras()
            print(f"\n사용 가능한 카메라 ID: {available_cameras}")
            print("\n다른 카메라 ID로 시도해보세요:")
            print(f"python src/gesture_test.py --camera <ID>")
            del temp_recognizer
        except:
            pass

if __name__ == "__main__":
    main() 