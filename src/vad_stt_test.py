"""
음성 활성화 감지(VAD)와 STT(Speech-to-Text)를 통합한 테스트 스크립트입니다.
음성이 감지되면 자동으로 녹음을 시작하고 Whisper API를 통해 텍스트로 변환합니다.
"""

import time
from src.audio_input import AudioInput
from src.stt_handler import STTHandler
from src.voice_detector import VoiceDetector

def process_detected_audio(audio_data, stt_handler):
    """
    감지된 오디오 데이터를 처리하는 함수
    
    Parameters:
    -----------
    audio_data : numpy.ndarray
        녹음된 오디오 데이터
    stt_handler : STTHandler
        텍스트 변환을 위한 STT 핸들러
    """
    # 오디오 정보 출력
    duration = audio_data.shape[0] / 16000  # 16kHz 샘플링 레이트 기준
    print(f"감지된 오디오 - 길이: {duration:.2f}초, 샘플 수: {audio_data.shape[0]}")
    
    # WAV 바이트로 변환
    audio_input = AudioInput()  # 임시로 생성하여 변환 기능 사용
    wav_bytes = audio_input.get_wav_bytes(audio_data)
    
    # STT 변환
    print("음성을 텍스트로 변환 중...")
    start_time = time.time()
    
    text = stt_handler.transcribe_audio(wav_bytes, prompt="음악, 감정 관련 단어")
    
    end_time = time.time()
    process_time = end_time - start_time
    
    # 결과 출력
    print("\n" + "=" * 50)
    print("음성-텍스트 변환 결과:")
    print("-" * 50)
    print(f"{text}")
    print("-" * 50)
    print(f"처리 시간: {process_time:.2f}초")
    print("=" * 50)
    
    return text

def main():
    """
    메인 실행 함수
    """
    # 모듈 초기화
    print("오디오 입력 모듈 초기화 중...")
    audio_input = AudioInput(sample_rate=16000, channels=1, chunk_duration=0.1)
    
    print("STT 핸들러 초기화 중...")
    stt_handler = STTHandler(language="ko", temperature=0)
    
    print("음성 감지기 초기화 중...")
    voice_detector = VoiceDetector(
        audio_input=audio_input,
        energy_threshold=0.05,
        pause_threshold=1.0,
        phrase_threshold=0.3,
        max_phrase_time=10.0
    )
    
    # 콜백 함수 정의 (클로저 사용)
    def audio_callback(audio_data):
        process_detected_audio(audio_data, stt_handler)
    
    # 주변 소음에 맞춰 임계값 조정
    voice_detector.adjust_for_ambient_noise(duration=2.0)
    
    # 음성 감지 시작
    print("\n음성 감지를 시작합니다. 말씀해 주세요. (종료하려면 Ctrl+C)")
    voice_detector.start_detection(callback=audio_callback)
    
    try:
        # 메인 스레드는 사용자 중단을 기다림
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n사용자에 의해 중단되었습니다.")
    finally:
        # 정리
        voice_detector.stop_detection()

if __name__ == "__main__":
    main() 