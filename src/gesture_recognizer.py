"""
제스처 인식 모듈: 웹캠을 통해 손 제스처를 감지하고 관련 데이터를 추출합니다.
"""

import cv2
import mediapipe as mp
import numpy as np
import time
import platform
from typing import Dict, List, Tuple, Optional, Union
from src.config_loader import load_camera_settings


class GestureRecognizer:
    """
    MediaPipe를 활용하여 웹캠에서 손 제스처를 인식하는 클래스
    """
    
    def __init__(self, 
                 settings_path: Optional[str] = None,
                 webcam_id: Optional[int] = None,
                 width: Optional[int] = None,
                 height: Optional[int] = None,
                 flip_horizontal: Optional[bool] = None):
        """
        GestureRecognizer 초기화
        
        Args:
            settings_path: 카메라 설정 파일 경로 (기본값: config/camera_settings.json)
            webcam_id: 웹캠 장치 ID (설정 파일보다 우선)
            width: 웹캠 프레임 너비 (설정 파일보다 우선)
            height: 웹캠 프레임 높이 (설정 파일보다 우선)
            flip_horizontal: 좌우반전 여부 (설정 파일보다 우선)
        """
        # 설정 로드
        self.settings = load_camera_settings(settings_path)
        
        # 인자로 받은 값이 있으면 설정 덮어쓰기
        if webcam_id is not None:
            self.settings["camera_id"] = webcam_id
        if width is not None:
            self.settings["width"] = width
        if height is not None:
            self.settings["height"] = height
        if flip_horizontal is not None:
            self.settings["flip_horizontal"] = flip_horizontal
            
        # 설정 값 추출
        self.webcam_id = self.settings["camera_id"]
        self.width = self.settings["width"]
        self.height = self.settings["height"]
        self.flip_horizontal = self.settings["flip_horizontal"]
        
        # MediaPipe Hands 솔루션 초기화
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        # Hands 객체 초기화
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=self.settings["max_hands"],
            min_detection_confidence=self.settings["min_detection_confidence"],
            min_tracking_confidence=self.settings["min_tracking_confidence"],
            model_complexity=1
        )
        
        # 웹캠 설정
        self.cap = None
        
        # 제스처 데이터
        self.gesture_data = {
            'left_hand': {
                'landmarks': None,
                'thumb_index_distance': 0.0,
                'x_position': 0.0,
                'y_position': 0.0,
                'detected': False
            },
            'right_hand': {
                'landmarks': None,
                'thumb_index_distance': 0.0,
                'x_position': 0.0,
                'y_position': 0.0,
                'detected': False
            },
            'hands_distance': 0.0,
            'both_hands_detected': False
        }
        
        # 스무딩 관련 설정
        self.smooth_landmarks = self.settings["smooth_landmarks"]
        self.smooth_factor = 0.8  # 스무딩 강도 (0~1, 높을수록 부드러움)
        self.previous_values = {}
        
    def detect_available_cameras(self) -> List[int]:
        """
        사용 가능한 카메라 목록 감지
        
        Returns:
            감지된 카메라 ID 리스트
        """
        available_cameras = []
        # 최대 10개 카메라 포트 확인 (0~9)
        for i in range(10):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                available_cameras.append(i)
                cap.release()
        
        return available_cameras
    
    def find_built_in_camera(self) -> int:
        """
        내장 웹캠 ID 찾기 (macOS 환경 기준)
        
        Returns:
            내장 웹캠 ID 또는 -1 (찾지 못한 경우)
        """
        # macOS의 경우 특수 처리
        if platform.system() == 'Darwin':  # macOS
            # 사용 가능한 카메라 확인
            available_cameras = self.detect_available_cameras()
            
            if not available_cameras:
                return -1  # 사용 가능한 카메라 없음
            
            # macOS에서는 일반적으로 내장 카메라가 ID 0
            # 간혹 외부 카메라 연결 시 순서가 바뀔 수 있음
            for camera_id in available_cameras:
                # 각 카메라 테스트
                cap = cv2.VideoCapture(camera_id)
                if cap.isOpened():
                    # 카메라 이름 확인 (미지원 시 빈 문자열)
                    if platform.mac_ver()[0]:  # macOS 버전 확인
                        try:
                            # macOS에서 내장 카메라 확인 방법
                            # 참고: 일부 OpenCV 버전에서만 지원
                            camera_name = cap.getBackendName()
                            if "FaceTime" in camera_name or "Built-in" in camera_name:
                                cap.release()
                                return camera_id
                        except:
                            pass
                    cap.release()
            
            # 명확한 내장 카메라를 찾지 못했다면 첫 번째 사용 가능한 카메라 사용
            return available_cameras[0]
        
        # 다른 OS의 경우 기본값 0 반환
        return 0
        
    def start_webcam(self) -> bool:
        """
        웹캠 시작
        
        Returns:
            성공 여부 (True/False)
        """
        try:
            # 자동 감지 모드인 경우
            if self.webcam_id == -1:
                # 내장 웹캠 감지 시도
                camera_id = self.find_built_in_camera()
                if camera_id == -1:
                    print("사용 가능한 카메라를 찾을 수 없습니다.")
                    
                    # 사용 가능한 카메라가 없으면 기본 ID 시도
                    camera_id = 0
                    print(f"기본 카메라 ID {camera_id}로 시도합니다...")
                else:
                    print(f"카메라 ID {camera_id}를 사용합니다.")
                
                self.webcam_id = camera_id
            
            # 직접 지정한 카메라 ID 사용
            self.cap = cv2.VideoCapture(self.webcam_id)
            
            # 해상도 설정
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            
            # 성공적으로 열렸는지 확인
            if not self.cap.isOpened():
                print(f"카메라 ID {self.webcam_id}를 열 수 없습니다.")
                
                # 다른 카메라 자동 시도
                print("다른 카메라를 시도합니다...")
                available_cameras = self.detect_available_cameras()
                
                for cam_id in available_cameras:
                    if cam_id != self.webcam_id:
                        print(f"카메라 ID {cam_id} 시도 중...")
                        self.cap = cv2.VideoCapture(cam_id)
                        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
                        
                        if self.cap.isOpened():
                            print(f"카메라 ID {cam_id}를 사용합니다.")
                            self.webcam_id = cam_id
                            # 테스트 프레임 읽어보기
                            ret, _ = self.cap.read()
                            if ret:
                                return True
                
                print("사용 가능한 카메라를 찾을 수 없습니다.")
                return False
            
            # 테스트 프레임 읽어보기
            ret, _ = self.cap.read()
            if not ret:
                print(f"카메라 ID {self.webcam_id}에서 프레임을 읽을 수 없습니다.")
                return False
                
            return True
            
        except Exception as e:
            print(f"웹캠 시작 중 오류 발생: {e}")
            return False
    
    def release_webcam(self):
        """웹캠 리소스 해제"""
        if self.cap and self.cap.isOpened():
            self.cap.release()
        cv2.destroyAllWindows()
    
    def calculate_distance(self, p1: List[float], p2: List[float]) -> float:
        """
        두 점 사이의 유클리드 거리 계산
        
        Args:
            p1: 첫 번째 점 좌표 [x, y, z]
            p2: 두 번째 점 좌표 [x, y, z]
            
        Returns:
            두 점 사이의 거리
        """
        return np.linalg.norm(np.array(p1) - np.array(p2))
    
    def smooth_value(self, key: str, value: float) -> float:
        """
        값에 스무딩 적용
        
        Args:
            key: 값 식별자
            value: 현재 값
            
        Returns:
            스무딩 적용된 값
        """
        if not self.smooth_landmarks:
            return value
            
        if key not in self.previous_values:
            self.previous_values[key] = value
            return value
            
        # 이동 평균 적용
        smoothed = self.previous_values[key] * self.smooth_factor + \
                   value * (1 - self.smooth_factor)
        self.previous_values[key] = smoothed
        
        return smoothed
    
    def process_hand_landmarks(self, results) -> Dict:
        """
        MediaPipe 손 랜드마크 결과 처리
        
        Args:
            results: MediaPipe Hands 처리 결과
            
        Returns:
            처리된 제스처 데이터 딕셔너리
        """
        # 제스처 데이터 초기화
        self.gesture_data['left_hand']['detected'] = False
        self.gesture_data['right_hand']['detected'] = False
        self.gesture_data['both_hands_detected'] = False
        
        if not results.multi_hand_landmarks:
            return self.gesture_data
            
        # 감지된 각 손 처리
        for idx, (hand_landmarks, handedness) in enumerate(
            zip(results.multi_hand_landmarks, results.multi_handedness)
        ):
            # 손 유형 확인 (왼손/오른손)
            hand_label = handedness.classification[0].label  # 'Left' 또는 'Right'
            
            # 좌우반전 적용 여부 확인
            if self.flip_horizontal:
                # 좌우반전 상태에서는 MediaPipe가 좌우를 반대로 인식함
                # 'Left'로 감지된 손은 실제로는 오른손이고, 'Right'로 감지된 손은 실제로는 왼손
                hand_type = 'right_hand' if hand_label == 'Left' else 'left_hand'
            else:
                # 좌우반전이 없는 경우 정상적으로 인식
                hand_type = 'left_hand' if hand_label == 'Left' else 'right_hand'
                
            # 랜드마크 좌표 추출
            landmarks_list = []
            for landmark in hand_landmarks.landmark:
                landmarks_list.append([landmark.x, landmark.y, landmark.z])
            
            # 손 데이터 업데이트
            self.gesture_data[hand_type]['landmarks'] = landmarks_list
            self.gesture_data[hand_type]['detected'] = True
            
            # 엄지-검지 사이 거리 계산
            thumb_tip = landmarks_list[4]  # 엄지 끝
            index_tip = landmarks_list[8]  # 검지 끝
            thumb_index_dist = self.calculate_distance(thumb_tip, index_tip)
            
            # 손목 위치 (x, y 좌표)
            wrist = landmarks_list[0]
            
            # 손 데이터 업데이트 (스무딩 적용)
            self.gesture_data[hand_type]['thumb_index_distance'] = \
                self.smooth_value(f"{hand_type}_thumb_index", thumb_index_dist)
            self.gesture_data[hand_type]['x_position'] = \
                self.smooth_value(f"{hand_type}_x", wrist[0])
            self.gesture_data[hand_type]['y_position'] = \
                self.smooth_value(f"{hand_type}_y", wrist[1])
        
        # 양손 감지 여부 확인
        if self.gesture_data['left_hand']['detected'] and \
           self.gesture_data['right_hand']['detected']:
            # 양손 감지 시 양손 사이 거리 계산
            left_wrist = self.gesture_data['left_hand']['landmarks'][0]
            right_wrist = self.gesture_data['right_hand']['landmarks'][0]
            hands_dist = self.calculate_distance(left_wrist, right_wrist)
            
            self.gesture_data['hands_distance'] = \
                self.smooth_value("hands_distance", hands_dist)
            self.gesture_data['both_hands_detected'] = True
        
        return self.gesture_data
    
    def get_hand_landmarks(self) -> Dict:
        """
        현재 제스처 데이터 반환
        
        Returns:
            제스처 데이터 딕셔너리
        """
        return self.gesture_data
    
    def draw_landmarks(self, image, results):
        """
        손 랜드마크 시각화
        
        Args:
            image: 원본 영상
            results: MediaPipe 처리 결과
        """
        if results.multi_hand_landmarks:
            for idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
                # 랜드마크 그리기
                self.mp_drawing.draw_landmarks(
                    image,
                    hand_landmarks,
                    self.mp_hands.HAND_CONNECTIONS,
                    self.mp_drawing_styles.get_default_hand_landmarks_style(),
                    self.mp_drawing_styles.get_default_hand_connections_style()
                )
                
    def draw_gesture_data(self, image):
        """
        제스처 데이터 텍스트 시각화
        
        Args:
            image: 원본 영상
        """
        # 왼손 정보
        if self.gesture_data['left_hand']['detected']:
            left_dist = self.gesture_data['left_hand']['thumb_index_distance']
            left_y = self.gesture_data['left_hand']['y_position']
            left_x = self.gesture_data['left_hand']['x_position']
            
            cv2.putText(image, f"Left Hand:", (10, 20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            cv2.putText(image, f"Thumb-Index: {left_dist:.2f}", (10, 40), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            cv2.putText(image, f"Y-pos: {left_y:.2f}", (10, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            cv2.putText(image, f"X-pos: {left_x:.2f}", (10, 80), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        # 오른손 정보
        if self.gesture_data['right_hand']['detected']:
            right_dist = self.gesture_data['right_hand']['thumb_index_distance']
            right_y = self.gesture_data['right_hand']['y_position']
            right_x = self.gesture_data['right_hand']['x_position']
            
            cv2.putText(image, f"Right Hand:", (image.shape[1] - 170, 20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
            cv2.putText(image, f"Thumb-Index: {right_dist:.2f}", (image.shape[1] - 170, 40), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
            cv2.putText(image, f"Y-pos: {right_y:.2f}", (image.shape[1] - 170, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
            cv2.putText(image, f"X-pos: {right_x:.2f}", (image.shape[1] - 170, 80), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        
        # 양손 정보
        if self.gesture_data['both_hands_detected']:
            hands_dist = self.gesture_data['hands_distance']
            
            cv2.putText(image, f"Hands Distance: {hands_dist:.2f}", 
                       (image.shape[1]//2 - 80, 20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
        
        # 카메라 ID 및 좌우반전 상태 표시
        flip_status = "On" if self.flip_horizontal else "Off"
        cv2.putText(image, f"Camera ID: {self.webcam_id} | Flip: {flip_status}", 
                   (10, image.shape[0] - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    def process_frame(self, frame) -> Tuple[Dict, np.ndarray]:
        """
        단일 프레임 처리
        
        Args:
            frame: 처리할 비디오 프레임
            
        Returns:
            (제스처 데이터, 시각화된 프레임)
        """
        # 좌우반전 적용 (설정된 경우)
        if self.flip_horizontal:
            frame = cv2.flip(frame, 1)  # 1: 수평 방향 뒤집기
        
        # 이미지 색상 변환 (BGR -> RGB)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # 이미지 처리
        results = self.hands.process(rgb_frame)
        
        # 손 랜드마크 처리
        self.process_hand_landmarks(results)
        
        # 랜드마크 시각화
        annotated_frame = frame.copy()
        self.draw_landmarks(annotated_frame, results)
        self.draw_gesture_data(annotated_frame)
        
        return self.gesture_data, annotated_frame
    
    def run(self, show_window: bool = True, callback = None):
        """
        실시간 웹캠 처리 루프
        
        Args:
            show_window: 화면에 결과 창 표시 여부
            callback: 제스처 데이터 처리 콜백 함수 (선택)
                      callback(gesture_data) 형태로 호출됨
        """
        if not self.start_webcam():
            print("웹캠을 시작할 수 없습니다. 다른 카메라 ID를 시도해보세요.")
            print("사용 가능한 카메라 확인:", self.detect_available_cameras())
            return
        
        try:
            while self.cap.isOpened():
                # 프레임 읽기
                ret, frame = self.cap.read()
                if not ret:
                    print("프레임 읽기 실패")
                    
                    # 연결 복구 시도
                    print("카메라 연결 복구 시도...")
                    self.cap.release()
                    self.cap = cv2.VideoCapture(self.webcam_id)
                    if not self.cap.isOpened():
                        print("카메라 복구 실패. 종료합니다.")
                        break
                    continue
                
                # 프레임 처리
                gesture_data, annotated_frame = self.process_frame(frame)
                
                # 콜백 함수 호출 (제공된 경우)
                if callback:
                    callback(gesture_data)
                
                # 결과 표시
                if show_window:
                    cv2.imshow('Hand Gesture Recognition', annotated_frame)
                
                # 종료 조건 ('q' 키 누름)
                if cv2.waitKey(5) & 0xFF == ord('q'):
                    break
                    
        finally:
            # 리소스 해제
            self.release_webcam()
    
# 테스트 코드
if __name__ == "__main__":
    # 사용 가능한 카메라 확인
    recognizer = GestureRecognizer()
    available_cameras = recognizer.detect_available_cameras()
    print(f"사용 가능한 카메라 ID: {available_cameras}")
    print(f"현재 설정: {recognizer.settings}")
    
    # 모듈 테스트를 위한 콜백 함수
    def print_gesture_values(gesture_data):
        if gesture_data['left_hand']['detected']:
            print(f"왼손 엄지-검지 거리: {gesture_data['left_hand']['thumb_index_distance']:.2f}")
        if gesture_data['right_hand']['detected']:
            print(f"오른손 엄지-검지 거리: {gesture_data['right_hand']['thumb_index_distance']:.2f}")
        if gesture_data['both_hands_detected']:
            print(f"양손 간 거리: {gesture_data['hands_distance']:.2f}")
        print("---")
    
    # 제스처 인식 시작
    print("제스처 인식을 시작합니다... (종료하려면 'q' 키를 누르세요)")
    recognizer.run(show_window=True, callback=print_gesture_values) 