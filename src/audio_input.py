"""
오디오 입력 처리 모듈입니다.
sounddevice 라이브러리를 사용하여 실시간 오디오 스트림을 캡처하고 처리합니다.
"""

import numpy as np
import sounddevice as sd
import queue
import threading
import time
import os
import wave
import datetime

class AudioInput:
    """
    마이크로부터 오디오 입력을 캡처하고 처리하는 클래스입니다.
    """
    def __init__(self, 
                 sample_rate=16000, 
                 channels=1, 
                 chunk_duration=1.0,
                 dtype='int16'):
        """
        AudioInput 클래스 초기화

        Parameters:
        -----------
        sample_rate : int
            오디오 샘플링 레이트 (Hz)
        channels : int
            오디오 채널 수 (1: 모노, 2: 스테레오)
        chunk_duration : float
            각 오디오 청크의 길이 (초)
        dtype : str
            오디오 데이터 타입 ('int16', 'float32' 등)
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_duration = chunk_duration
        self.dtype = dtype
        self.chunk_size = int(self.sample_rate * self.chunk_duration)
        
        # 오디오 데이터를 저장할 큐
        self.audio_queue = queue.Queue()
        
        # 스트림 상태 변수
        self.is_recording = False
        self.stream = None
        self.stream_thread = None
    
    def _audio_callback(self, indata, frames, time, status):
        """
        오디오 스트림 콜백 함수
        
        sounddevice 라이브러리에서 호출되는 콜백으로, 
        입력 오디오 데이터를 큐에 추가합니다.
        """
        if status:
            print(f"상태: {status}")
        
        # 입력 데이터를 큐에 넣기
        self.audio_queue.put(indata.copy())
    
    def start_recording(self):
        """
        오디오 녹음을 시작합니다.
        """
        if self.is_recording:
            print("이미 녹음 중입니다.")
            return
        
        # 큐 초기화
        while not self.audio_queue.empty():
            self.audio_queue.get()
        
        # 오디오 스트림 설정 및 시작
        self.stream = sd.InputStream(
            callback=self._audio_callback,
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype=self.dtype,
            blocksize=self.chunk_size
        )
        
        self.is_recording = True
        self.stream.start()
        print("녹음을 시작합니다.")
    
    def stop_recording(self):
        """
        오디오 녹음을 중지합니다.
        """
        if not self.is_recording:
            print("녹음 중이 아닙니다.")
            return
        
        self.is_recording = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        print("녹음을 중지했습니다.")
    
    def get_audio_chunk(self, timeout=None):
        """
        오디오 큐에서 청크를 가져옵니다.
        
        Parameters:
        -----------
        timeout : float or None
            큐에서 데이터를 기다리는 시간 (초). None이면 무한정 대기.
            
        Returns:
        --------
        numpy.ndarray or None
            오디오 데이터 청크, 타임아웃이면 None 반환
        """
        try:
            return self.audio_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def record_for_duration(self, duration):
        """
        지정된 시간(초) 동안 오디오를 녹음하고 전체 데이터를 반환합니다.
        
        Parameters:
        -----------
        duration : float
            녹음할 시간 (초)
            
        Returns:
        --------
        numpy.ndarray
            녹음된 전체 오디오 데이터
        """
        # 녹음 시작
        self.start_recording()
        
        # 청크 수 계산
        num_chunks = int(duration / self.chunk_duration) + 1
        chunks = []
        
        # 지정된 시간 동안 오디오 청크 수집
        for _ in range(num_chunks):
            chunk = self.get_audio_chunk(timeout=self.chunk_duration * 1.5)
            if chunk is not None:
                chunks.append(chunk)
            else:
                break
        
        # 녹음 중지
        self.stop_recording()
        
        # 청크들을 하나의 배열로 결합
        if chunks:
            return np.vstack(chunks)
        else:
            return np.array([])
    
    def get_wav_bytes(self, audio_data):
        """
        NumPy 배열을 WAV 형식의 바이트로 변환합니다.
        
        Parameters:
        -----------
        audio_data : numpy.ndarray
            변환할 오디오 데이터
            
        Returns:
        --------
        bytes
            WAV 형식의 바이트 데이터
        """
        import io
        import wave
        
        # 데이터가 비어있으면 빈 바이트 반환
        if audio_data.size == 0:
            return b''
        
        # WAV 파일 형식으로 변환
        byte_io = io.BytesIO()
        with wave.open(byte_io, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)  # int16은 2바이트
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio_data.tobytes())
        
        # 바이트 데이터 반환
        byte_io.seek(0)
        return byte_io.read()

    def save_to_wav_file(self, audio_data, file_path=None):
        """
        오디오 데이터를 WAV 파일로 저장합니다.
        
        Parameters:
        -----------
        audio_data : numpy.ndarray
            저장할 오디오 데이터
        file_path : str or None
            저장할 파일 경로. None이면 자동 생성됨
            
        Returns:
        --------
        str
            저장된 파일의 경로
        """
        # 데이터가 비어있으면 빈 문자열 반환
        if audio_data.size == 0:
            print("오디오 데이터가 없습니다.")
            return ""
        
        # 파일 경로 생성
        if file_path is None:
            # 오디오 녹음 저장 디렉토리 확인 및 생성
            recordings_dir = "audio_recordings"
            os.makedirs(recordings_dir, exist_ok=True)
            
            # 타임스탬프로 파일 이름 생성
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = os.path.join(recordings_dir, f"recording_{timestamp}.wav")
        
        # WAV 파일로 저장
        with wave.open(file_path, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)  # int16은 2바이트
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio_data.tobytes())
        
        print(f"오디오 파일이 저장되었습니다: {file_path}")
        return file_path
    
    def load_from_wav_file(self, file_path):
        """
        WAV 파일에서 오디오 데이터를 로드합니다.
        
        Parameters:
        -----------
        file_path : str
            로드할 WAV 파일 경로
            
        Returns:
        --------
        numpy.ndarray
            로드된 오디오 데이터
        """
        if not os.path.exists(file_path):
            print(f"파일이 존재하지 않습니다: {file_path}")
            return np.array([])
        
        with wave.open(file_path, 'rb') as wf:
            # WAV 헤더 정보 읽기
            channels = wf.getnchannels()
            sample_width = wf.getsampwidth()
            sample_rate = wf.getframerate()
            n_frames = wf.getnframes()
            
            # 오디오 데이터 읽기
            raw_data = wf.readframes(n_frames)
            
            # NumPy 배열로 변환
            if sample_width == 2:  # 16-bit
                dtype = np.int16
            elif sample_width == 4:  # 32-bit
                dtype = np.int32
            else:
                dtype = np.uint8
            
            audio_data = np.frombuffer(raw_data, dtype=dtype)
            
            # 채널이 2개(스테레오)면 모양 조정
            if channels == 2:
                audio_data = audio_data.reshape(-1, 2)
        
        return audio_data

# 간단한 테스트 코드
if __name__ == "__main__":
    audio_input = AudioInput()
    
    print("5초 동안 녹음을 시작합니다...")
    audio_data = audio_input.record_for_duration(5)
    
    if audio_data.size > 0:
        print(f"녹음 완료. 데이터 모양: {audio_data.shape}, 타입: {audio_data.dtype}")
        
        # WAV 바이트로 변환 테스트
        wav_bytes = audio_input.get_wav_bytes(audio_data)
        print(f"WAV 바이트 크기: {len(wav_bytes)} 바이트")
        
        # 파일로 저장 테스트
        file_path = audio_input.save_to_wav_file(audio_data)
        print(f"WAV 파일이 저장되었습니다: {file_path}")
        
        # 저장된 파일 다시 로드 테스트
        loaded_data = audio_input.load_from_wav_file(file_path)
        print(f"파일을 로드했습니다. 데이터 모양: {loaded_data.shape}, 타입: {loaded_data.dtype}")
    else:
        print("녹음된 데이터가 없습니다.") 