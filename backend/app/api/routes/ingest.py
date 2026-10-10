from fastapi import APIRouter

router = APIRouter()

@router.post("/run")
def run_ingest():
    # TODO: call scripts/ingest_data.py logic: load Data/*.pdf -> chunk -> embed -> pgvector
    return {"msg": "ingest placeholder - reads from DATA_DIR"}
