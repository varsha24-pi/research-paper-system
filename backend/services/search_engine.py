import re
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from backend.database.models import Paper, PaperSection, PaperKeyword, SearchLog

# Basic English stopwords to filter from search queries
QUERY_STOP_WORDS = {
    "a", "an", "the", "in", "on", "at", "to", "for", "of", "with", "by",
    "from", "about", "into", "through", "during", "before", "after",
    "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
    "do", "does", "did", "and", "or", "but", "if", "then", "this", "that"
}


def tokenize_query(query: str) -> List[str]:
    """
    Cleans and tokenizes a user search query, filtering out noise.
    """
    if not query:
        return []
    tokens = re.findall(r"\b[a-zA-Z0-9_-]{2,}\b", query.lower())
    clean_tokens = [t for t in tokens if t not in QUERY_STOP_WORDS]
    return clean_tokens or tokens


def extract_context_snippet(text: str, query_tokens: List[str], window_chars: int = 200) -> str:
    """
    Extracts a concise 200-character context window surrounding the matched query keywords.
    """
    if not text:
        return ""

    text_lower = text.lower()
    first_match_pos = -1

    for token in query_tokens:
        pos = text_lower.find(token)
        if pos != -1 and (first_match_pos == -1 or pos < first_match_pos):
            first_match_pos = pos

    if first_match_pos == -1:
        snippet = text[:window_chars].strip()
        return f"{snippet}..." if len(text) > window_chars else snippet

    half_window = window_chars // 2
    start = max(0, first_match_pos - half_window)
    end = min(len(text), first_match_pos + half_window)
    snippet = text[start:end].strip()

    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(text) else ""
    return f"{prefix}{snippet}{suffix}"


def build_paper_corpus_text(paper: Paper) -> str:
    """
    Builds a weighted composite text representation for a research paper:
    - Title repeated 3x (boosts title relevance)
    - Abstract repeated 2x (boosts abstract summary)
    - All extracted section texts
    - All extracted NLP keywords
    """
    title_part = f"{paper.title} " * 3 if paper.title else ""
    abstract_part = f"{paper.abstract} " * 2 if paper.abstract else ""
    sections_part = " ".join(s.content for s in paper.sections if s.content)
    keywords_part = " ".join(k.keyword for k in paper.keywords if k.keyword)

    return f"{title_part} {abstract_part} {keywords_part} {sections_part}".strip()


def search_papers_tfidf(
    query: str,
    db: Session,
    user_id: Optional[int] = None,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Intelligent Vector Space Information Retrieval using TF-IDF and Cosine Similarity.

    Pipeline:
    1. Fetch all indexed research papers from MySQL.
    2. Build full document corpus and fit TF-IDF Vectorizer.
    3. Transform query into query vector.
    4. Compute Cosine Similarity between query vector and all document vectors.
    5. Rank papers by cosine similarity score descending.
    6. Extract contextual snippets and return top-k results.
    """
    query_str = query.strip() if query else ""
    tokens = tokenize_query(query_str)

    if not tokens:
        return {
            "status": "success",
            "query": query_str,
            "query_tokens": [],
            "retrieval_model": "TF-IDF + Cosine Similarity",
            "total_results": 0,
            "results": [],
            "message": "Empty or stop-word only search query."
        }

    # 1. Fetch all completed research papers from database
    papers: List[Paper] = db.query(Paper).all()

    if not papers:
        return {
            "status": "success",
            "query": query_str,
            "query_tokens": tokens,
            "retrieval_model": "TF-IDF + Cosine Similarity",
            "total_results": 0,
            "results": [],
            "message": "No research papers have been uploaded yet."
        }

    # 2. Build Document Corpus
    corpus: List[str] = [build_paper_corpus_text(p) for p in papers]

    try:
        # 3. Fit TF-IDF Vectorizer across the document collection
        vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),       # Captures single words and 2-word phrases
            sublinear_tf=True,        # Uses 1 + log(tf) to dampen excessive repetition
            norm="l2"                 # Normalizes vectors to unit Euclidean length
        )

        # Document TF-IDF Matrix (Shape: N_documents x Vocabulary_Size)
        doc_tfidf_matrix = vectorizer.fit_transform(corpus)

        # 4. Transform Search Query into TF-IDF Query Vector (Shape: 1 x Vocabulary_Size)
        query_vector = vectorizer.transform([query_str])

        # 5. Compute Cosine Similarity: cos_sim(q, d) = (q . d) / (||q|| * ||d||)
        # Result shape: (1, N_documents)
        similarity_scores = cosine_similarity(query_vector, doc_tfidf_matrix)[0]

    except Exception:
        # Fallback if vocabulary is too sparse (single word doc)
        similarity_scores = np.zeros(len(papers))

    # 6. Collect and rank papers with non-zero similarity
    scored_results: List[Dict[str, Any]] = []

    for idx, paper in enumerate(papers):
        score = float(similarity_scores[idx])

        # If TF-IDF cosine score is > 0, paper is relevant
        # Also check fallback keyword substring if corpus was small
        if score <= 0.0:
            title_lower = (paper.title or "").lower()
            abstract_lower = (paper.abstract or "").lower()
            if any(t in title_lower or t in abstract_lower for t in tokens):
                score = 0.15

        if score > 0.0:
            # Find best contextual snippet (search abstract first, then sections)
            snippet = ""
            if paper.abstract and any(t in paper.abstract.lower() for t in tokens):
                snippet = extract_context_snippet(paper.abstract, tokens)
            else:
                for sec in paper.sections:
                    if any(t in sec.content.lower() for t in tokens):
                        snippet = extract_context_snippet(sec.content, tokens)
                        break

            if not snippet:
                snippet = extract_context_snippet(paper.abstract or paper.title, tokens)

            # Matched keyword tags
            matched_tags = [
                kw.keyword for kw in paper.keywords
                if any(t in kw.keyword.lower() for t in tokens)
            ]

            scored_results.append({
                "document_id": paper.id,
                "title": paper.title,
                "authors": paper.authors,
                "publication_year": paper.publication_year,
                "score": round(score, 4),                     # Raw Cosine Similarity (0.0000 - 1.0000)
                "relevance_percentage": f"{round(score * 100, 1)}%",
                "snippet": snippet,
                "matched_keywords": matched_tags,
                "total_pages": paper.total_pages,
                "uploaded_at": paper.uploaded_at.isoformat()
            })

    # 7. Sort papers by Cosine Similarity descending
    ranked_results = sorted(scored_results, key=lambda x: x["score"], reverse=True)[:limit]

    # 8. Log search query to database for analytics
    try:
        log_entry = SearchLog(
            user_id=user_id,
            query_text=query_str,
            search_type="tfidf_cosine",
            results_count=len(ranked_results)
        )
        db.add(log_entry)
        db.commit()
    except Exception:
        db.rollback()

    if not ranked_results:
        return {
            "status": "success",
            "query": query_str,
            "query_tokens": tokens,
            "retrieval_model": "TF-IDF + Cosine Similarity",
            "total_results": 0,
            "results": [],
            "message": f"No research papers found matching '{query_str}'."
        }

    return {
        "status": "success",
        "query": query_str,
        "query_tokens": tokens,
        "retrieval_model": "TF-IDF + Cosine Similarity",
        "total_results": len(ranked_results),
        "results": ranked_results
    }


# Backwards compatibility alias
search_papers = search_papers_tfidf
