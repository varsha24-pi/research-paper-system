import re
from typing import Dict, Any, List, Optional
from sklearn.feature_extraction.text import TfidfVectorizer

# Common English and Academic Stop Words
ACADEMIC_STOP_WORDS = {
    "et", "al", "figure", "table", "paper", "section", "using", "used", "propose",
    "proposed", "based", "results", "shown", "shows", "show", "author", "authors",
    "university", "department", "conference", "journal", "proceedings", "volume",
    "pages", "page", "ieee", "acm", "springer", "elsevier", "doi", "http", "https",
    "www", "org", "com", "edu", "abstract", "introduction", "conclusion", "references"
}

# Standard academic section heading patterns
SECTION_PATTERNS = [
    (r"(?i)\babstract\b", "Abstract"),
    (r"(?i)\b(?:\d+\.?\s*)?introduction\b", "Introduction"),
    (r"(?i)\b(?:\d+\.?\s*)?(?:related\s+work|literature\s+review|background)\b", "Related Work"),
    (r"(?i)\b(?:\d+\.?\s*)?(?:methodology|proposed\s+method|proposed\s+model|method|system\s+model|architecture)\b", "Methodology"),
    (r"(?i)\b(?:\d+\.?\s*)?(?:experiments|experimental\s+results|results\s+and\s+discussion|results|evaluation)\b", "Results & Evaluation"),
    (r"(?i)\b(?:\d+\.?\s*)?(?:discussion)\b", "Discussion"),
    (r"(?i)\b(?:\d+\.?\s*)?(?:conclusion|conclusions|concluding\s+remarks)\b", "Conclusion"),
    (r"(?i)\b(?:\d+\.?\s*)?(?:references|bibliography)\b", "References"),
]


def clean_text_content(text: str) -> str:
    """
    Cleans raw text by removing extraneous line numbers, excessive whitespace,
    and standard noise characters while preserving sentence structure.
    """
    if not text:
        return ""

    # Remove inline line numbering artifacts (e.g., '12 ', '13 ') common in paper drafts
    text = re.sub(r"^\s*\d+\s+", "", text, flags=re.MULTILINE)

    # Normalize multiple whitespace and tabs to single space
    text = re.sub(r"[ \t]+", " ", text)

    # Normalize 3+ newlines to double newline (paragraphs)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def extract_abstract(full_text: str) -> Optional[str]:
    """
    Extracts the Abstract section from research paper text using regex boundaries.
    """
    if not full_text:
        return None

    # Pattern: Match from "Abstract" up to "1 Introduction" or "Introduction"
    match = re.search(
        r"(?i)\babstract\b[:\s]*(.+?)(?=\b(?:\d+\.?\s*)?introduction\b|\n\n\s*[1-9]\b|$)",
        full_text,
        re.DOTALL
    )
    if match:
        abstract_text = match.group(1).strip()
        # Ensure abstract has reasonable length (between 30 and 3000 chars)
        if 30 <= len(abstract_text) <= 3000:
            return clean_text_content(abstract_text)

    # Fallback: Check first paragraph if it looks like an abstract
    paragraphs = [p.strip() for p in full_text.split("\n\n") if len(p.strip()) > 100]
    if paragraphs:
        first_para = paragraphs[0]
        if "abstract" in first_para.lower()[:30]:
            return clean_text_content(first_para)

    return None


