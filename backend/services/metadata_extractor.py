import re
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pathlib import Path

# Headers or banners commonly appearing at the top of academic preprints / journals to ignore for title detection
HEADER_IGNORE_PATTERNS = [
    r"(?i)^arxiv:\d+\.\d+",
    r"(?i)^ieee\s+transactions",
    r"(?i)^proceedings\s+of",
    r"(?i)^journal\s+of",
    r"(?i)^springer",
    r"(?i)^elsevier",
    r"(?i)^acm\s+conference",
    r"(?i)^preprint\.?\s*under\s+review",
    r"(?i)^published\s+as\s+a\s+conference\s+paper",
    r"(?i)^volume\s+\d+",
    r"(?i)^issn:\s*[\d-]+",
    r"(?i)^doi:\s*10\.\d+"
]

# Patterns representing affiliation/institution noise in author blocks
AFFILIATION_PATTERNS = [
    r"(?i)department\s+of",
    r"(?i)school\s+of",
    r"(?i)faculty\s+of",
    r"(?i)university",
    r"(?i)institute",
    r"(?i)laboratory",
    r"(?i)corporation",
    r"(?i)center\s+for",
    r"(?i)research\s+lab",
    r"(?i)college",
    r"(?i)[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",  # Email addresses
    r"(?i)\b(?:usa|uk|canada|china|india|germany|france|japan)\b"
]


