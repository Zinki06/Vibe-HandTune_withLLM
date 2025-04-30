"""
MIDI 메시지 생성 모듈: 프리셋 정보를 바탕으로 MIDI 시퀀스(note_on/off 메시지)를 생성
"""

import mido
import time
from typing import List, Dict, Union, Optional

# 음표 이름을 MIDI 노트 번호로 변환하는 딕셔너리
NOTE_TO_MIDI = {
    'C0': 12, 'C#0': 13, 'D0': 14, 'D#0': 15, 'E0': 16, 'F0': 17, 
    'F#0': 18, 'G0': 19, 'G#0': 20, 'A0': 21, 'A#0': 22, 'B0': 23,
    'C1': 24, 'C#1': 25, 'D1': 26, 'D#1': 27, 'E1': 28, 'F1': 29, 
    'F#1': 30, 'G1': 31, 'G#1': 32, 'A1': 33, 'A#1': 34, 'B1': 35,
    'C2': 36, 'C#2': 37, 'D2': 38, 'D#2': 39, 'E2': 40, 'F2': 41, 
    'F#2': 42, 'G2': 43, 'G#2': 44, 'A2': 45, 'A#2': 46, 'B2': 47,
    'C3': 48, 'C#3': 49, 'D3': 50, 'D#3': 51, 'E3': 52, 'F3': 53, 
    'F#3': 54, 'G3': 55, 'G#3': 56, 'A3': 57, 'A#3': 58, 'B3': 59,
    'C4': 60, 'C#4': 61, 'D4': 62, 'D#4': 63, 'E4': 64, 'F4': 65, 
    'F#4': 66, 'G4': 67, 'G#4': 68, 'A4': 69, 'A#4': 70, 'B4': 71,
}

class MidiGenerator:
    """MIDI 메시지 생성기"""
    
    def __init__(self, ticks_per_beat: int = 480):
        """
        MIDI 제너레이터 초기화
        
        Args:
            ticks_per_beat: MIDI 타이밍 해상도(기본값: 480)
        """
        self.ticks_per_beat = ticks_per_beat
        
    def note_name_to_number(self, note_name: str) -> int:
        """
        음표 이름을 MIDI 노트 번호로 변환
        
        Args:
            note_name: 음표 이름 (예: 'C3', 'G2')
            
        Returns:
            MIDI 노트 번호
            
        Raises:
            ValueError: 잘못된 음표 이름
        """
        if note_name in NOTE_TO_MIDI:
            return NOTE_TO_MIDI[note_name]
        raise ValueError(f"잘못된 음표 이름: {note_name}")
    
    def parse_rhythm(self, rhythm_pattern: str) -> List[float]:
        """
        리듬 패턴 문자열을 노트 길이 리스트로 변환
        
        Args:
            rhythm_pattern: 리듬 패턴 (예: '4,8,8,4' - 4분음표, 8분음표, 8분음표, 4분음표)
            
        Returns:
            노트 길이 리스트 (초 단위)
        """
        if not rhythm_pattern:
            return [1.0]  # 기본값: 4분음표
            
        # 쉼표로 구분된 숫자를 파싱
        parts = rhythm_pattern.split(',')
        note_lengths = []
        
        for part in parts:
            try:
                # 숫자는 음표 길이(분수)를 나타냄
                denominator = int(part.strip())
                if denominator <= 0:
                    raise ValueError(f"음표 길이는 양수여야 합니다: {denominator}")
                    
                # 4분음표 = 1.0을 기준으로 계산
                length = 4.0 / denominator
                note_lengths.append(length)
            except ValueError:
                # 잘못된 형식은 기본값(4분음표) 사용
                note_lengths.append(1.0)
                
        return note_lengths
    
    def generate_messages(self, preset: Dict[str, Union[str, int, float, List[str]]]) -> List[mido.Message]:
        """
        프리셋을 기반으로 MIDI 메시지 리스트 생성
        
        Args:
            preset: 프리셋 딕셔너리 (tempo, rhythm, notes)
            
        Returns:
            MIDI 메시지 객체 리스트
        """
        messages = []
        
        # 프리셋에서 필요한 정보 추출
        tempo = float(preset.get('tempo', 120))
        rhythm_pattern = str(preset.get('rhythm', '4,4,4,4'))
        notes = preset.get('notes', ['C3', 'E3', 'G3', 'C4'])
        
        # 리듬 패턴 파싱
        note_lengths = self.parse_rhythm(rhythm_pattern)
        
        # 박자 길이 계산 (초 단위)
        beat_duration = 60.0 / tempo  # 4분음표 길이(초)
        
        # 노트와 리듬 패턴을 조합하여 메시지 생성
        current_time = 0.0
        
        # 노트 수와 리듬 패턴 길이가 다를 경우를 처리
        pattern_length = len(note_lengths)
        
        for i, note_name in enumerate(notes):
            # 현재 노트에 해당하는 리듬 패턴 인덱스
            pattern_idx = i % pattern_length
            note_length = note_lengths[pattern_idx]
            
            # 노트 길이를 초 단위로 변환
            duration = note_length * beat_duration
            
            try:
                # 음표 이름을 MIDI 노트 번호로 변환
                note_number = self.note_name_to_number(note_name)
                
                # note_on 메시지 생성 (시작 시간 = 이전 노트의 종료 시간)
                messages.append(mido.Message('note_on', note=note_number, velocity=64, time=current_time))
                
                # note_off 메시지 생성 (시간 = 노트 길이)
                messages.append(mido.Message('note_off', note=note_number, velocity=64, time=current_time + duration))
                
                # 다음 노트의 시작 시간 업데이트
                current_time += duration
                
            except ValueError as e:
                print(f"노트 처리 중 오류 발생: {e}")
                continue
        
        return messages 