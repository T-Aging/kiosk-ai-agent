import sounddevice as sd
from scipy.io.wavfile import write
from openai import OpenAI
import os
import tempfile
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def record_and_stt(duration=5, fs=16000):
    # 랜덤 tmp.wav 파일 생성, delete=True -> with 블록 끝난 후 삭제
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as tmp:
        filename = tmp.name
        print("[STT] 녹음 시작!")

        recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
        sd.wait()
        write(filename, fs, recording)
        print("[STT] 녹음 완료!")

        # tmp.wav 파일을 STT로 변환
        with open(filename, "rb") as f:
            resp = client.audio.transcriptions.create(
                model="gpt-4o-transcribe",
                file=f,
                response_format="text"
            )
        
    user_text = resp.strip()
    print("[STT] 변환 완료:", user_text)

    return user_text