def segment_into_sections(full_text: str, pages: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
    """
    Segments the document into logical academic sections (Abstract, Intro, Method, etc.).
    Falls back to page-by-page chunking if explicit headings cannot be detected.
    """
    sections: List[Dict[str, Any]] = []

    if not full_text or not full_text.strip():
        return sections

    # 1. Try finding section heading split points in full text
    combined_pattern = r"(?m)^(?:\d+\.?\s*)?(" + "|".join([
        r"Abstract",
        r"Introduction",
        r"Related\s+Work",
        r"Literature\s+Review",
        r"Background",
        r"Methodology",
        r"Proposed\s+Method",
        r"Proposed\s+Model",
        r"System\s+Architecture",
        r"Experiments?",
        r"Results(?:\s+and\s+Discussion)?",
        r"Evaluation",
        r"Discussion",
        r"Conclusion(?:s)?",
        r"References"
    ]) + r")\b.*$"

    matches = list(re.finditer(combined_pattern, full_text, re.IGNORECASE))

    if matches and len(matches) >= 2:
        # Detected structured academic headings
        for i in range(len(matches)):
            heading = matches[i].group(0).strip()
            start_pos = matches[i].end()
            end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(full_text)

            content = full_text[start_pos:end_pos].strip()
            if content:
                sections.append({
                    "section_name": heading[:100],
                    "section_order": i + 1,
                    "page_number": None,
                    "content": clean_text_content(content)
                })

    # 2. Fallback: If headings weren't cleanly detected, segment by page
    if not sections and pages:
        order = 1
        for page in pages:
            page_text = page.get("text", "").strip()
            if page_text:
                sections.append({
                    "section_name": f"Page {page.get('page_number', order)}",
                    "section_order": order,
                    "page_number": page.get("page_number", order),
                    "content": clean_text_content(page_text)
                })
                order += 1

    # 3. Final Fallback: Single section with full text
    if not sections:
        sections.append({
            "section_name": "Full Document",
            "section_order": 1,
            "page_number": 1,
            "content": clean_text_content(full_text)
        })

    return sections


def extract_keywords(full_text: str, top_n: int = 10) -> List[Dict[str, Any]]:
    """
    Extracts top keywords and key phrases with relevance scores using TF-IDF.
    """
    if not full_text or len(full_text.strip()) < 50:
        return []

    try:
        # Combine English stopwords with domain academic stop words
        from sklearn.feature_extraction import text
        stop_words = list(text.ENGLISH_STOP_WORDS.union(ACADEMIC_STOP_WORDS))

        vectorizer = TfidfVectorizer(
            stop_words=stop_words,
            ngram_range=(1, 2),        # Extracts unigrams and bigrams (e.g. "transformer", "attention mechanism")
            max_df=0.90,               # Ignore terms appearing in >90% of documents
            min_df=1,
            token_pattern=r"(?u)\b[a-zA-Z][a-zA-Z0-9_-]{2,}\b"  # At least 3 chars
        )

        tfidf_matrix = vectorizer.fit_transform([full_text])
        feature_names = vectorizer.get_feature_names_out()
        scores = tfidf_matrix.toarray()[0]

        # Sort terms by TF-IDF weight descending
        ranked_indices = scores.argsort()[::-1]

        keywords: List[Dict[str, Any]] = []
        seen = set()

        for idx in ranked_indices:
            term = str(feature_names[idx]).strip()
            score = float(scores[idx])

            # Filter out single letters, digits, or duplicate substrings
            if len(term) < 3 or term in seen or term.isdigit():
                continue

            seen.add(term)
            keywords.append({
                "keyword": term,
                "relevance_score": round(score, 4)
            })

            if len(keywords) >= top_n:
                break

        return keywords

    except Exception:
        # Fallback to simple frequency extraction if vectorizer encounters edge case
        words = re.findall(r"\b[a-zA-Z]{4,}\b", full_text.lower())
        from collections import Counter
        counts = Counter(w for w in words if w not in ACADEMIC_STOP_WORDS)
        total = sum(counts.values()) or 1
        return [
            {"keyword": word, "relevance_score": round(count / total, 4)}
            for word, count in counts.most_common(top_n)
        ]


def process_extracted_document(extraction_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main orchestrator for text preprocessing:
    Takes output from pdf_extractor.py, cleans text, extracts abstract,
    segments sections, and extracts top keywords.
    """
    full_text = extraction_data.get("full_text", "")
    pages = extraction_data.get("pages", [])

    # 1. Clean full text
    cleaned_full_text = clean_text_content(full_text)

    # 2. Extract abstract
    abstract = extract_abstract(cleaned_full_text)

    # 3. Segment into sections
    sections = segment_into_sections(cleaned_full_text, pages)

    # 4. Extract top NLP keywords
    keywords = extract_keywords(cleaned_full_text, top_n=10)

    return {
        "status": "success",
        "abstract": abstract,
        "sections": sections,
        "keywords": keywords,
        "total_sections": len(sections),
        "total_keywords": len(keywords)
    }