class MetadataExtractor:
    """
    Dedicated service for heuristic-based extraction of research paper metadata:
    - Title
    - Authors
    - Abstract
    - Publication Year
    - Explicit Keywords
    - Structural Sections
    """

    @staticmethod
    def extract_title(full_text: str, page1_text: str, pdf_metadata: Dict[str, Any], filename: str) -> str:
        """
        Attempts to extract paper title using a hierarchy of heuristics:
        1. PDF internal metadata (if valid and not a default placeholder like 'untitled').
        2. First prominent text block on Page 1 before authors/Abstract.
        3. Fallback to clean filename.
        """
        # 1. Check embedded PDF metadata title
        meta_title = (pdf_metadata.get("title") or "").strip()
        if meta_title and len(meta_title) > 5 and not any(meta_title.lower().startswith(x) for x in ["untitled", "microsoft word", "latex", "document"]):
            return meta_title

        # 2. Parse Page 1 lines
        if page1_text:
            lines = [line.strip() for line in page1_text.split("\n") if line.strip()]
            candidate_lines = []

            for line in lines[:10]:
                # Skip header/journal banners
                if any(re.search(pat, line) for pat in HEADER_IGNORE_PATTERNS):
                    continue

                # Stop if we hit Abstract, Introduction, Email, or Affiliation
                if re.search(r"(?i)\b(abstract|introduction|email|department|university)\b", line):
                    break

                # Stop if line looks like author list (e.g. contains 'and' or multiple commas)
                if len(candidate_lines) >= 1 and ("," in line or " and " in line.lower() or "@" in line):
                    break

                candidate_lines.append(line)
                if len(candidate_lines) >= 2:
                    break

            if candidate_lines:
                title_candidate = " ".join(candidate_lines).strip()
                title_candidate = re.sub(r"\s+", " ", title_candidate)
                if 10 <= len(title_candidate) <= 250:
                    return title_candidate

        # 3. Fallback: Clean filename
        clean_fallback = Path(filename).stem.replace("_", " ").replace("-", " ").title()
        return clean_fallback or "Untitled Research Paper"

    @staticmethod
    def extract_authors(page1_text: str, pdf_metadata: Dict[str, Any]) -> Optional[str]:
        """
        Extracts author names from embedded metadata or Page 1 block between title and Abstract.
        """
        # 1. Check embedded metadata
        meta_author = (pdf_metadata.get("author") or "").strip()
        if meta_author and len(meta_author) > 2 and not any(meta_author.lower().startswith(x) for x in ["user", "author", "admin", "administrator"]):
            return meta_author

        # 2. Heuristic extraction from Page 1
        if not page1_text:
            return None

        # Look for text before 'Abstract'
        abstract_idx = re.search(r"(?i)\babstract\b", page1_text)
        header_portion = page1_text[:abstract_idx.start()] if abstract_idx else page1_text[:1000]

        lines = [line.strip() for line in header_portion.split("\n") if line.strip()]
        author_lines = []

        # Find lines after Title that look like author names
        for line in lines[1:8]:
            if any(re.search(pat, line) for pat in HEADER_IGNORE_PATTERNS):
                continue
            if any(re.search(pat, line) for pat in AFFILIATION_PATTERNS):
                continue
            # Authors line typically has commas or 'and' (e.g., "Kaiming He, Xiangyu Zhang, Shaoqing Ren")
            if ("," in line or " and " in line.lower()) and len(line) < 150:
                author_lines.append(line)
                break

        if author_lines:
            authors_str = ", ".join(author_lines)
            authors_str = re.sub(r"[\d\*\†\‡\§]+", "", authors_str)
            authors_str = re.sub(r"\s{2,}", " ", authors_str).strip()
            if 3 <= len(authors_str) <= 300:
                return authors_str

        return None


    @staticmethod
    def extract_abstract(full_text: str) -> Optional[str]:
        """
        Extracts the Abstract summary using boundary matching.
        """
        if not full_text:
            return None

        match = re.search(
            r"(?i)\babstract\b[:\s\-—]*(.+?)(?=\b(?:\d+\.?\s*)?introduction\b|\n\n\s*[1-9]\b|$)",
            full_text,
            re.DOTALL
        )
        if match:
            abstract_candidate = match.group(1).strip()
            # Clean inner line breaks and spaces
            abstract_clean = re.sub(r"\s+", " ", abstract_candidate)
            if 30 <= len(abstract_clean) <= 3500:
                return abstract_clean

        # Fallback: Check first paragraph
        paragraphs = [p.strip() for p in full_text.split("\n\n") if len(p.strip()) > 80]
        if paragraphs and "abstract" in paragraphs[0].lower()[:30]:
            return re.sub(r"\s+", " ", paragraphs[0])

        return None

    @staticmethod
    def extract_publication_year(full_text: str, pdf_metadata: Dict[str, Any]) -> Optional[int]:
        """
        Extracts publication year from embedded date or regex scanning for 4-digit years (1970 - 2026).
        """
        current_year = datetime.now(timezone.utc).year

        # 1. Check embedded creation date (e.g., 'D:20230515120000')
        creation_date = str(pdf_metadata.get("creation_date") or "")
        year_match = re.search(r"20\d{2}|19\d{2}", creation_date)
        if year_match:
            y = int(year_match.group(0))
            if 1970 <= y <= current_year + 1:
                return y

        # 2. Search Page 1 header/footer for copyright or publication years: e.g. "© 2023 IEEE", "arXiv:2305.18290"
        page1_sample = full_text[:2000]

        # Check for arXiv format: arXiv:2305.xxxx -> Year 2023
        arxiv_match = re.search(r"(?i)arxiv:(\d{2})\d{2}\.", page1_sample)
        if arxiv_match:
            yy = int(arxiv_match.group(1))
            return 2000 + yy if yy <= (current_year % 100) + 1 else 1900 + yy

        # Check for standard 4-digit year patterns
        explicit_year_match = re.search(r"(?i)(?:copyright|published|©|\bconf(?:erence)?\b|\bproceedings\b|\bjournal\b)[^\d\n]*\b(19\d{2}|20\d{2})\b", page1_sample)
        if explicit_year_match:
            y = int(explicit_year_match.group(1))
            if 1970 <= y <= current_year + 1:
                return y

        return None

    @staticmethod
    def extract_explicit_keywords(full_text: str) -> List[str]:
        """
        Extracts author-defined keywords (e.g., 'Index Terms—', 'Keywords:', 'Key words:').
        """
        if not full_text:
            return []

        match = re.search(
            r"(?i)\b(?:keywords|key\s+words|index\s+terms|terms)\b[:\s\-—]+([^\n\r]+(?:\n[^\n\r]+)?)",
            full_text[:3000]
        )
        if match:
            raw_keywords = match.group(1).strip()
            # Stop if another section header began
            raw_keywords = re.split(r"(?i)\b(?:1\.?\s*introduction|abstract|background)\b", raw_keywords)[0]

            # Split by comma, semicolon, or bullet
            items = re.split(r"[,;•\n—]", raw_keywords)
            clean_items = []
            for item in items:
                clean_kw = re.sub(r"[^\w\s-]", "", item).strip()
                if 2 <= len(clean_kw) <= 50 and not clean_kw.lower().startswith("introduction"):
                    clean_items.append(clean_kw)

            if clean_items:
                return clean_items[:10]

        return []

    @classmethod
    def extract_all_metadata(
        cls,
        extraction_data: Dict[str, Any],
        custom_title: Optional[str] = None,
        custom_authors: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Main entry point: Extracts all metadata attributes and returns a structured dictionary.
        """
        full_text = extraction_data.get("full_text", "")
        pages = extraction_data.get("pages", [])
        page1_text = pages[0].get("text", "") if pages else full_text[:2000]
        pdf_metadata = extraction_data.get("metadata", {})
        filename = extraction_data.get("file_name", "document.pdf")

        # 1. Resolve Title
        title = custom_title.strip() if custom_title and custom_title.strip() else cls.extract_title(
            full_text=full_text,
            page1_text=page1_text,
            pdf_metadata=pdf_metadata,
            filename=filename
        )

        # 2. Resolve Authors
        authors = custom_authors.strip() if custom_authors and custom_authors.strip() else cls.extract_authors(
            page1_text=page1_text,
            pdf_metadata=pdf_metadata
        )

        # 3. Extract Abstract
        abstract = cls.extract_abstract(full_text)

        # 4. Extract Publication Year
        publication_year = cls.extract_publication_year(full_text, pdf_metadata)

        # 5. Extract Explicit Keywords
        explicit_keywords = cls.extract_explicit_keywords(full_text)

        return {
            "title": title,
            "authors": authors,
            "abstract": abstract,
            "publication_year": publication_year,
            "explicit_keywords": explicit_keywords,
            "total_pages": extraction_data.get("total_pages", len(pages)),
            "total_words": extraction_data.get("total_words", 0),
            "extraction_confidence": {
                "title_detected": bool(title),
                "authors_detected": bool(authors),
                "abstract_detected": bool(abstract),
                "year_detected": bool(publication_year),
                "keywords_detected": bool(explicit_keywords)
            }
        }
