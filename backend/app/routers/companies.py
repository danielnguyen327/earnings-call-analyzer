from fastapi import APIRouter

from app.company_directory import directory

router = APIRouter(tags=["companies"])


@router.get("/companies/search")
async def search_companies(q: str):
    return await directory.search(q)
