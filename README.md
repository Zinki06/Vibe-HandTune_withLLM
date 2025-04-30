# 🎼 제스처 기반 실시간 베이스 멜로디 생성 및 연주 시스템

## 📌 프로젝트 개요

사용자의 음성 입력(아이디어, 감정 표현)을 분석하여 초기 베이스 멜로디를 생성하고, 양손 제스처를 통해 실시간으로 멜로디의 리듬, 톤, 이펙트 등을 제어하며 상호작용적인 연주를 가능하게 하는 시스템입니다.

## ✨ 주요 기능

1.  **🗣️ 음성 -> 텍스트 변환 (STT):** 사용자의 음성 명령 또는 멜로디 설명을 텍스트로 변환합니다. (OpenAI Whisper 사용)
2.  **🧠 감정 분석 & 프리셋 선택:** 변환된 텍스트를 분석하여 감정을 파악하고, 미리 정의된 베이스 멜로디 프리셋(`bass_presets.json`)을 선택합니다. (OpenAI GPT-4o 사용)
3.  **🎶 MIDI 멜로디 생성:** 선택된 프리셋(조성, 템포, 리듬 등)을 기반으로 초기 MIDI 베이스라인을 생성합니다. (`mido` 라이브러리 사용)
4.  **🖐️ 제스처 기반 실시간 제어:**
    *   웹캠(`OpenCV`, `MediaPipe`) 또는 Leap Motion 센서를 통해 양손의 움직임과 모양을 인식합니다.
    *   **왼손:** 리듬 복잡도, 옥타브, 기본 패턴 변경
    *   **오른손:** 필터 컷오프, 피치/레조넌스, 이펙트(리버브/딜레이) 양 조절
    *   **양손 거리:** 전체 템포 또는 마스터 새츄레이션 제어
5.  **📡 MIDI/OSC 출력:** 실시간으로 변형되는 MIDI 데이터를 가상 MIDI 포트 또는 OSC를 통해 DAW, 신디사이저, 시각화 툴(TouchDesigner 등)로 전송합니다.
6.  **👶 아동 친화적 GUI:** 직관적인 인터페이스로 아이들도 쉽게 사용할 수 있는 GUI를 제공합니다.

## 🛠️ 기술 스택

*   **파이썬 버전:** Python 3.11.11
*   **핵심 라이브러리:**
    *   **AI:** `openai` (Whisper, GPT-4o)
    *   **오디오:** `sounddevice`
    *   **제스처:** `opencv-python`, `mediapipe` (또는 Leap Motion SDK)
    *   **MIDI:** `mido`, `python-rtmidi`
    *   **GUI:** `customtkinter`
    *   **데이터 처리:** `numpy`, `json` 
    *   **(선택) OSC:** `python-osc`
*   **환경 설정:** `python-dotenv` (API 키 관리)
*   **외부 설정:** 가상 MIDI 포트 (macOS: IAC Driver, Windows: loopMIDI)

## 📋 구현된 모듈

### 1. 오디오 처리 모듈
- **AudioInput (src/audio_input.py)**: 마이크로부터 오디오 입력 캡처 및 처리
  - 실시간 오디오 스트림 캡처 및 WAV 포맷으로 변환
  - 오디오 파일 저장 및 로드 기능

- **VoiceDetector (src/voice_detector.py)**: 음성 활성화 감지(VAD)
  - 실시간 음성 감지 및 자동 녹음 시작/종료
  - 주변 소음에 맞춰 임계값 자동 조정

### 2. 텍스트 및 감정 분석 모듈
- **STTHandler (src/stt_handler.py)**: 음성-텍스트 변환
  - OpenAI Whisper API 연동
  - 오디오 파일 및 실시간 오디오 스트림을 텍스트로 변환

- **EmotionAnalyzer (src/emotion_analyzer.py)**: 텍스트 기반 감정 분석
  - OpenAI GPT-4o 모델을 사용한 감정 분석
  - 감정을 1-5 숫자로 분류 (1:슬픔 ~ 5:흥분)

### 3. MIDI 생성 및 출력 모듈
- **PresetLoader (src/preset_loader.py)**: 베이스 멜로디 프리셋 관리
  - 감정별 MIDI 프리셋 로드 및 관리
  - JSON 기반 프리셋 데이터 처리

