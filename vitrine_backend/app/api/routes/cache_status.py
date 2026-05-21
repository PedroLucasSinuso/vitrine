from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from app.api.deps import get_db
from app.domain.models.cache_status import CacheStatus
from app.limiter import limiter

router = APIRouter(prefix="/status", tags=["Status"])


@router.get("/")
@limiter.limit("10/minute")
def get_status(request: Request, db=Depends(get_db)):
    stmt = select(CacheStatus).order_by(CacheStatus.id.desc())
    result = db.execute(stmt).scalars().first()

    return {
        "last_updated": result.last_updated if result else None
    }