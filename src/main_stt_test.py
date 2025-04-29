"""
음성 입력 및 STT 모듈 테스트 스크립트입니다.
마이크에서 오디오를 캡처하고 Whisper API를 사용해 텍스트로 변환하는 전체 과정을 테스트합니다.
"""

from src.audio_input import AudioInput
from src.stt_handler import STTHandler
import time

def test_audio_to_text(record_duration=5, prompt=""):
    """
    오디오 입력 및 STT 변환 통합 테스트 함수

    Parameters:
    -----------
    record_duration : float
        녹음할 시간 (초)
    prompt : str
        Whisper API에 전달할 프롬프트 (STT 품질 향상 힌트)
    """
    # 모듈 초기화
    print("오디오 입력 모듈 초기화 중...")
    audio_input = AudioInput(sample_rate=16000, channels=1, chunk_duration=1.0)
    
    print("STT 핸들러 초기화 중...")
    stt_handler = STTHandler(language="ko", temperature=0)
    
    # 녹음 시작
    print(f"{record_duration}초 동안 말씀해주세요...")
    audio_data = audio_input.record_for_duration(record_duration)
    
    if audio_data.size == 0:
        print("오디오 데이터가 없습니다.")
        return
    
    print(f"녹음 완료. 데이터 모양: {audio_data.shape}, 타입: {audio_data.dtype}")
    
    # WAV 바이트로 변환
    print("오디오 데이터를 WAV 형식으로 변환 중...")
    wav_bytes = audio_input.get_wav_bytes(audio_data)
    print(f"WAV 바이트 크기: {len(wav_bytes)} 바이트")
    
    # 텍스트로 변환
    print("Whisper API를 사용하여 음성을 텍스트로 변환 중...")
    start_time = time.time()
    
    text = stt_handler.transcribe_audio(wav_bytes, prompt=prompt)
    
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

def test_chunks_processing():
    """
    여러 오디오 청크를 처리하는 기능을 테스트합니다.
    각 청크는 2초 길이이며, 총 3개의 청크를 처리합니다.
    """
    # 모듈 초기화
    audio_input = AudioInput(sample_rate=16000, channels=1, chunk_duration=2.0)
    stt_handler = STTHandler(language="ko", temperature=0)
    
    # 청크 목록 준비
    chunks = []
    
    print("첫 번째 2초 청크 녹음...")
    audio_data1 = audio_input.record_for_duration(2)
    wav_bytes1 = audio_input.get_wav_bytes(audio_data1)
    chunks.append(wav_bytes1)
    
    time.sleep(0.5)  # 잠시 대기
    
    print("두 번째 2초 청크 녹음...")
    audio_data2 = audio_input.record_for_duration(2)
    wav_bytes2 = audio_input.get_wav_bytes(audio_data2)
    chunks.append(wav_bytes2)
    
    time.sleep(0.5)  # 잠시 대기
    
    print("세 번째 2초 청크 녹음...")
    audio_data3 = audio_input.record_for_duration(2)
    wav_bytes3 = audio_input.get_wav_bytes(audio_data3)
    chunks.append(wav_bytes3)
    
    # 청크들을 텍스트로 변환
    print("여러 청크를 텍스트로 변환 중...")
    text = stt_handler.transcribe_chunks(chunks)
    
    # 결과 출력
    print("\n" + "=" * 50)
    print("청크 처리 결과:")
    print("-" * 50)
    print(f"{text}")
    print("=" * 50)

if __name__ == "__main__":
    print("=== 단일 녹음 STT 테스트 ===")
    test_audio_to_text(record_duration=5, prompt="음악, 감정, 선율")
    
    print("\n\n=== 여러 청크 STT 테스트 ===")
    # test_chunks_processing()  # 필요한 경우 주석 해제 