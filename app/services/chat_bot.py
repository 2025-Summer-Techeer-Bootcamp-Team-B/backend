from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage, AIMessage
from sqlalchemy.orm import Session
from app.models.news_article import NewsArticle
from typing import List, Optional, Dict
import os
import json
import redis
import uuid
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class NewsChatBot:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.7,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Redis 연결
        self.redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "redis"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=int(os.getenv("REDIS_DB", 0)),
            decode_responses=True
        )
        
        # 대화 만료 시간 (30분)
        self.conversation_expiry = 1800  # 30분
        
        # 뉴스 기사 관련 시스템 프롬프트
        self.system_prompt = """당신은 뉴스 기사에 대한 질문에 답변하는 전문적인 AI 어시스턴트입니다.
        
        다음 규칙을 따라주세요:
        1. 뉴스 기사와 관련된 질문에만 답변하세요
        2. 정확하고 객관적인 정보를 제공하세요
        3. 사용자가 제공한 기사 내용을 바탕으로 답변하세요
        4. 모르는 내용에 대해서는 솔직히 모른다고 답변하세요
        5. 한국어로 답변하세요
        6. 이전 대화 내용을 참고하여 연속적인 대화를 유지하세요
        7. 추가 정보를 필요로 하는 경우엔 원본 기사 주소를 제공하세요
        
        기사 정보:
        - 제목: {title}
        - 요약: {summary}
        - 카테고리: {category}
        - 언론사: {press}
        - 작성자: {author}
        - 발행일: {published_at}
        - 주소: {url}
        """ 
    
    def get_article_context(self, db: Session, article_id: str) -> dict:
        """기사 정보를 가져와서 컨텍스트로 만듭니다."""
        article = db.query(NewsArticle).filter(
            NewsArticle.id == article_id,
            NewsArticle.is_deleted == False
        ).first()
        
        if not article:
            return None
            
        return {
            "title": article.title,
            "summary": article.summary_text,
            "category": article.category_name,
            "press": article.press.press_name if article.press else "알 수 없음",
            "author": article.author,
            "published_at": article.published_at.strftime("%Y-%m-%d %H:%M"),
            "url": article.url
        }
    
    def create_conversation_id(self) -> str:
        """새로운 대화 ID를 생성합니다."""
        return str(uuid.uuid4())
    
    def get_conversation_history(self, conversation_id: str) -> List[Dict]:
        """Redis에서 대화 기록을 가져옵니다."""
        try:
            history_data = self.redis_client.get(f"chat_history:{conversation_id}")
            if history_data:
                return json.loads(history_data)
            return []
        except Exception as e:
            print(f"대화 기록 조회 오류: {e}")
            return []
    
    def save_conversation_history(self, conversation_id: str, history: List[Dict]):
        """Redis에 대화 기록을 저장합니다."""
        try:
            history_json = json.dumps(history, ensure_ascii=False)
            key = f"chat_history:{conversation_id}"
            # 키가 없으면 setex(만료 30분), 있으면 set(key, value, keepttl=True)로 TTL 유지
            if self.redis_client.exists(key):
                self.redis_client.set(key, history_json, keepttl=True)
            else:
                self.redis_client.setex(key, self.conversation_expiry, history_json)
        except Exception as e:
            print(f"대화 기록 저장 오류: {e}")
    
    def chat_with_article(self, message: str, article_context: dict, conversation_id: str = None) -> Dict:
        """기사 컨텍스트와 함께 챗봇과 대화합니다."""
        # 새로운 대화 ID 생성 (제공되지 않은 경우)
        if not conversation_id:
            conversation_id = self.create_conversation_id()
        
        conversation_history = self.get_conversation_history(conversation_id)
        
        system_message = self.system_prompt.format(**article_context)
        
        messages = [SystemMessage(content=system_message)]
        
        for msg in conversation_history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))
        
        messages.append(HumanMessage(content=message))
        
        try:
            response = self.llm.invoke(messages)
            ai_response = response.content
            
            conversation_history.append({"role": "user", "content": message, "timestamp": datetime.now().isoformat()})
            conversation_history.append({"role": "assistant", "content": ai_response, "timestamp": datetime.now().isoformat()})
            
            self.save_conversation_history(conversation_id, conversation_history)
            ttl = self.redis_client.ttl(f"chat_history:{conversation_id}")
            if ttl > 0:
                min = ttl // 60
                sec = ttl % 60
                print(f"[{conversation_id}] 남은 시간: {min}분 {sec}초")
            elif ttl == -1:
                print(f"[{conversation_id}] 만료 시간이 설정되어 있지 않습니다.")
            else:
                print(f"[{conversation_id}] 대화 기록이 존재하지 않습니다.")
            return {
                "conversation_id": conversation_id,
                "response": ai_response,
                "article_context": article_context
            }
            
        except Exception as e:
            conversation_history.append({"role": "user", "content": message, "timestamp": datetime.now().isoformat()})
            conversation_history.append({"role": "assistant", "content": "죄송하지만 현재 OpenAI API 할당량이 초과되어 정확한 답변을 드릴 수 없습니다. API 키를 확인하거나 할당량을 늘려주세요.", "timestamp": datetime.now().isoformat()})
            
            self.save_conversation_history(conversation_id, conversation_history)
            ttl = self.redis_client.ttl(f"chat_history:{conversation_id}")
            if ttl > 0:
                min = ttl // 60
                sec = ttl % 60
                print(f"[{conversation_id}] 남은 시간: {min}분 {sec}초")
            elif ttl == -1:
                print(f"[{conversation_id}] 만료 시간이 설정되어 있지 않습니다.")
            else:
                print(f"[{conversation_id}] 대화 기록이 존재하지 않습니다.")

            return {
                "conversation_id": conversation_id,
                "response": "죄송하지만 현재 OpenAI API 할당량이 초과되어 정확한 답변을 드릴 수 없습니다. API 키를 확인하거나 할당량을 늘려주세요.",
                "article_context": article_context,
            }
    
    def chat_general(self, message: str, conversation_id: str = None) -> Dict:
        """일반적인 뉴스 관련 질문에 답변합니다."""
        # 새로운 대화 ID 생성 (제공되지 않은 경우)
        if not conversation_id:
            conversation_id = self.create_conversation_id()
        
        conversation_history = self.get_conversation_history(conversation_id)
        
        general_system_prompt = """당신은 뉴스에 대한 일반적인 질문에 답변하는 AI 어시스턴트입니다.
        한국어로 답변하고, 이전 대화 내용을 참고하여 연속적인 대화를 유지하세요."""
        
        messages = [SystemMessage(content=general_system_prompt)]
        
        for msg in conversation_history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))

        messages.append(HumanMessage(content=message))
        
        try:
            response = self.llm.invoke(messages)
            ai_response = response.content
            
            conversation_history.append({"role": "user", "content": message, "timestamp": datetime.now().isoformat()})
            conversation_history.append({"role": "assistant", "content": ai_response, "timestamp": datetime.now().isoformat()})
            
            self.save_conversation_history(conversation_id, conversation_history)

            ttl = self.redis_client.ttl(f"chat_history:{conversation_id}")
            if ttl > 0:
                min = ttl // 60
                sec = ttl % 60
                print(f"[{conversation_id}] 남은 시간: {min}분 {sec}초")
            elif ttl == -1:
                print(f"[{conversation_id}] 만료 시간이 설정되어 있지 않습니다.")
            else:
                print(f"[{conversation_id}] 대화 기록이 존재하지 않습니다.")

            return {
                "conversation_id": conversation_id,
                "response": ai_response
            }
            
        except Exception as e:
            conversation_history.append({"role": "user", "content": message, "timestamp": datetime.now().isoformat()})
            conversation_history.append({"role": "assistant", "content": "죄송하지만 현재 OpenAI API 할당량이 초과되어 정확한 답변을 드릴 수 없습니다. API 키를 확인하거나 할당량을 늘려주세요.", "timestamp": datetime.now().isoformat()})
            
            self.save_conversation_history(conversation_id, conversation_history)
            
            return {
                "conversation_id": conversation_id,
                "response": "죄송하지만 현재 OpenAI API 할당량이 초과되어 정확한 답변을 드릴 수 없습니다. API 키를 확인하거나 할당량을 늘려주세요."
            }
        
    def get_conversation_info(self, conversation_id: str) -> dict:
        """대화 정보를 조회합니다."""
        try:
            history = self.get_conversation_history(conversation_id)
            if history:
                ttl = self.redis_client.ttl(f"chat_history:{conversation_id}")
                return {
                "conversation_id": conversation_id,
                "message_count": len(history),
                "expires_in_seconds": ttl if ttl > 0 else 0,
                "last_message": history[-1] if history else None
            }
            return None
        except Exception as e:
            print(f"대화 정보 조회 오류: {e}")
            return None