from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    BigInteger,
    String,
    Text,
    Float,
    DateTime,
    ForeignKey,
    Enum,
    Index
)
from sqlalchemy.orm import relationship
from backend.database.connection import Base


class User(Base):
    """
    Represents registered users in the system.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    papers = relationship("Paper", back_populates="user", cascade="all, delete-orphan")
    search_logs = relationship("SearchLog", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"


class Paper(Base):
    """
    Represents an uploaded research paper document and its core metadata.
    """
    __tablename__ = "papers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(500), nullable=False, index=True)
    authors = Column(String(500), nullable=True)
    publication_year = Column(Integer, nullable=True)
    journal_conference = Column(String(255), nullable=True)
    doi = Column(String(100), nullable=True)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size_bytes = Column(BigInteger, nullable=False)
    total_pages = Column(Integer, default=0, nullable=False)
    abstract = Column(Text, nullable=True)
    processing_status = Column(
        Enum("uploaded", "processing", "completed", "failed", name="paper_processing_status"),
        default="uploaded",
        nullable=False
    )
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="papers")
    sections = relationship("PaperSection", back_populates="paper", cascade="all, delete-orphan")
    keywords = relationship("PaperKeyword", back_populates="paper", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Paper(id={self.id}, title='{self.title[:30]}...')>"


class PaperSection(Base):
    """
    Stores extracted text split by logical section or page.
    """
    __tablename__ = "paper_sections"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    paper_id = Column(Integer, ForeignKey("papers.id", ondelete="CASCADE"), nullable=False, index=True)
    section_name = Column(String(100), nullable=False)  # e.g., 'Abstract', 'Introduction', 'Methodology'
    section_order = Column(Integer, default=1, nullable=False)
    page_number = Column(Integer, nullable=True)
    content = Column(Text, nullable=False)  # Extracted text content for this section

    # Relationship
    paper = relationship("Paper", back_populates="sections")

    def __repr__(self):
        return f"<PaperSection(id={self.id}, paper_id={self.paper_id}, section='{self.section_name}')>"


class PaperKeyword(Base):
    """
    Stores keywords extracted by NLP algorithms with relevance scores.
    """
    __tablename__ = "paper_keywords"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    paper_id = Column(Integer, ForeignKey("papers.id", ondelete="CASCADE"), nullable=False, index=True)
    keyword = Column(String(100), nullable=False, index=True)
    relevance_score = Column(Float, default=1.0, nullable=False)

    # Relationship
    paper = relationship("Paper", back_populates="keywords")

    def __repr__(self):
        return f"<PaperKeyword(keyword='{self.keyword}', score={self.relevance_score})>"


class SearchLog(Base):
    """
    Tracks search queries executed across the system.
    """
    __tablename__ = "search_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    query_text = Column(String(255), nullable=False)
    search_type = Column(String(50), default="keyword", nullable=False)  # 'keyword', 'title', 'fulltext'
    results_count = Column(Integer, default=0, nullable=False)
    searched_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship
    user = relationship("User", back_populates="search_logs")

    def __repr__(self):
        return f"<SearchLog(query='{self.query_text}', count={self.results_count})>"
