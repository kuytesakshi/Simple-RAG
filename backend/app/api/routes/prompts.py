"""Prompt library admin endpoints. All routes require is_admin."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import require_admin
from app.models.prompt_library import Prompt, PromptVersion
from app.models.schemas import PromptOut, PromptUpdate, PromptVersionOut
from app.models.user import User
from app.rag import prompts as prompt_service

router = APIRouter()


@router.get("/", response_model=list[PromptOut])
async def list_prompts(
    current: User = Depends(require_admin), db: AsyncSession = Depends(get_db)
):
    rows = (await db.execute(select(Prompt).order_by(Prompt.name))).scalars().all()
    out: list[PromptOut] = []
    for p in rows:
        versions = (
            await db.execute(
                select(PromptVersion)
                .where(PromptVersion.prompt_id == p.id)
                .order_by(PromptVersion.version.asc())
            )
        ).scalars().all()
        out.append(
            PromptOut(
                name=p.name, active_version=p.active_version, updated_at=p.updated_at,
                versions=[
                    PromptVersionOut(
                        version=v.version, content=v.content,
                        note=v.note, created_at=v.created_at,
                    )
                    for v in versions
                ],
            )
        )
    return out


@router.post("/reload")
async def reload_prompts(
    current: User = Depends(require_admin), db: AsyncSession = Depends(get_db)
):
    count = await prompt_service.refresh_prompts(db)
    return {"reloaded": count}


@router.post("/{name}", response_model=PromptVersionOut | dict)
async def update_prompt(
    name: str,
    body: PromptUpdate,
    current: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """New version only when content differs; identical resubmit is a no-op."""
    try:
        row = await prompt_service.set_prompt(db, name, body.content, body.note)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    if row is None:
        return {"unchanged": True, "detail": "Content identical to active version"}
    return PromptVersionOut(
        version=row.version, content=row.content, note=row.note, created_at=row.created_at
    )


@router.post("/{name}/rollback/{version}", response_model=PromptVersionOut)
async def rollback_prompt(
    name: str,
    version: int,
    current: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    try:
        row = await prompt_service.rollback_prompt(db, name, version)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return PromptVersionOut(
        version=row.version, content=row.content, note=row.note, created_at=row.created_at
    )
