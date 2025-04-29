"""
음성-텍스트 변환(Speech-to-Text) 처리 모듈입니다.
OpenAI의 Whisper API를 사용하여 오디오를 텍스트로 변환합니다.
"""

import os
from openai import OpenAI
import time
import numpy as np
from src.config_loader import load_api_key

class STTHandler:
    """
    Whisper API를 사용하여 Speech-to-Text 변환을 처리하는 클래스입니다.
    """
    def __init__(self, model="whisper-1", language="ko", temperature=0):
        """
        STTHandler 클래스 초기화

        Parameters:
        -----------
        model : str
            사용할 Whisper 모델 이름
        language : str
            인식할 언어 코드 (예: 'ko', 'en', 'ja')
        temperature : float
            모델의 온도 값 (0~1, 낮을수록 더 확정적인 결과)
        """
        api_key = load_api_key()
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.language = language
        self.temperature = temperature
        self.max_retries = 3
        self.retry_delay = 2  # 초 단위

    def transcribe_audio(self, audio_data_or_path, prompt=""):
        """
        오디오 데이터를 텍스트로 변환합니다.

        Parameters:
        -----------
        audio_data_or_path : bytes, str or numpy.ndarray
            텍스트로 변환할 오디오 데이터 또는 파일 경로
        prompt : str
            STT 결과를 안내하는 프롬프트 (특정 단어나 문맥을 힌트로 제공)

        Returns:
        --------
        str
            변환된 텍스트
        """
        # 타입 확인 및 처리
        if isinstance(audio_data_or_path, str):
            # 파일 경로인 경우 파일 열기
            audio_file = open(audio_data_or_path, "rb")
        elif isinstance(audio_data_or_path, np.ndarray):
            # 오류 반환
            raise ValueError("NumPy 배열은 직접 처리할 수 없습니다. WAV 바이트로 먼저 변환해주세요.")
        else:
            # 바이트 데이터인 경우 그대로 사용
            audio_file = audio_data_or_path

        # 오디오가 비어있는지 확인
        if hasattr(audio_file, "read") and len(audio_file.read(1)) == 0:
            audio_file.seek(0)  # 포인터 초기화
            return ""

        if isinstance(audio_file, bytes) and len(audio_file) == 0:
            return ""

        # API 호출 시도
        for attempt in range(self.max_retries):
            try:
                # API 호출 준비
                if isinstance(audio_file, bytes):
                    # 바이트 데이터인 경우 임시 파일 객체로 변환
                    from io import BytesIO
                    audio_file = ("audio.wav", audio_file, "audio/wav")

                # Whisper API 호출
                response = self.client.audio.transcriptions.create(
                    model=self.model,
                    file=audio_file,
                    language=self.language,
                    prompt=prompt,
                    temperature=self.temperature,
                    response_format="text"
                )
                
                # 결과 반환
                return response.text
                
            except Exception as e:
                print(f"STT 변환 시도 {attempt+1}/{self.max_retries} 실패: {str(e)}")
                
                # 파일 포인터 초기화 (파일 객체인 경우)
                if hasattr(audio_file, "seek"):
                    audio_file.seek(0)
                
                # 마지막 시도가 아니면 대기 후 재시도
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    raise RuntimeError(f"STT 변환 실패 (최대 시도 횟수 초과): {str(e)}")
        
        return ""  # 여기까지 오면 빈 문자열 반환 (실제로는 위에서 예외 발생)

    def transcribe_chunks(self, audio_chunks, prompt=""):
        """
        여러 오디오 청크를 처리하고 결과를 결합합니다.

        Parameters:
        -----------
        audio_chunks : list
            오디오 청크 목록 (WAV 바이트 또는 파일 경로)
        prompt : str
            STT 결과를 안내하는 프롬프트

        Returns:
        --------
        str
            변환된 텍스트
        """
        results = []
        
        for chunk in audio_chunks:
            text = self.transcribe_audio(chunk, prompt)
            if text:
                results.append(text)
        
        return " ".join(results)

    def transcribe_wav_file(self, file_path, prompt=""):
        """
        WAV 파일을 직접 텍스트로 변환합니다.
        
        Parameters:
        -----------
        file_path : str
            변환할 WAV 파일 경로
        prompt : str
            STT 결과를 안내하는 프롬프트
            
        Returns:
        --------
        str
            변환된 텍스트
        """
        if not os.path.exists(file_path):
            print(f"파일이 존재하지 않습니다: {file_path}")
            return ""
        
        if not file_path.lower().endswith('.wav'):
            print(f"WAV 파일이 아닙니다: {file_path}")
            return ""
        
        try:
            # 파일을 직접 열어서 변환
            with open(file_path, 'rb') as audio_file:
                return self.transcribe_audio(audio_file, prompt)
        except Exception as e:
            print(f"WAV 파일 변환 중 오류 발생: {str(e)}")
            return ""

# 테스트 코드
if __name__ == "__main__":
    from src.audio_input import AudioInput
    import os
    
    # 오디오 입력 모듈 초기화
    audio_input = AudioInput()
    
    # STT 핸들러 초기화
    stt_handler = STTHandler()
    
    # 테스트 모드 선택 (1: 실시간 녹음 후 변환, 2: 파일에서 변환)
    test_mode = input("테스트 모드 선택 (1: 실시간 녹음, 2: 파일 변환): ")
    
    if test_mode == "1":
        # 5초 동안 녹음
        print("5초 동안 말씀해주세요...")
        audio_data = audio_input.record_for_duration(5)
        
        if audio_data.size > 0:
            # WAV 바이트로 변환
            wav_bytes = audio_input.get_wav_bytes(audio_data)
            
            # 파일로 저장
            file_path = audio_input.save_to_wav_file(audio_data)
            
            # 텍스트로 변환
            print("음성을 텍스트로 변환 중...")
            text = stt_handler.transcribe_audio(wav_bytes)
            
            print(f"변환 결과: {text}")
    
    elif test_mode == "2":
        # 파일 경로 입력 또는 기본값 사용
        file_path = input("변환할 WAV 파일 경로 (기본값: 가장 최근 녹음): ")
        
        if not file_path:
            # 오디오 녹음 디렉토리에서 가장 최근 파일 찾기
            recordings_dir = "audio_recordings"
            if os.path.exists(recordings_dir):
                wav_files = [os.path.join(recordings_dir, f) for f in os.listdir(recordings_dir) if f.endswith('.wav')]
                if wav_files:
                    wav_files.sort(key=os.path.getmtime, reverse=True)
                    file_path = wav_files[0]
                    print(f"가장 최근 녹음 파일 사용: {file_path}")
        
        if file_path and os.path.exists(file_path):
            # 파일에서 직접 변환
            print(f"파일을 텍스트로 변환 중: {file_path}")
            text = stt_handler.transcribe_wav_file(file_path)
            
            print(f"변환 결과: {text}")
        else:
            print("유효한 파일 경로가 없습니다.")
    
    else:
        print("잘못된 테스트 모드 선택") 