- **MidiGenerator (src/midi_generator.py)**: MIDI 메시지 생성
  - 프리셋 정보(템포, 리듬, 노트)를 MIDI 메시지로 변환
  - 음표 이름을 MIDI 노트 번호로 변환
  - 리듬 패턴 문자열을 노트 길이로 변환

- **MidiOutput (src/midi_output.py)**: MIDI 출력 관리
  - 시스템의 MIDI 출력 포트 목록 조회
  - MIDI 포트 열기 및 메시지 전송
  - 가상 MIDI 포트 생성 및 관리

### 4. GUI 인터페이스
- **AudioRecorderGUI (src/audio_gui.py)**: 아이들을 위한 GUI 인터페이스
  - 마이크 버튼으로 녹음 시작/종료 제어
  - 녹음 파일 목록 관리 및 텍스트 변환 결과 표시
  - 직관적인 애니메이션과 피드백

## 🚀 설치 및 실행

1.  **저장소 복제:**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **가상 환경 생성 및 활성화:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # macOS/Linux
    # venv\Scripts\activate  # Windows
    ```

3.  **의존성 설치:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **API 키 설정:**
    *   `.env.example` 파일을 복사하여 `.env` 파일을 생성합니다.
    *   `.env` 파일 안에 OpenAI API 키를 입력합니다.
      ```dotenv
      OPENAI_API_KEY='sk-...'
      ```

5.  **가상 MIDI 포트 설정:**
    *   **Mac OS:** Audio MIDI 설정 앱에서 IAC 드라이버 활성화
        1. Spotlight에서 "Audio MIDI 설정"을 검색해 실행
        2. 메뉴에서 "윈도우 > MIDI 스튜디오 보기" 클릭
        3. IAC 드라이버를 더블클릭하고 "기기가 온라인 상태임" 체크박스 활성화
        4. 우측 하단의 "적용" 버튼 클릭
    *   **Windows:** loopMIDI 설치 및 설정
        1. loopMIDI 다운로드 및 설치
        2. '+' 버튼을 눌러 가상 포트 생성

6.  **테스트 실행:**
    ```bash
    # 음성 입력 및 STT 테스트
    python src/main_stt_test.py
    
    # MIDI 생성 및 출력 테스트
    python src/main_midi_test.py
    ```

7.  **메인 프로그램 실행:**
    ```bash
    python src/main.py
    ```

## 📂 프로젝트 구조

```
.
├── src/                       # 소스 코드 디렉토리
│   ├── audio_input.py         # 오디오 입력 처리
│   ├── audio_gui.py           # 아이들을 위한 GUI 인터페이스
│   ├── config_loader.py       # 설정 로드 유틸리티
│   ├── emotion_analyzer.py    # 텍스트 기반 감정 분석
│   ├── midi_generator.py      # MIDI 메시지 생성
│   ├── midi_output.py         # MIDI 포트 관리 및 출력
│   ├── preset_loader.py       # 베이스 멜로디 프리셋 로더
│   ├── stt_handler.py         # 음성-텍스트 변환 처리
│   ├── voice_detector.py      # 음성 활성화 감지
│   ├── main_stt_test.py       # STT 테스트 스크립트
│   ├── main_midi_test.py      # MIDI 테스트 스크립트
│   ├── vad_stt_test.py        # VAD-STT 통합 테스트
│   └── main.py                # 메인 프로그램 진입점
├── config/                    # 설정 파일
│   └── bass_presets.json      # 감정별 베이스 멜로디 프리셋
├── audio_recordings/          # 녹음된 오디오 파일 저장 디렉토리
├── docs/                      # 문서 파일
│   ├── memory.md              # 프로젝트 진행 기록
│   └── ...
├── .env                       # API 키 (Git 무시됨)
├── .env.example               # 환경 변수 예시
├── requirements.txt           # Python 의존성 목록
└── README.md                  # 프로젝트 설명
```

## 📈 개발 현황

- ✅ 오디오 입력 및 STT 변환 모듈 구현
- ✅ 텍스트 기반 감정 분석 모듈 구현
- ✅ 프리셋 로드 및 MIDI 생성 모듈 구현
- ✅ MIDI 출력 및 가상 포트 연결 구현
- ✅ GUI 인터페이스 구현
- 🔄 제스처 인식 모듈 개발 중
- 🔄 제스처-MIDI 매핑 모듈 개발 중
- 🔄 전체 통합 및 실시간 처리 파이프라인 개발 중

## 📄 라이선스

(프로젝트 라이선스 정보를 여기에 기입) 