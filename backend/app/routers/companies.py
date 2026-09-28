from fastapi import APIRouter

from app.transcript_client import TranscriptClient

router = APIRouter(tags=["companies"])


@router.get("/companies/search")
async def search_companies(q: str):
    query = q.strip()
    if not query:
        return []
    client = TranscriptClient()
    return await client.search_companies(query)
