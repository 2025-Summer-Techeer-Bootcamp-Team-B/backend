import os
import asyncio
import tempfile
from typing import Dict, Optional
from google.cloud import texttospeech
import boto3
from botocore.exceptions import ClientError
from datetime import datetime
import uuid

class TTSGenerator:
    def __init__(self):
        self.tts_client = texttospeech.TextToSpeechClient()
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION")
        )
        self.bucket_name = os.getenv("AWS_S3_BUCKET")

    async def generate_tts_audio(self, text: str, voice_name: str = "ko-KR-Chirp3-HD-Charon", speaking_rate: float = 1.1) -> Optional[str]:
        temp_path = None
        try:
            synthesis_input = texttospeech.SynthesisInput(text=text)
            voice = texttospeech.VoiceSelectionParams(
                language_code="ko-KR",
                name=voice_name
            )
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=speaking_rate
            )
            response = self.tts_client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as out:
                out.write(response.audio_content)
                temp_path = out.name
            file_key = f"audio/{datetime.now().strftime('%Y/%m/%d')}/{uuid.uuid4()}.mp3"
            self.s3_client.upload_file(
                temp_path,
                self.bucket_name,
                file_key,
                ExtraArgs={'ContentType': 'audio/mpeg'}
            )
            os.unlink(temp_path)
            s3_url = f"https://{self.bucket_name}.s3.{os.getenv('AWS_REGION')}.amazonaws.com/{file_key}"
            return s3_url
        except Exception as e:
            print(f"Google TTS 생성 실패: {e}")
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)
            return None

    async def generate_male_female_audio(self, text: str) -> Dict[str, Optional[str]]:
        male_task = self.generate_tts_audio(text, "ko-KR-Chirp3-HD-Charon", 1.1)
        female_task = self.generate_tts_audio(text, "ko-KR-Chirp3-HD-Kore", 1.1)
        male_url, female_url = await asyncio.gather(male_task, female_task)
        return {
            "male_audio_url": male_url,
            "female_audio_url": female_url
        } 