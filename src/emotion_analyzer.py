"""
텍스트 기반 감정 분석 모듈입니다.
OpenAI의 GPT-4o API를 사용하여 텍스트에서 감정을 분석하고, 
1~5 사이의 숫자로 분류합니다.
"""

import os
import re
from openai import OpenAI
from src.config_loader import load_api_key

class EmotionAnalyzer:
    """
    텍스트 기반 감정 분석 클래스입니다.
    """
    
    def __init__(self, model="gpt-4o-mini", temperature=0.2):
        """
        EmotionAnalyzer 클래스 초기화
        
        Parameters:
        -----------
        model : str
            사용할 OpenAI 모델 이름
        temperature : float
            모델의 온도 값 (0~1, 낮을수록 더 확정적인 결과)
        """
        # OpenAI API 키 로드
        api_key = load_api_key()
        self.client = OpenAI(api_key=api_key)
        
        # 모델 파라미터
        self.model = model
        self.temperature = temperature
        
        # 감정 매핑 (번호: 이름)
        self.emotion_map = {
            "1": "슬픔",
            "2": "평온",
            "3": "중립",
            "4": "행복",
            "5": "흥분"
        }
    
    def _create_emotion_prompt(self, text):
        """
        감정 분석을 위한 프롬프트를 생성합니다.
        
        Parameters:
        -----------
        text : str
            분석할 텍스트
            
        Returns:
        --------
        list
            OpenAI API에 전송할 메시지 리스트
        """
        # 시스템 메시지: 분석 방법 지정
        system_message = """당신은 감정 분석 전문가입니다. 
입력된 텍스트에서 표현된 감정을 아래 다섯 가지 중 하나로 분류하고, 
해당 감정에 대응되는 숫자만 응답해야 합니다. 다른 설명이나 텍스트는 추가하지 마세요.

1: 슬픔 - 우울함, 슬픔, 상실감, 절망
2: 평온 - 안정, 차분함, 평화로움
3: 중립 - 감정이 없거나 중립적, 일상적
4: 행복 - 기쁨, 즐거움, 만족감
5: 흥분 - 열정, 활기참, 에너지, 격앙됨

숫자만 답변하세요. 1, 2, 3, 4, 5 중에서만 응답하세요."""

        # 사용자 메시지: 분석할 텍스트
        user_message = f"다음 텍스트의 감정을 분석해주세요: {text}"
        
        # 메시지 리스트 구성
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]
        
        return messages
    
    def analyze_emotion(self, text):
        """
        텍스트에서 감정을 분석하여 1~5 사이의 숫자로 반환합니다.
        
        Parameters:
        -----------
        text : str
            분석할 텍스트
            
        Returns:
        --------
        int
            감정을 나타내는 숫자 (1~5)
        """
        if not text or not isinstance(text, str):
            print("텍스트가 유효하지 않습니다.")
            return 3  # 기본값: 중립
        
        # 빈 텍스트 처리
        text = text.strip()
        if not text:
            print("빈 텍스트입니다.")
            return 3  # 기본값: 중립
        
        try:
            # 프롬프트 생성
            messages = self._create_emotion_prompt(text)
            
            # API 호출
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=10  # 짧은 응답만 필요
            )
            
            # 응답 추출
            result = response.choices[0].message.content.strip()
            
            # 응답 유효성 검사 및 정제
            emotion_number = self._validate_response(result)
            
            # 결과 반환
            return emotion_number
            
        except Exception as e:
            print(f"감정 분석 중 오류 발생: {str(e)}")
            return 3  # 기본값: 중립
    
    def _validate_response(self, response):
        """
        API 응답에서 유효한 감정 번호를 추출합니다.
        
        Parameters:
        -----------
        response : str
            API 응답 텍스트
            
        Returns:
        --------
        int
            유효한 감정 번호 (1~5)
        """
        # 숫자만 추출
        match = re.search(r'[1-5]', response)
        
        if match:
            # 유효한 감정 번호 (문자열)
            emotion_str = match.group(0)
            # 숫자로 변환
            return int(emotion_str)
        else:
            # 응답에서 유효한 감정 번호를 찾지 못한 경우
            print(f"유효하지 않은 응답: {response}")
            # 기본값: 중립
            return 3
    
    def get_emotion_name(self, emotion_number):
        """
        감정 번호에 해당하는 감정 이름을 반환합니다.
        
        Parameters:
        -----------
        emotion_number : int or str
            감정 번호
            
        Returns:
        --------
        str
            감정 이름
        """
        emotion_key = str(emotion_number)
        return self.emotion_map.get(emotion_key, "중립")

# 간단한 테스트 코드
if __name__ == "__main__":
    # 감정 분석기 생성
    emotion_analyzer = EmotionAnalyzer()
    
    # 테스트 문장 목록
    test_texts = [
        "오늘은 정말 슬프고 우울한 하루였어...",
        "평화롭고 고요한 밤이야.",
        "그냥 보통 하루였어. 특별한 일은 없었어.",
        "와! 정말 즐겁고 신나는 여행이었어!",
        "너무 흥분되고 열정적인 공연이었다!"
    ]
    
    # 각 문장 감정 분석
    for text in test_texts:
        emotion_number = emotion_analyzer.analyze_emotion(text)
        emotion_name = emotion_analyzer.get_emotion_name(emotion_number)
        
        print(f"\n텍스트: \"{text}\"")
        print(f"감정 번호: {emotion_number}")
        print(f"감정 이름: {emotion_name}") 