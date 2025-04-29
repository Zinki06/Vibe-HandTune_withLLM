"""
오디오 GUI 테스트 스크립트입니다.
아이들을 위한 GUI 인터페이스를 실행하여 음성 녹음 및 STT 변환 기능을 테스트합니다.
"""

import tkinter as tk
import sys
import os

# src 디렉토리를 Python 경로에 추가 (다른 디렉토리에서 실행하는 경우를 위함)
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from src.audio_gui import AudioRecorderGUI

def main():
    """
    GUI 애플리케이션을 실행합니다.
    """
    # 녹음 파일 저장 디렉토리 확인 및 생성
    recordings_dir = os.path.join(parent_dir, "audio_recordings")
    os.makedirs(recordings_dir, exist_ok=True)
    
    # tkinter 루트 윈도우 생성
    root = tk.Tk()
    
    # GUI 애플리케이션 생성
    app = AudioRecorderGUI(root)
    
    # 환영 메시지 표시
    app.result_text.insert(tk.END, "안녕하세요! 음성 마법사입니다.\n\n"
                            "왼쪽의 마이크 버튼을 클릭하면 녹음이 시작됩니다.\n"
                            "녹음을 마치려면 다시 마이크 버튼을 클릭하세요.\n\n"
                            "녹음된 파일은 오른쪽 목록에 표시되며,\n"
                            "파일을 선택하고 '선택한 파일 변환하기' 버튼을 클릭하면\n"
                            "텍스트로 변환됩니다.")
    
    # 이벤트 루프 시작
    root.mainloop()

if __name__ == "__main__":
    main() 