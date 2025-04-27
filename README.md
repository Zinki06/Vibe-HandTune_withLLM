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

## 🛠️ 기술 스택

*   **파이썬 버전:** Python 3.12.2
*   **핵심 라이브러리:**
    *   **AI:** `openai` (Whisper, GPT-4o)
    *   **오디오:** `sounddevice`
    *   **제스처:** `opencv-python`, `mediapipe` (또는 Leap Motion SDK)
    *   **MIDI:** `mido`
    *   **데이터 처리:** `numpy`, `json`
    *   **(선택) OSC:** `python-osc`
*   **환경 설정:** `python-dotenv` (API 키 관리)
*   **외부 설정:** 가상 MIDI 포트 (macOS: IAC Driver, Windows: loopMIDI)

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
    *   운영체제에 맞는 가상 MIDI 포트(IAC Driver, loopMIDI 등)를 활성화/설치하고 설정합니다.
    *   (필요시) 코드 내에서 사용할 MIDI 포트 이름을 확인하고 수정합니다.

6.  **(선택) Leap Motion SDK 설치:**
    *   Leap Motion 컨트롤러를 사용하는 경우, 관련 SDK를 설치합니다.

7.  **프로그램 실행:**
    ```bash
    python main.py
    ```
    (실행 스크립트 이름은 실제 프로젝트에 맞게 변경)

## 📂 프로젝트 구조 (예시)

```
.
├── src/                # 소스 코드 디렉토리
│   ├── audio_input.py
│   ├── emotion_analysis.py
│   ├── gesture_recognition.py
│   ├── midi_handler.py
│   └── main.py
├── config/             # 설정 파일
│   └── bass_presets.json
├── docs/               # 문서 파일
│   ├── MainDevPlan.md
│   ├── UseLibrary.md
│   └── ...
├── .env                # API 키 (Git 무시됨)
├── .env.example
├── requirements.txt    # Python 의존성 목록
└── README.md           # 프로젝트 설명
```

## 📄 라이선스

(프로젝트 라이선스 정보를 여기에 기입) 