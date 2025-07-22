from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.chat_bot import NewsChatBot
from app.schemas.chat_bot import ChatMessage, ChatResponse, ConversationDeleteResponse

router = APIRouter(prefix="/chat", tags=["chat"])


chat_bot = NewsChatBot()

@router.post("/start", response_model=ChatResponse)
async def start_new_conversation(
    chat_message: ChatMessage,
    db: Session = Depends(get_db)
):
    try:
        if chat_message.article_id:
            article_context = chat_bot.get_article_context(db, chat_message.article_id)
            if not article_context:
                raise HTTPException(status_code=404, detail="기사를 찾을 수 없습니다.")
            
            result = chat_bot.chat_with_article(
                chat_message.message, 
                article_context, 
                None  
            )
            return ChatResponse(
                conversation_id=result["conversation_id"],
                response=result["response"],
                article_context=result["article_context"]
            )
        else:
            result = chat_bot.chat_general(
                chat_message.message, 
                None  
            )
            return ChatResponse(
                conversation_id=result["conversation_id"],
                response=result["response"]
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"챗봇 오류: {str(e)}")

@router.post("/message", response_model=ChatResponse)
async def send_message(
    chat_message: ChatMessage,
    db: Session = Depends(get_db)
):
    try:
        if not chat_message.conversation_id:
            raise HTTPException(
                status_code=400, 
                detail="conversation_id가 필요합니다. 새로운 대화를 시작하려면 /start 엔드포인트를 사용하세요"
            )
        
        conversation_info = chat_bot.get_conversation_info(chat_message.conversation_id)
        if not conversation_info:
            raise HTTPException(
                status_code=404, 
                detail="대화를 찾을 수 없습니다. 대화가 만료되었거나 존재하지 않습니다. /start 엔드포인트로 새로운 대화를 시작하세요"
            )
        
        if chat_message.article_id:
            article_context = chat_bot.get_article_context(db, chat_message.article_id)
            if not article_context:
                raise HTTPException(status_code=404, detail="기사를 찾을 수 없습니다")
            
            result = chat_bot.chat_with_article(
                chat_message.message, 
                article_context, 
                chat_message.conversation_id
            )
            return ChatResponse(
                conversation_id=result["conversation_id"],
                response=result["response"],
                article_context=result["article_context"]
            )
        else:
            result = chat_bot.chat_general(
                chat_message.message, 
                chat_message.conversation_id
            )
            return ChatResponse(
                conversation_id=result["conversation_id"],
                response=result["response"]
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"챗봇 오류: {str(e)}")