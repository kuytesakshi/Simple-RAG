from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[str] = []


# ---- Conversations ----

class ConversationCreate(BaseModel):
    title: str = Field(default="New conversation", max_length=120)


class ConversationOut(BaseModel):
    id: UUID
    title: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MessageOut(BaseModel):
    id: UUID
    role: str
    content: str
    sources: list[str] = []
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationDetail(ConversationOut):
    messages: list[MessageOut] = []


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)


class AskResponse(BaseModel):
    conversation_id: UUID
    answer: str
    sources: list[str] = []


# ---- Auth ----

class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=4, max_length=128)


class UserLogin(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: UUID
    username: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---- Prompt library (admin) ----

class PromptVersionOut(BaseModel):
    version: int
    content: str
    note: str | None = None
    created_at: datetime


class PromptOut(BaseModel):
    name: str
    active_version: int
    updated_at: datetime
    versions: list[PromptVersionOut] = []


class PromptUpdate(BaseModel):
    content: str = Field(min_length=1)
    note: str | None = Field(default=None, max_length=255)
