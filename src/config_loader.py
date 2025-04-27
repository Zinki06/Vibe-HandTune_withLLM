import os
import dotenv

def load_api_key():
    dotenv.load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OpenAI API Key not found in .env file.")
    return api_key

# 간단한 테스트 코드 (main 블록 내)
if __name__ == '__main__':
    try:
        key = load_api_key()
        print("API Key loaded successfully.")
    except ValueError as e:
        print(e) 