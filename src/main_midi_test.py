"""
MIDI 생성 및 출력 테스트 스크립트
"""

import os
import sys
import json
import time

# 프로젝트 루트 경로를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.midi_generator import MidiGenerator
from src.midi_output import MidiOutput

def load_sample_preset():
    """
    샘플 프리셋 데이터 로드 (테스트용)
    
    Returns:
        프리셋 딕셔너리
    """
    # 실제 프로젝트에서는 preset_loader.py에서 로드하지만, 테스트를 위한 임시 구현
    sample_preset = {
        'tempo': 120,
        'rhythm': '4,8,8,4',  # 4분음표, 8분음표, 8분음표, 4분음표
        'notes': ['C3', 'E3', 'G3', 'C4', 'G3', 'E3']
    }
    return sample_preset

def main():
    """MIDI 생성 및 출력 테스트 메인 함수"""
    print("MIDI 생성 및 출력 테스트 시작...")
    
    # MIDI 생성기 초기화
    midi_generator = MidiGenerator()
    
    # MIDI 출력 초기화
    midi_output = MidiOutput()
    
    # 사용 가능한 MIDI 포트 목록 출력
    available_ports = midi_output.list_output_ports()
    print("\n사용 가능한 MIDI 출력 포트:")
    for i, port in enumerate(available_ports):
        print(f"  {i+1}. {port}")
    
    # 샘플 프리셋 로드
    preset = load_sample_preset()
    print(f"\n샘플 프리셋 정보:")
    print(f"  템포: {preset['tempo']} BPM")
    print(f"  리듬: {preset['rhythm']}")
    print(f"  노트: {', '.join(preset['notes'])}")
    
    # MIDI 메시지 생성
    messages = midi_generator.generate_messages(preset)
    print(f"\n생성된 MIDI 메시지 수: {len(messages)}")
    
    # 포트 선택 또는 가상 포트 생성
    if not available_ports:
        print("\n사용 가능한 MIDI 포트가 없습니다.")
        create_virtual = input("가상 MIDI 포트를 생성하시겠습니까? (y/n): ").lower() == 'y'
        
        if create_virtual:
            port_name = input("생성할 가상 포트 이름 입력: ")
            if midi_output.open_virtual_port(port_name):
                print(f"가상 포트 '{port_name}' 생성 및 열기 성공")
            else:
                print("MIDI 포트를 열 수 없습니다. 프로그램을 종료합니다.")
                return
        else:
            print("MIDI 포트를 선택하지 않았습니다. 프로그램을 종료합니다.")
            return
    else:
        # 사용자로부터 포트 선택 입력 받기
        while True:
            try:
                choice = input("\n사용할 MIDI 포트 번호 선택 (q로 종료): ")
                if choice.lower() == 'q':
                    print("프로그램을 종료합니다.")
                    return
                    
                port_idx = int(choice) - 1
                if 0 <= port_idx < len(available_ports):
                    selected_port = available_ports[port_idx]
                    if midi_output.open_port(selected_port):
                        print(f"포트 '{selected_port}' 열기 성공")
                        break
                else:
                    print("잘못된 포트 번호입니다. 다시 시도하세요.")
            except ValueError:
                print("숫자를 입력하세요.")
    
    # MIDI 메시지 전송
    print("\nMIDI 메시지 전송 중...")
    if midi_output.send_messages(messages):
        print("MIDI 메시지 전송 완료")
    else:
        print("MIDI 메시지 전송 실패")
    
    # 포트 닫기
    midi_output.close_port()
    print("\nMIDI 포트 닫힘")
    print("테스트 종료")

if __name__ == "__main__":
    main() 