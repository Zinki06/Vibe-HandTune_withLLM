"""
MIDI 출력 모듈: MIDI 포트 관리 및 메시지 전송
"""

import mido
import time
from typing import List, Optional

class MidiOutput:
    """MIDI 출력 관리 클래스"""
    
    def __init__(self):
        """MIDI 출력 초기화"""
        self.port = None
        
    def list_output_ports(self) -> List[str]:
        """
        사용 가능한 MIDI 출력 포트 목록 반환
        
        Returns:
            출력 포트 이름 리스트
        """
        return mido.get_output_names()
    
    def open_port(self, port_name: str) -> bool:
        """
        지정된 이름의 MIDI 출력 포트 열기
        
        Args:
            port_name: 열고자 하는 MIDI 포트 이름
            
        Returns:
            성공 여부 (True/False)
            
        Raises:
            IOError: 포트를 열 수 없는 경우
        """
        try:
            # 이미 열린 포트가 있으면 닫기
            if self.port:
                self.close_port()
                
            # 지정된 이름의 포트 열기
            self.port = mido.open_output(port_name)
            return True
        except (IOError, ValueError) as e:
            print(f"MIDI 포트 '{port_name}' 열기 실패: {e}")
            return False
            
    def open_virtual_port(self, port_name: str) -> bool:
        """
        가상 MIDI 출력 포트 생성 및 열기
        
        Args:
            port_name: 생성할 가상 포트 이름
            
        Returns:
            성공 여부 (True/False)
        """
        try:
            # 이미 열린 포트가 있으면 닫기
            if self.port:
                self.close_port()
                
            # 가상 포트 생성 및 열기
            self.port = mido.open_output(port_name, virtual=True)
            return True
        except (IOError, ValueError, AttributeError) as e:
            # 가상 포트를 지원하지 않는 백엔드 또는 기타 오류
            print(f"가상 MIDI 포트 '{port_name}' 생성 실패: {e}")
            print("참고: 백엔드에 따라 가상 포트 생성이 지원되지 않을 수 있습니다.")
            return False
    
    def send_message(self, message: mido.Message) -> bool:
        """
        단일 MIDI 메시지 전송
        
        Args:
            message: 전송할 MIDI 메시지
            
        Returns:
            성공 여부 (True/False)
        """
        if not self.port:
            print("MIDI 출력 포트가 열려있지 않습니다.")
            return False
            
        try:
            self.port.send(message)
            return True
        except Exception as e:
            print(f"MIDI 메시지 전송 실패: {e}")
            return False
    
    def send_messages(self, messages: List[mido.Message]) -> bool:
        """
        MIDI 메시지 리스트를 적절한 타이밍으로 전송
        
        Args:
            messages: 전송할 MIDI 메시지 리스트
            
        Returns:
            성공 여부 (True/False)
        """
        if not self.port:
            print("MIDI 출력 포트가 열려있지 않습니다.")
            return False
            
        try:
            for msg in messages:
                if msg.time > 0:
                    # 메시지 간 딜레이 적용
                    time.sleep(msg.time)
                # 메시지 전송
                self.port.send(msg)
            return True
        except Exception as e:
            print(f"MIDI 메시지 시퀀스 전송 실패: {e}")
            return False
    
    def close_port(self) -> None:
        """현재 열린 MIDI 포트 닫기"""
        if self.port:
            self.port.close()
            self.port = None 