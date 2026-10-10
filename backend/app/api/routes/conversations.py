"""Persisted chat history: conversations + messages, all scoped to the logged-in user."""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.conversation import Conversation, Message
from app.models.schemas import (
    AskRequest,
    AskResponse,
    ConversationCreate,
    ConversationDetail,
    ConversationOut,
    MessageOut,
)
from app.models.user import User
from app.rag.chain import answer_question

router = APIRouter()


async def _owned_conversation(
    conversation_id: UUID, current: User, db: AsyncSession
) -> Conversation:
    convo = (
        await db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == current.id,
            )
        )
    ).scalar_one_or_none()
    if convo is None:
        # 404 either way: never leak whether another user's id exists
        raise HTTPException(status_code=404, detail="Conversation not found")
    return convo


@router.get("/", response_model=list[ConversationOut])
async def list_conversations(
    current: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    rows = (
        await db.execute(
            select(Conversation)
            .where(Conversation.user_id == current.id)
            .order_by(Conversation.updated_at.desc())
        )
    ).scalars().all()
    return rows


@router.post("/", response_model=ConversationOut, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    body: ConversationCreate,
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    convo = Conversation(user_id=current.id, title=body.title or "New conversation")
    db.add(convo)
    await db.commit()
    await db.refresh(convo)
    return convo


@router.get("/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: UUID,
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    convo = await _owned_conversation(conversation_id, current, db)
    msgs = (
        await db.execute(
            select(Message)
            .where(Message.conversation_id == convo.id)
            .order_by(Message.created_at.asc())
        )
    ).scalars().all()
    return ConversationDetail(
        id=convo.id, title=convo.title,
        created_at=convo.created_at, updated_at=convo.updated_at,
        messages=[
            MessageOut(
                id=m.id, role=m.role, content=m.content,
                sources=m.sources or [], created_at=m.created_at,
            )
            for m in msgs
        ],
    )


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: UUID,
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    convo = await _owned_conversation(conversation_id, current, db)
    # Bulk deletes (async-safe: no relationship lazy-loads)
    await db.execute(delete(Message).where(Message.conversation_id == convo.id))
    await db.execute(delete(Conversation).where(Conversation.id == convo.id))
    await db.commit()


@router.post("/{conversation_id}/ask", response_model=AskResponse)
async def ask(
    conversation_id: UUID,
    body: AskRequest,
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Append user turn -> run RAG chain -> append bot turn. One call, full turn persisted."""
    from sqlalchemy import func as sa_func

    convo = await _owned_conversation(conversation_id, current, db)
    question = body.question.strip()
    db.add(Message(conversation_id=convo.id, role="user", content=question))
    await db.flush()
    answer, sources = await answer_question(db, question)
    db.add(Message(conversation_id=convo.id, role="bot", content=answer, sources=sources))
    # Retitle empty threads from the first question
    count = (
        await db.execute(
            select(sa_func.count())
            .select_from(Message)
            .where(Message.conversation_id == convo.id)
        )
    ).scalar_one()
    if count <= 2 and (not convo.title or convo.title == "New conversation"):
        convo.title = question[:117] + ("…" if len(question) > 117 else "")
    await db.commit()
    return AskResponse(conversation_id=convo.id, answer=answer, sources=sources)
