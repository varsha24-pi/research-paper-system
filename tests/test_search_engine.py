import sys
import os

# Add project root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from backend.main import app
from backend.database.connection import SessionLocal, engine, Base
from backend.database.models import User, Paper, PaperSection, PaperKeyword
from backend.services.search_engine import search_papers_tfidf

client = TestClient(app)


def seed_corpus_data():
    """Seeds test research papers for TF-IDF Vector Space Model testing."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        user = db.query(User).filter(User.username == "tfidf_tester").first()
        if not user:
            user = User(
                username="tfidf_tester",
                email="tfidf_tester@example.com",
                password_hash="testpass",
                full_name="TF-IDF Tester"
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        # Paper 1: Transformer & Attention
        p1 = db.query(Paper).filter(Paper.title == "Attention Mechanisms in Deep Learning").first()
        if not p1:
            p1 = Paper(
                user_id=user.id,
                title="Attention Mechanisms in Deep Learning",
                authors="Vaswani, Devlin",
                publication_year=2023,
                file_name="attention_paper.pdf",
                file_path="uploads/attention_paper.pdf",
                file_size_bytes=204800,
                total_pages=8,
                abstract="This paper surveys attention mechanisms and self-attention in modern transformers.",
                processing_status="completed"
            )
            db.add(p1)
            db.flush()

            db.add(PaperSection(
                paper_id=p1.id,
                section_name="Methodology",
                section_order=1,
                content="Self-attention allows models to weigh the significance of different tokens dynamically."
            ))
            db.add(PaperKeyword(paper_id=p1.id, keyword="transformer", relevance_score=0.95))
            db.add(PaperKeyword(paper_id=p1.id, keyword="attention", relevance_score=0.90))

        # Paper 2: Computer Vision / CNNs
        p2 = db.query(Paper).filter(Paper.title == "Convolutional Neural Networks for Image Recognition").first()
        if not p2:
            p2 = Paper(
                user_id=user.id,
                title="Convolutional Neural Networks for Image Recognition",
                authors="LeCun, He",
                publication_year=2022,
                file_name="cnn_paper.pdf",
                file_path="uploads/cnn_paper.pdf",
                file_size_bytes=180000,
                total_pages=6,
                abstract="A detailed study of convolutional layers and residual connections in computer vision.",
                processing_status="completed"
            )
            db.add(p2)
            db.flush()

            db.add(PaperSection(
                paper_id=p2.id,
                section_name="Methodology",
                section_order=1,
                content="Deep convolutional residual networks address vanishing gradients in visual classification."
            ))
            db.add(PaperKeyword(paper_id=p2.id, keyword="convolutional", relevance_score=0.92))
            db.add(PaperKeyword(paper_id=p2.id, keyword="computer vision", relevance_score=0.85))

        db.commit()

    finally:
        db.close()


def run_tfidf_search_tests():
    print("=" * 65)
    print(" Running TF-IDF + Cosine Similarity Retrieval Tests")
    print("=" * 65)

    seed_corpus_data()
    db = SessionLocal()

    try:
        # Test 1: Query for 'attention transformer'
        res1 = search_papers_tfidf("attention transformer", db)
        assert res1["status"] == "success"
        assert res1["retrieval_model"] == "TF-IDF + Cosine Similarity"
        assert res1["total_results"] >= 1
        top_doc = res1["results"][0]
        assert "Attention" in top_doc["title"] or "Transformer" in top_doc["title"]
        assert 0.0 < top_doc["score"] <= 1.0, f"Expected 0 < score <= 1, got {top_doc['score']}"
        print(f"[PASS] Query 'attention transformer' -> Top Match: '{top_doc['title']}'")
        print(f"       Cosine Similarity Score: {top_doc['score']} ({top_doc['relevance_percentage']})")
        print(f"       Snippet: \"{top_doc['snippet']}\"")

        # Test 2: Query for 'convolutional image'
        res2 = search_papers_tfidf("convolutional image", db)
        assert res2["total_results"] >= 1
        top_cnn = res2["results"][0]
        assert "Convolutional" in top_cnn["title"]
        print(f"[PASS] Query 'convolutional image' -> Top Match: '{top_cnn['title']}'")
        print(f"       Cosine Similarity Score: {top_cnn['score']} ({top_cnn['relevance_percentage']})")

        # Test 3: Query with zero matches
        res3 = search_papers_tfidf("quantum astrophysics plasma", db)
        assert res3["total_results"] == 0
        assert len(res3["results"]) == 0
        print(f"[PASS] Zero-result query handled gracefully: \"{res3['message']}\"")

        # Test 4: Verify REST API GET /search/?q=attention
        api_res = client.get("/search/?q=attention")
        assert api_res.status_code == 200
        assert api_res.json()["total_results"] >= 1
        print(f"[PASS] REST API GET /search/?q=attention verified via TestClient.")

        print("=" * 65)
        print("[OK] All TF-IDF & Cosine Similarity Tests Passed Successfully!")
        print("=" * 65)

    finally:
        db.close()


if __name__ == "__main__":
    run_tfidf_search_tests()
