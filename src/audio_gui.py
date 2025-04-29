"""
아이들을 위한 오디오 녹음 및 STT 변환 GUI 모듈입니다.
마이크 아이콘을 클릭하여 녹음을 시작/종료하고, 변환된 텍스트를 표시합니다.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import os
import threading
import time
import numpy as np
from PIL import Image, ImageTk
import datetime
import queue

from src.audio_input import AudioInput
from src.stt_handler import STTHandler
from src.emotion_analyzer import EmotionAnalyzer
from src.preset_loader import PresetLoader

# 기본 색상 정의
BACKGROUND_COLOR = "#f0f0ff"  # 밝은 하늘색 배경
PRIMARY_COLOR = "#ff7eb9"     # 분홍색 (아이들이 좋아하는 색상)
SECONDARY_COLOR = "#7afcff"   # 청록색
TEXT_COLOR = "#333333"        # 어두운 회색 텍스트
BUTTON_COLOR = "#ff9e7e"      # 주황색 버튼

# 감정별 색상 정의
EMOTION_COLORS = {
    "1": "#a0a0ff",  # 슬픔: 파란색
    "2": "#a0ffa0",  # 평온: 녹색
    "3": "#d0d0d0",  # 중립: 회색
    "4": "#ffffa0",  # 행복: 노란색
    "5": "#ffa0a0"   # 흥분: 빨간색
}

# 애니메이션 주기 (밀리초)
ANIMATION_INTERVAL = 100  # 100ms마다 애니메이션 업데이트

class AudioRecorderGUI:
    """
    아이들을 위한 오디오 녹음 및 STT 변환 GUI 클래스입니다.
    """
    def __init__(self, root):
        """
        GUI 초기화
        
        Parameters:
        -----------
        root : tk.Tk
            tkinter 루트 윈도우
        """
        self.root = root
        self.root.title("음성 마법사")
        self.root.geometry("800x600")
        self.root.configure(bg=BACKGROUND_COLOR)
        
        # 모듈 초기화
        self.audio_input = AudioInput(sample_rate=16000, channels=1, chunk_duration=0.1)
        self.stt_handler = STTHandler(language="ko", temperature=0)
        self.emotion_analyzer = EmotionAnalyzer()
        self.preset_loader = PresetLoader()
        
        # 상태 변수
        self.is_recording = False
        self.recording_thread = None
        self.animation_id = None
        self.audio_chunks = []
        self.audio_data = None
        self.last_saved_file = None
        self.current_emotion = None
        self.current_preset = None
        
        # 결과 큐 (스레드 간 데이터 전달)
        self.result_queue = queue.Queue()
        
        # 오디오 녹음 디렉토리 확인 및 생성
        self.recordings_dir = "audio_recordings"
        os.makedirs(self.recordings_dir, exist_ok=True)
        
        # GUI 구성
        self._create_widgets()
        self._load_recording_list()
        
        # 주기적으로 큐 확인
        self._check_queue()
    
    def _create_widgets(self):
        """
        GUI 위젯 생성 및 배치
        """
        # 프레임 구성
        self.title_frame = tk.Frame(self.root, bg=BACKGROUND_COLOR)
        self.title_frame.pack(pady=10)
        
        self.main_frame = tk.Frame(self.root, bg=BACKGROUND_COLOR)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # 좌우 분할
        self.left_frame = tk.Frame(self.main_frame, bg=BACKGROUND_COLOR)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
        
        self.right_frame = tk.Frame(self.main_frame, bg=BACKGROUND_COLOR)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10)
        
        # 제목 라벨
        self.title_label = tk.Label(
            self.title_frame, 
            text="음성 마법사", 
            font=("Arial", 24, "bold"),
            bg=BACKGROUND_COLOR,
            fg=PRIMARY_COLOR
        )
        self.title_label.pack(pady=10)
        
        # 왼쪽 프레임: 녹음 컨트롤 및 결과 표시
        self.control_frame = tk.Frame(self.left_frame, bg=BACKGROUND_COLOR)
        self.control_frame.pack(pady=20)
        
        # 마이크 버튼 이미지 생성 (원이 있는 간단한 마이크 아이콘)
        self.mic_canvas = tk.Canvas(
            self.control_frame, 
            width=100, 
            height=100, 
            bg=BACKGROUND_COLOR,
            bd=0, 
            highlightthickness=0
        )
        self.mic_canvas.pack(pady=10)
        
        # 마이크 아이콘 그리기
        self._draw_mic_icon(recording=False)
        
        # 마이크 버튼 클릭 이벤트 연결
        self.mic_canvas.bind("<Button-1>", self._toggle_recording)
        
        # 상태 라벨
        self.status_label = tk.Label(
            self.control_frame,
            text="마이크를 클릭하면 녹음이 시작됩니다",
            font=("Arial", 12),
            bg=BACKGROUND_COLOR,
            fg=TEXT_COLOR
        )
        self.status_label.pack(pady=10)
        
        # 결과 텍스트 영역
        self.result_frame = tk.LabelFrame(
            self.left_frame, 
            text="변환 결과", 
            font=("Arial", 12, "bold"),
            bg=BACKGROUND_COLOR,
            fg=TEXT_COLOR
        )
        self.result_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.result_text = scrolledtext.ScrolledText(
            self.result_frame,
            wrap=tk.WORD,
            font=("Arial", 12),
            bg="white",
            fg=TEXT_COLOR
        )
        self.result_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 오른쪽 프레임: 파일 목록
        self.files_frame = tk.LabelFrame(
            self.right_frame, 
            text="녹음 파일 목록", 
            font=("Arial", 12, "bold"),
            bg=BACKGROUND_COLOR,
            fg=TEXT_COLOR
        )
        self.files_frame.pack(fill=tk.BOTH, expand=True)
        
        self.files_listbox = tk.Listbox(
            self.files_frame,
            font=("Arial", 11),
            bg="white",
            fg=TEXT_COLOR,
            selectbackground=PRIMARY_COLOR,
            selectforeground="white"
        )
        self.files_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 파일 작업 버튼 프레임
        self.file_buttons_frame = tk.Frame(self.right_frame, bg=BACKGROUND_COLOR)
        self.file_buttons_frame.pack(fill=tk.X, pady=10)
        
        # 파일 불러오기 및 변환 버튼
        self.load_button = tk.Button(
            self.file_buttons_frame,
            text="선택한 파일 변환하기",
            font=("Arial", 11),
            bg=BUTTON_COLOR,
            fg="white",
            relief=tk.RAISED,
            command=self._convert_selected_file
        )
        self.load_button.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # 재생 버튼 (미구현)
        self.play_button = tk.Button(
            self.file_buttons_frame,
            text="파일 듣기",
            font=("Arial", 11),
            bg=BUTTON_COLOR,
            fg="white",
            relief=tk.RAISED,
            command=self._play_selected_file
        )
        self.play_button.pack(side=tk.RIGHT, padx=5, fill=tk.X, expand=True)
    
    def _draw_mic_icon(self, recording=False):
        """
        마이크 아이콘을 그립니다.
        
        Parameters:
        -----------
        recording : bool
            녹음 중인지 여부
        """
        self.mic_canvas.delete("all")
        
        # 배경 원
        if recording:
            color = "red"  # 녹음 중일 때는 빨간색
            pulse_radius = 50 + (time.time() % 1) * 10  # 맥박 효과 (0-10 픽셀 크기 변화)
            self.mic_canvas.create_oval(
                50-pulse_radius, 50-pulse_radius, 
                50+pulse_radius, 50+pulse_radius, 
                fill="", outline=color, width=2
            )
        else:
            color = PRIMARY_COLOR
        
        # 메인 원
        self.mic_canvas.create_oval(10, 10, 90, 90, fill=color, outline="")
        
        # 마이크 아이콘 (간단한 모양)
        if recording:
            # 정지 아이콘 (사각형)
            self.mic_canvas.create_rectangle(35, 35, 65, 65, fill="white", outline="")
        else:
            # 마이크 모양
            self.mic_canvas.create_rectangle(40, 30, 60, 60, fill="white", outline="")
            self.mic_canvas.create_rectangle(45, 60, 55, 70, fill="white", outline="")
            self.mic_canvas.create_line(50, 70, 50, 75, fill="white", width=3)
            self.mic_canvas.create_line(40, 75, 60, 75, fill="white", width=3)
    
    def _toggle_recording(self, event=None):
        """
        녹음 시작/종료를 토글합니다.
        """
        if self.is_recording:
            # 녹음 중이면 종료
            self._stop_recording()
        else:
            # 녹음 중이 아니면 시작
            self._start_recording()
    
    def _start_recording(self):
        """
        녹음을 시작합니다.
        """
        if self.is_recording:
            return
        
        # 상태 업데이트
        self.is_recording = True
        self.status_label.config(text="녹음 중... 마이크를 다시 클릭하면 종료됩니다")
        
        # 청크 초기화
        self.audio_chunks = []
        
        # 녹음 스레드 시작
        self.recording_thread = threading.Thread(target=self._recording_thread_func)
        self.recording_thread.daemon = True
        self.recording_thread.start()
        
        # 애니메이션 시작
        self._animate_mic_icon()
    
    def _stop_recording(self):
        """
        녹음을 종료합니다.
        """
        if not self.is_recording:
            return
        
        # 상태 업데이트
        self.is_recording = False
        self.status_label.config(text="녹음 종료. 처리 중...")
        
        # 애니메이션 중지
        if self.animation_id:
            self.root.after_cancel(self.animation_id)
            self.animation_id = None
        
        # 아이콘 업데이트
        self._draw_mic_icon(recording=False)
        
        # 스레드 종료를 기다림 (녹음 스레드가 알아서 종료됨)
        if self.recording_thread:
            self.recording_thread.join(timeout=2.0)
    
    def _recording_thread_func(self):
        """
        녹음 스레드 함수
        """
        try:
            # 녹음 시작
            self.audio_input.start_recording()
            
            # 녹음 중일 때만 계속 청크를 가져옴
            while self.is_recording:
                chunk = self.audio_input.get_audio_chunk(timeout=0.2)
                if chunk is not None:
                    self.audio_chunks.append(chunk)
                    
            # 녹음 중지
            self.audio_input.stop_recording()
            
            # 청크가 있으면 처리
            if self.audio_chunks:
                # 청크를 하나의 배열로 결합
                self.audio_data = np.vstack(self.audio_chunks)
                
                # 파일로 저장
                file_path = self.audio_input.save_to_wav_file(self.audio_data)
                self.last_saved_file = file_path
                
                # GUI 스레드에 완료 알림
                self.result_queue.put(("recording_complete", file_path))
            else:
                self.result_queue.put(("recording_error", "녹음된 데이터가 없습니다."))
        
        except Exception as e:
            print(f"녹음 스레드 오류: {str(e)}")
            self.result_queue.put(("recording_error", str(e)))
    
    def _check_queue(self):
        """
        결과 큐를 확인하고 GUI 업데이트
        """
        try:
            # 큐에서 메시지 가져옴 (대기하지 않음)
            while not self.result_queue.empty():
                msg_type, msg_data = self.result_queue.get_nowait()
                
                if msg_type == "recording_complete":
                    # 녹음 완료
                    file_path = msg_data
                    self.status_label.config(text="녹음이 완료되었습니다. 변환 중...")
                    
                    # 목록 새로고침
                    self._load_recording_list()
                    
                    # 파일에서 텍스트 변환 (스레드로 실행)
                    threading.Thread(
                        target=self._convert_file_thread,
                        args=(file_path,),
                        daemon=True
                    ).start()
                
                elif msg_type == "recording_error":
                    # 녹음 오류
                    self.status_label.config(text=f"녹음 오류: {msg_data}")
                
                elif msg_type == "conversion_complete":
                    # 변환 완료
                    text = msg_data
                    self.status_label.config(text="텍스트 변환이 완료되었습니다.")
                    self.result_text.delete(1.0, tk.END)
                    self.result_text.insert(tk.END, text)
                
                elif msg_type == "conversion_error":
                    # 변환 오류
                    self.status_label.config(text=f"변환 오류: {msg_data}")
        
        except Exception as e:
            print(f"큐 처리 오류: {str(e)}")
        
        # 주기적으로 큐 확인 (50ms마다)
        self.root.after(50, self._check_queue)
    
    def _animate_mic_icon(self):
        """
        마이크 아이콘 애니메이션
        """
        if self.is_recording:
            self._draw_mic_icon(recording=True)
            self.animation_id = self.root.after(ANIMATION_INTERVAL, self._animate_mic_icon)
    
    def _load_recording_list(self):
        """
        녹음 파일 목록을 로드하고 표시
        """
        # 리스트박스 초기화
        self.files_listbox.delete(0, tk.END)
        
        # 디렉토리가 있는지 확인
        if not os.path.exists(self.recordings_dir):
            return
        
        # WAV 파일 목록 가져오기
        wav_files = [f for f in os.listdir(self.recordings_dir) if f.endswith('.wav')]
        
        if not wav_files:
            self.files_listbox.insert(tk.END, "(녹음된 파일이 없습니다)")
            return
        
        # 파일을 시간 역순으로 정렬 (최신 파일이 맨 위에)
        wav_files.sort(key=lambda f: os.path.getmtime(os.path.join(self.recordings_dir, f)), reverse=True)
        
        # 목록에 추가
        for wav_file in wav_files:
            # 파일 생성 시간 가져오기
            file_path = os.path.join(self.recordings_dir, wav_file)
            mtime = os.path.getmtime(file_path)
            time_str = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
            
            # 리스트에 표시 형식: "파일명 (시간)"
            display_name = f"{wav_file} ({time_str})"
            self.files_listbox.insert(tk.END, display_name)
        
        # 가장 최근 파일 선택
        self.files_listbox.selection_set(0)
    
    def _convert_selected_file(self):
        """
        선택한 파일을 텍스트로 변환
        """
        # 선택된 아이템 가져오기
        selected_idx = self.files_listbox.curselection()
        if not selected_idx:
            messagebox.showinfo("알림", "변환할 파일을 선택해주세요.")
            return
        
        # 파일 이름 추출 (출력 형식에서 파일명만 추출)
        display_name = self.files_listbox.get(selected_idx[0])
        if display_name.startswith("("):
            # 파일이 없는 경우
            return
        
        file_name = display_name.split(" (")[0]
        file_path = os.path.join(self.recordings_dir, file_name)
        
        if not os.path.exists(file_path):
            messagebox.showinfo("오류", f"파일이 존재하지 않습니다: {file_path}")
            return
        
        # 상태 업데이트
        self.status_label.config(text=f"파일 변환 중: {file_name}")
        
        # 별도 스레드에서 변환 진행
        threading.Thread(
            target=self._convert_file_thread,
            args=(file_path,),
            daemon=True
        ).start()
    
    def _convert_file_thread(self, file_path):
        """
        파일을 텍스트로 변환하는 스레드 함수
        
        Parameters:
        -----------
        file_path : str
            변환할 WAV 파일 경로
        """
        try:
            # 파일에서 텍스트 변환
            text = self.stt_handler.transcribe_wav_file(file_path, prompt="음악, 감정 관련 단어")
            
            # 결과가 있으면 감정 분석 진행
            if text:
                # 감정 분석
                emotion_number = self.emotion_analyzer.analyze_emotion(text)
                emotion_name = self.emotion_analyzer.get_emotion_name(emotion_number)
                
                # 감정에 따른 프리셋 로드
                preset_info = self.preset_loader.get_preset_by_emotion(emotion_number)
                
                # 현재 감정 및 프리셋 저장
                self.current_emotion = str(emotion_number)
                self.current_preset = preset_info
                
                # 감정 분석 결과와 함께 텍스트 표시
                result_text = f"{text}\n\n[감정: {emotion_name} ({emotion_number}번)]\n"
                
                # 프리셋 정보 추가
                result_text += f"\n[선택된 베이스 프리셋]\n"
                for key, value in preset_info["preset"].items():
                    result_text += f"- {key}: {value}\n"
                
                # 결과 큐에 추가
                self.result_queue.put(("conversion_complete", result_text))
                
                # 감정에 따른 프리셋 정보 큐에 추가
                self.result_queue.put(("emotion_preset", (emotion_number, preset_info)))
            else:
                self.result_queue.put(("conversion_error", "텍스트 변환 결과가 없습니다."))
        
        except Exception as e:
            print(f"변환 스레드 오류: {str(e)}")
            self.result_queue.put(("conversion_error", str(e)))
    
    def _play_selected_file(self):
        """
        선택한 파일 재생 (현재는 구현되지 않음)
        """
        # 선택된 아이템 가져오기
        selected_idx = self.files_listbox.curselection()
        if not selected_idx:
            messagebox.showinfo("알림", "재생할 파일을 선택해주세요.")
            return
        
        # 파일 이름 추출
        display_name = self.files_listbox.get(selected_idx[0])
        if display_name.startswith("("):
            # 파일이 없는 경우
            return
        
        file_name = display_name.split(" (")[0]
        file_path = os.path.join(self.recordings_dir, file_name)
        
        if not os.path.exists(file_path):
            messagebox.showinfo("오류", f"파일이 존재하지 않습니다: {file_path}")
            return
        
        # 오디오 재생 기능은 추후 구현 예정
        messagebox.showinfo("알림", "오디오 재생 기능은 아직 구현되지 않았습니다.")

# 테스트 코드
if __name__ == "__main__":
    # tkinter 루트 윈도우 생성
    root = tk.Tk()
    
    # GUI 애플리케이션 생성
    app = AudioRecorderGUI(root)
    
    # 이벤트 루프 시작
    root.mainloop() 