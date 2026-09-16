from typing import Optional, List
from pydantic import BaseModel, Field
from fastapi import APIRouter, Query, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.database.connection import get_db
from backend.database.models import SearchLog
from backend.services.search_engine import search_papers

router = APIRouter(prefix="/search", tags=["Search & Retrieval"])


# -----------------------------------------------------------------------------
# Pydantic Schemas for Swagger / OpenAPI Documentation
# -----------------------------------------------------------------------------
class SearchResultItem(BaseModel):
    document_id: int = Field(..., description="Unique ID of the research paper")
    title: str = Field(..., description="Title of the research paper")
    authors: Optional[str] = Field(None, description="Paper authors")
    publication_year: Optional[int] = Field(None, description="Year of publication")
    score: float = Field(..., description="Weighted relevance score calculated by the search engine")
    relevance_percentage: Optional[str] = Field(None, description="Human readable percentage format")
    snippet: str = Field(..., description="Short context snippet containing matching terms")
    matched_keywords: List[str] = Field(default=[], description="Keywords matching the search query")
    total_pages: int = Field(..., description="Total pages in the PDF document")
    uploaded_at: str = Field(..., description="ISO 8601 timestamp of upload")


class SearchResponse(BaseModel):
    status: str = Field("success", description="Status of the search request")
    query: str = Field(..., description="Original user search query")
    query_tokens: List[str] = Field(default=[], description="Processed search tokens after stopword filtering")
    total_results: int = Field(..., description="Number of matching papers found")
    results: List[SearchResultItem] = Field(default=[], description="List of matching papers ranked by relevance")
    message: Optional[str] = Field(None, description="Optional informational message (e.g. for empty results)")


# -----------------------------------------------------------------------------
# Search Endpoints
# -----------------------------------------------------------------------------
@router.get(
    "",
    response_model=SearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Search Research Papers",
    description="Searches indexed research papers using multi-field weighted relevance scoring across title, abstract, sections, and NLP keywords."
)
@router.get(
    "/",
    response_model=SearchResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False  # Avoid duplicating in Swagger UI docs
)
def search_documents(
    q: Optional[str] = Query(
        None,
        description="Search phrase or keywords (e.g., 'attention mechanism', 'neural networks')",
        min_length=1,
        max_length=200
    ),
    query: Optional[str] = Query(
        None,
        description="Alternative parameter name for search query",
        min_length=1,
        max_length=200
    ),
    limit: int = Query(
        10,
        ge=1,
        le=50,
        description="Maximum number of ranked results to return (1-50)"
    ),
    user_id: Optional[int] = Query(
        None,
        description="Optional user ID for tracking search query history"
    ),
    db: Session = Depends(get_db)
):
    """
    Search Endpoint:
    - Validates query input (non-empty, non-whitespace).
    - Executes multi-field weighted search in `services/search_engine.py`.
    - Returns ranked results with relevance scores, short snippets, and metadata.
    """
    # 1. Resolve search query parameter (support either `q` or `query`)
    search_term = (q or query or "").strip()

    # 2. Validate query input
    if not search_term:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query cannot be empty or whitespace only. Please provide a valid 'q' or 'query' parameter."
        )

    # 3. Execute search via search_engine service
    try:
        results = search_papers(
            query=search_term,
            db=db,
            user_id=user_id,
            limit=limit
        )
        return results

    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while executing search: {str(err)}"
        )


@router.get(
    "/history",
    status_code=status.HTTP_200_OK,
    summary="Search Query History",
    description="Retrieves the most recent search queries logged in the MySQL database."
)
def get_search_history(
    limit: int = Query(10, ge=1, le=50, description="Max history logs to return"),
    db: Session = Depends(get_db)
):
    """
    Returns search query logs from the `search_logs` table.
    """
    try:
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
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch search history: {str(err)}"
        )
