from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.schemas import ChatRequest, ChatResponse
from app.models.user import User
from app.rag.chain import answer_question

router = APIRouter()


@router.post("/", response_model=ChatResponse)
async def chat(
    req: ChatRequest,
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    answer, sources = await answer_question(db, req.question)
    return ChatResponse(answer=answer, sources=sources)
