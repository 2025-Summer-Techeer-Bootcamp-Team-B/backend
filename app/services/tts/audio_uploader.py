import os
import tempfile
from typing import Optional
from google.cloud import storage
from datetime import datetime
import uuid

class AudioUploader:
    def __init__(self):
        self.storage_client = storage.Client()
        self.bucket_name = os.getenv("GOOGLE_CLOUD_STORAGE_BUCKET")
        self.bucket = self.storage_client.bucket(self.bucket_name)

    async def upload_audio_to_gcs(self, audio_content: bytes, voice_name: str) -> Optional[str]:
        """오디오 파일을 Google Cloud Storage에 업로드합니다."""
        temp_path = None
        try:
            # 임시 파일 생성
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as out:
                out.write(audio_content)
                temp_path = out.name
            
            # GCS 파일 키 생성
            file_key = f"audio/{datetime.now().strftime('%Y/%m/%d')}/{uuid.uuid4()}.mp3"
            print(f"Google Cloud Storage 업로드 시작: bucket={self.bucket_name}, key={file_key}")
            
            # GCS에 업로드
            blob = self.bucket.blob(file_key)
            blob.upload_from_filename(temp_path, content_type='audio/mpeg')
            
            # 임시 파일 삭제
            os.unlink(temp_path)
            
            gcs_url = f"https://storage.googleapis.com/{self.bucket_name}/{file_key}"
            print(f"오디오 업로드 완료: voice={voice_name}, url={gcs_url}")
            return gcs_url
            
        except Exception as e:
            print(f"Google Cloud Storage 업로드 실패: voice={voice_name}, error={e}")
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)
            return None 