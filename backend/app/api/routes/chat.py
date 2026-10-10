from fastapi import APIRouter
from app.models.schemas import ChatRequest, ChatResponse

router = APIRouter()

@router.post("/", response_model=ChatResponse)
def chat(req: ChatRequest):
    # TODO: 1) embed query 2) pgvector similarity search 3) Groq LLM answer
    return ChatResponse(answer="RAG placeholder - wire pgvector + Groq here", sources=[])
