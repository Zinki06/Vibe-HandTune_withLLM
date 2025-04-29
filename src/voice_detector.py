"""
음성 활성화 감지(Voice Activity Detection) 모듈입니다.
오디오 스트림에서 음성이 있는지 감지하고 자동으로 녹음을 시작/중지합니다.
"""

import numpy as np
import time
import threading
from src.audio_input import AudioInput

class VoiceDetector:
    """
    실시간 음성 활성화 감지를 처리하는 클래스입니다.
    """
    def __init__(self, 
                 audio_input=None,
                 energy_threshold=0.05,  # 에너지 임계값 (0~1)
                 pause_threshold=1.0,    # 음성 사이 허용 묵음 시간 (초)
                 phrase_threshold=0.3,   # 음성 시작 인식 시간 (초)
                 max_phrase_time=10.0):  # 최대 음성 녹음 시간 (초)
        """
        VoiceDetector 클래스 초기화

        Parameters:
        -----------
        audio_input : AudioInput or None
            사용할 AudioInput 인스턴스, None이면 자동 생성
        energy_threshold : float
            음성 감지 에너지 임계값 (0~1)
        pause_threshold : float
            음성 사이 허용되는 묵음 시간 (초)
        phrase_threshold : float
            음성 시작 인식에 필요한 최소 시간 (초)
        max_phrase_time : float
            한 문장 최대 녹음 시간 (초)
        """
        # AudioInput 인스턴스 생성 또는 사용
        self.audio_input = audio_input or AudioInput(chunk_duration=0.1)
        
        # 음성 감지 매개변수
        self.energy_threshold = energy_threshold
        self.pause_threshold = pause_threshold
        self.phrase_threshold = phrase_threshold
        self.max_phrase_time = max_phrase_time
        
        # 상태 변수
        self.is_listening = False
        self.listen_thread = None
    
    def _calculate_energy(self, audio_chunk):
        """
        오디오 청크의 에너지 레벨을 계산합니다.
        
        Parameters:
        -----------
        audio_chunk : numpy.ndarray
            오디오 데이터 청크
            
        Returns:
        --------
        float
            정규화된 에너지 레벨 (0~1)
        """
        if audio_chunk is None or audio_chunk.size == 0:
            return 0.0
        
        # 진폭 값을 제곱하여 에너지 계산
        if audio_chunk.dtype.kind == 'i':  # int16 등의 정수형
            # 정수형 데이터는 최대값으로 나누어 정규화
            max_value = np.iinfo(audio_chunk.dtype).max
            energy = np.mean(np.abs(audio_chunk / max_value))
        else:  # float32 등의 부동소수점형
            # 이미 -1~1 범위의 부동소수점은 바로 계산
            energy = np.mean(np.abs(audio_chunk))
        
        return energy
    
    def _listen_for_phrase(self, callback=None):
        """
        백그라운드 스레드에서 실행되는 음성 감지 및 녹음 함수
        
        Parameters:
        -----------
        callback : function or None
            음성이 감지되고 녹음이 완료되었을 때 호출할 콜백 함수
            콜백은 매개변수로 녹음된 오디오 데이터(numpy.ndarray)를 받음
        """
        # 오디오 입력 시작
        self.audio_input.start_recording()
        
        # 상태 변수
        is_speaking = False
        speech_start_time = None
        last_speech_time = None
        collected_chunks = []
        
        print("음성 감지 대기 중...")
        
        try:
            while self.is_listening:
                # 오디오 청크 가져오기
                chunk = self.audio_input.get_audio_chunk(timeout=0.2)
                if chunk is None:
                    continue
                
                # 에너지 레벨 계산
                energy = self._calculate_energy(chunk)
                
                current_time = time.time()
                
                # 음성 감지 로직
                if energy > self.energy_threshold:
                    # 에너지가 임계값보다 높으면 음성으로 간주
                    if not is_speaking:
                        # 음성 시작 감지
                        is_speaking = True
                        speech_start_time = current_time
                        print("음성 감지됨 - 녹음 시작")
                    
                    # 마지막 음성 시간 업데이트
                    last_speech_time = current_time
                    
                    # 청크 저장
                    collected_chunks.append(chunk)
                    
                elif is_speaking:
                    # 음성 중 묵음 상태
                    collected_chunks.append(chunk)  # 묵음도 녹음에 포함
                    
                    # 일정 시간 이상 묵음이 지속되면 음성이 끝난 것으로 간주
                    if (current_time - last_speech_time) > self.pause_threshold:
                        # 음성 종료 감지
                        is_speaking = False
                        
                        # 최소 인식 시간 확인
                        if (last_speech_time - speech_start_time) >= self.phrase_threshold:
                            # 유효한 음성이 감지됨
                            print("음성 녹음 완료")
                            
                            # 녹음된 청크를 하나의 배열로 결합
                            if collected_chunks:
                                audio_data = np.vstack(collected_chunks)
                                
                                # 콜백 호출
                                if callback:
                                    callback(audio_data)
                            
                        else:
                            print("음성이 너무 짧아서 무시됩니다.")
                        
                        # 청크 초기화
                        collected_chunks = []
                        speech_start_time = None
                        last_speech_time = None
                
                # 최대 녹음 시간 확인
                if is_speaking and speech_start_time and (current_time - speech_start_time) > self.max_phrase_time:
                    print(f"최대 녹음 시간({self.max_phrase_time}초)에 도달했습니다.")
                    is_speaking = False
                    
                    # 녹음된 청크를 하나의 배열로 결합
                    if collected_chunks:
                        audio_data = np.vstack(collected_chunks)
                        
                        # 콜백 호출
                        if callback:
                            callback(audio_data)
                    
                    # 청크 초기화
                    collected_chunks = []
                    speech_start_time = None
                    last_speech_time = None
            
        finally:
            # 스레드 종료 시 오디오 스트림 중지
            self.audio_input.stop_recording()
    
    def start_detection(self, callback=None):
        """
        음성 감지를 시작합니다.
        
        Parameters:
        -----------
        callback : function or None
            음성이 감지되었을 때 호출할 콜백 함수
        """
        if self.is_listening:
            print("이미 음성 감지 중입니다.")
            return
        
        self.is_listening = True
        self.listen_thread = threading.Thread(
            target=self._listen_for_phrase,
            args=(callback,),
            daemon=True
        )
        self.listen_thread.start()
    
    def stop_detection(self):
        """
        음성 감지를 중지합니다.
        """
        if not self.is_listening:
            print("음성 감지 중이 아닙니다.")
            return
        
        self.is_listening = False
        if self.listen_thread:
            self.listen_thread.join(timeout=2.0)
        print("음성 감지가 중지되었습니다.")
    
    def adjust_for_ambient_noise(self, duration=1.0):
        """
        주변 환경 소음에 맞춰 에너지 임계값을 조정합니다.
        
        Parameters:
        -----------
        duration : float
            샘플링할 시간 (초)
        """
        print(f"{duration}초 동안 주변 소음을 측정합니다...")
        
        # 임시 녹음
        self.audio_input.start_recording()
        chunks = []
        
        end_time = time.time() + duration
        while time.time() < end_time:
            chunk = self.audio_input.get_audio_chunk(timeout=0.1)
            if chunk is not None:
                chunks.append(self._calculate_energy(chunk))
        
        self.audio_input.stop_recording()
        
        if chunks:
            # 평균 에너지의 1.1배를 새 임계값으로 설정
            avg_energy = np.mean(chunks)
            self.energy_threshold = min(0.2, avg_energy * 1.1)
            print(f"에너지 임계값이 {self.energy_threshold:.4f}로 조정되었습니다.")
        else:
            print("소음 측정에 실패했습니다.")

# 테스트 코드
if __name__ == "__main__":
    from src.audio_input import AudioInput
    
    # 처리된 오디오 데이터를 출력하는 콜백 함수
    def print_audio_info(audio_data):
        print(f"감지된 오디오 데이터 - 모양: {audio_data.shape}, 길이: {audio_data.shape[0]/16000:.2f}초")
    
    # 오디오 입력 및 음성 감지기 설정
    audio_input = AudioInput(sample_rate=16000, channels=1, chunk_duration=0.1)
    voice_detector = VoiceDetector(
        audio_input=audio_input,
        energy_threshold=0.05,
        pause_threshold=1.0
    )
    
    # 주변 소음에 맞춰 임계값 조정
    voice_detector.adjust_for_ambient_noise(duration=2.0)
    
    # 음성 감지 시작
    print("음성 감지를 시작합니다. 말씀해 주세요. (종료하려면 Ctrl+C)")
    voice_detector.start_detection(callback=print_audio_info)
    
    try:
        # 메인 스레드는 사용자 중단을 기다림
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n사용자에 의해 중단되었습니다.")
    finally:
        # 정리
        voice_detector.stop_detection() 