import openai, os, logging
from typing import Optional
from dotenv import load_dotenv
load_dotenv()
# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def summarize_article_with_gpt(content: str) -> Optional[str]:
    try:
        # OpenAI API 키 확인
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            logger.error("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
            return None
        
        # OpenAI 클라이언트 설정
        client = openai.OpenAI(api_key=api_key)
        
        # 프롬프트 구성
        prompt = f"""
        해당 기사 본문을 읽고 요구사항에 맞게 요약해
본문:
{content}
요구사항:
1. 핵심 내용만 추출하여 500자 이내로 요약
2. 객관적이고 사실 중심으로 작성
3. 한국어로 작성
4. 불필요한 수식어나 반복 제거
5. ~했습니다 형식으로 말하기
"""
        # GPT API 호출
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "당신은 뉴스 기사를 요약하는 전문가입니다. 핵심 내용을 간결하고 명확하게 요약해주세요."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.3
        )
        summary = response.choices[0].message.content.strip()
        logger.info("기사 요약 완료")
        return summary
        
    except Exception as e:
        logger.error(f"기사 요약 중 오류 발생: {e}")
        return None