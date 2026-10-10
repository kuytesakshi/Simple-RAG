from fastapi import APIRouter, Depends
from app.core.security import get_current_user
from app.models.schemas import ChatRequest, ChatResponse
from app.models.user import User

router = APIRouter()


@router.post("/", response_model=ChatResponse)
def chat(req: ChatRequest, current: User = Depends(get_current_user)):
    # TODO: 1) embed query 2) pgvector similarity search 3) Groq LLM answer
    return ChatResponse(answer="RAG placeholder - wire pgvector + Groq here", sources=[])
