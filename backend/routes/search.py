from typing import Optional
from fastapi import APIRouter, Query, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.database.connection import get_db
from backend.database.models import SearchLog
from backend.services.search_engine import search_papers

router = APIRouter(prefix="/search", tags=["Search & Retrieval"])


@router.get("/", status_code=status.HTTP_200_OK)
def search_documents(
    q: str = Query(..., min_length=1, description="Keywords or search phrase"),
    limit: int = Query(10, ge=1, le=50, description="Max results to return"),
    user_id: Optional[int] = Query(None, description="Optional user ID for logging"),
    db: Session = Depends(get_db)
):
    """
    Search indexed research papers using multi-field weighted relevance scoring.
    
    Returns matching paper titles, IDs, relevance scores, and highlighted context snippets.
    """
    return search_papers(query=q, db=db, user_id=user_id, limit=limit)


@router.get("/history", status_code=status.HTTP_200_OK)
def get_search_history(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Retrieve recent search query logs and analytics.
    """
    logs = db.query(SearchLog).order_by(desc(SearchLog.searched_at)).limit(limit).all()
    return {
        "status": "success",
        "total_logs": len(logs),
        "history": [
            {
                "id": log.id,
                "query": log.query_text,
                "results_count": log.results_count,
                "searched_at": log.searched_at.isoformat()
            }
            for log in logs
        ]
    }
