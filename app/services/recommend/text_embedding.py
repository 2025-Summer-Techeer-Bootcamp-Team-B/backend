import os
import asyncio
import logging
from typing import List
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()

async_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def get_embedding_async(text: str) -> list:
    """단일 텍스트의 임베딩을 생성합니다."""
    response = await async_client.embeddings.create(
        input=text,
        model="text-embedding-ada-002"
    )
    return response.data[0].embedding

async def get_embeddings_batch_async(texts: List[str]) -> List[List[float]]:
    """여러 텍스트의 임베딩을 배치로 생성합니다."""
    try:
        response = await async_client.embeddings.create(
            input=texts,
            model="text-embedding-ada-002"
        )
        return [r.embedding for r in response.data]
    except Exception as e:
        logging.error(f"❌ Embedding batch 실패: {e}")
        raise

async def get_embedding_async_limited(text: str, semaphore: asyncio.Semaphore) -> list:
    """세마포어를 적용한 임베딩 생성 (동시성 제한)"""
    async with semaphore:
        return await get_embedding_async(text) 