import os
from typing import Optional
from google.cloud import texttospeech
from app.services.tts.audio_uploader import AudioUploader

class TTSGenerator:
    def __init__(self):
        self.tts_client = texttospeech.TextToSpeechClient()
        self.audio_uploader = AudioUploader()

    async def generate_tts_audio(self, text: str, voice_name: str = "ko-KR-Chirp3-HD-Charon", speaking_rate: float = 1.1) -> Optional[str]:
        """텍스트를 음성으로 변환하고 GCS에 업로드합니다."""
        try:
            print(f"TTS 생성 시작: voice={voice_name}, text_length={len(text)}")
            
            # TTS 요청 설정
            synthesis_input = texttospeech.SynthesisInput(text=text)
            voice = texttospeech.VoiceSelectionParams(
                language_code="ko-KR",
                name=voice_name
            )
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=speaking_rate
            )
            
            # Google TTS API 호출
            print(f"Google TTS API 호출 중: voice={voice_name}")
            response = self.tts_client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            print(f"Google TTS API 응답 성공: voice={voice_name}, audio_size={len(response.audio_content)}")
            
            # GCS에 업로드
            gcs_url = await self.audio_uploader.upload_audio_to_gcs(response.audio_content, voice_name)
            if gcs_url:
                print(f"TTS 생성 완료: voice={voice_name}, url={gcs_url}")
                return gcs_url
            else:
                print(f"TTS 업로드 실패: voice={voice_name}")
                return None
            
        except Exception as e:
            print(f"Google TTS 생성 실패: voice={voice_name}, error={e}")
            return None 