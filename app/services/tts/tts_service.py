import asyncio
from typing import Dict, Optional
from app.services.tts.tts_generator import TTSGenerator

class TTSService:
    def __init__(self):
        self.tts_generator = TTSGenerator()

    async def generate_male_female_audio(self, text: str) -> Dict[str, Optional[str]]:
        """남성과 여성 목소리로 동시에 TTS를 생성합니다."""
        print(f"남성/여성 TTS 생성 시작: text_length={len(text)}")
        
        # 남성과 여성 TTS를 동시에 생성
        male_task = self.tts_generator.generate_tts_audio(text, "ko-KR-Chirp3-HD-Charon", 1.1)
        female_task = self.tts_generator.generate_tts_audio(text, "ko-KR-Chirp3-HD-Kore", 1.1)
        
        male_url, female_url = await asyncio.gather(male_task, female_task)
        
        result = {
            "male_audio_url": male_url,
            "female_audio_url": female_url
        }
        print(f"남성/여성 TTS 생성 완료: {result}")
        return result 