from fastapi import APIRouter, Depends
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter()


@router.post("/run")
def run_ingest(current: User = Depends(get_current_user)):
    # TODO: call scripts/ingest_data.py logic: load Data/*.pdf -> chunk -> embed -> pgvector
    return {"msg": "ingest placeholder - reads from DATA_DIR"}
