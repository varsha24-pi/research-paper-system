import re
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc

from backend.database.models import Paper, PaperSection, PaperKeyword, SearchLog

# Scoring weights across different document fields
WEIGHT_TITLE = 4.0       # Direct match in title carries the highest relevance
WEIGHT_KEYWORDS = 3.0    # Match in NLP-extracted top keywords
WEIGHT_ABSTRACT = 2.0    # Match in abstract summary
WEIGHT_SECTION = 1.0     # Match in section content

# Basic English stopwords to filter from search queries
QUERY_STOP_WORDS = {
    "a", "an", "the", "in", "on", "at", "to", "for", "of", "with", "by",
    "from", "about", "into", "through", "during", "before", "after",
    "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
    "do", "does", "did", "and", "or", "but", "if", "then", "this", "that"
}


def tokenize_query(query: str) -> List[str]:
    """
    Cleans and tokenizes a user's search query into distinct terms,
    filtering out punctuation and common stop words.
    """
    if not query:
        return []

    # Extract alphanumeric words (at least 2 characters)
    tokens = re.findall(r"\b[a-zA-Z0-9_-]{2,}\b", query.lower())
    clean_tokens = [t for t in tokens if t not in QUERY_STOP_WORDS]
    
    # If all tokens were stopwords (e.g. query was 'the of'), keep original tokens
    return clean_tokens or tokens


def extract_context_snippet(text: str, query_tokens: List[str], window_chars: int = 200) -> str:
    """
    Extracts a concise snippet surrounding the first matching query term,
    avoiding returning the entire document text.
    """
    if not text:
        return ""

    text_lower = text.lower()
    first_match_pos = -1

    # Find position of earliest occurring query token
    for token in query_tokens:
        pos = text_lower.find(token)
        if pos != -1 and (first_match_pos == -1 or pos < first_match_pos):
            first_match_pos = pos

    # If no token matched inside this specific text block, return first 150 chars
    if first_match_pos == -1:
        snippet = text[:window_chars].strip()
        return f"{snippet}..." if len(text) > window_chars else snippet

    # Calculate window start and end around match
    half_window = window_chars // 2
    start = max(0, first_match_pos - half_window)
    end = min(len(text), first_match_pos + half_window)

    snippet = text[start:end].strip()

    # Add ellipses if text was truncated
    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(text) else ""

    return f"{prefix}{snippet}{suffix}"


def search_papers(
    query: str,
    db: Session,
    user_id: Optional[int] = None,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Executes a multi-field weighted keyword search across stored papers.

    Parameters:
        query (str): The search phrase entered by the user.
        db (Session): Active SQLAlchemy database session.
        user_id (Optional[int]): Optional user ID for logging search queries.
        limit (int): Maximum number of ranked results to return.

    Returns:
        Dict[str, Any]: Search summary, total results count, and ranked papers list.
    """
    query_str = query.strip() if query else ""
    tokens = tokenize_query(query_str)

    if not tokens:
        return {
            "status": "success",
            "query": query_str,
            "total_results": 0,
            "results": [],
            "message": "Empty or stop-word only search query."
        }

    # 1. Fetch candidate papers that match ANY token in title, abstract, sections, or keywords
    title_filters = [Paper.title.ilike(f"%{t}%") for t in tokens]
    abstract_filters = [Paper.abstract.ilike(f"%{t}%") for t in tokens]

    candidate_papers = db.query(Paper).filter(
        or_(*title_filters, *abstract_filters)
    ).all()

    # Also search by section contents
    section_filters = [PaperSection.content.ilike(f"%{t}%") for t in tokens]
    matching_sections = db.query(PaperSection).filter(or_(*section_filters)).all()

    # Also search by extracted keywords
    keyword_filters = [PaperKeyword.keyword.ilike(f"%{t}%") for t in tokens]
    matching_keywords = db.query(PaperKeyword).filter(or_(*keyword_filters)).all()

    # Group all matched paper IDs
    all_paper_ids = set([p.id for p in candidate_papers])
    for sec in matching_sections:
        all_paper_ids.add(sec.paper_id)
    for kw in matching_keywords:
        all_paper_ids.add(kw.paper_id)

    if not all_paper_ids:
        # Log empty search
        log_entry = SearchLog(
            user_id=user_id,
            query_text=query_str,
            search_type="keyword",
            results_count=0
        )
        db.add(log_entry)
        db.commit()

        return {
            "status": "success",
            "query": query_str,
            "total_results": 0,
            "results": [],
            "message": f"No research papers found matching '{query_str}'."
        }

    # 2. Retrieve complete paper records for scoring
    papers = db.query(Paper).filter(Paper.id.in_(all_paper_ids)).all()

    # 3. Calculate Multi-Field Weighted Relevance Score for each paper
    scored_results: List[Dict[str, Any]] = []

    for paper in papers:
        score = 0.0
        title_lower = paper.title.lower() if paper.title else ""
        abstract_lower = paper.abstract.lower() if paper.abstract else ""

        best_snippet = ""
        snippet_found = False

        # --- A. Score Title Matches ---
        for token in tokens:
            if token in title_lower:
                # Count frequency in title
                freq = title_lower.count(token)
                score += freq * WEIGHT_TITLE

        # --- B. Score Keyword Matches ---
        for kw in paper.keywords:
            kw_lower = kw.keyword.lower()
            for token in tokens:
                if token in kw_lower:
                    score += kw.relevance_score * WEIGHT_KEYWORDS

        # --- C. Score Abstract Matches ---
        if abstract_lower:
            for token in tokens:
                if token in abstract_lower:
                    freq = abstract_lower.count(token)
                    score += freq * WEIGHT_ABSTRACT
                    if not snippet_found:
                        best_snippet = extract_context_snippet(paper.abstract, tokens)
                        snippet_found = True

        # --- D. Score Section Content Matches ---
        for sec in paper.sections:
            sec_lower = sec.content.lower()
            for token in tokens:
                if token in sec_lower:
                    freq = sec_lower.count(token)
                    score += freq * WEIGHT_SECTION
                    if not snippet_found:
                        best_snippet = extract_context_snippet(sec.content, tokens)
                        snippet_found = True

        # Fallback snippet if none generated
        if not best_snippet:
            best_snippet = extract_context_snippet(paper.abstract or paper.title, tokens)

        # Matched keywords for UI tag rendering
        matched_tags = [
            kw.keyword for kw in paper.keywords
            if any(t in kw.keyword.lower() for t in tokens)
        ]

        scored_results.append({
            "document_id": paper.id,
            "title": paper.title,
            "authors": paper.authors,
            "publication_year": paper.publication_year,
            "score": round(score, 2),
            "snippet": best_snippet,
            "matched_keywords": matched_tags,
            "total_pages": paper.total_pages,
            "uploaded_at": paper.uploaded_at.isoformat()
        })

    # 4. Rank results by score descending
    ranked_results = sorted(scored_results, key=lambda x: x["score"], reverse=True)[:limit]

    # 5. Log search query to database for analytics
    try:
        log_entry = SearchLog(
            user_id=user_id,
            query_text=query_str,
            search_type="keyword",
            results_count=len(ranked_results)
        )
        db.add(log_entry)
        db.commit()
    except Exception:
        db.rollback()

    return {
        "status": "success",
        "query": query_str,
        "query_tokens": tokens,
        "total_results": len(ranked_results),
        "results": ranked_results
    }
