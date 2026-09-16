import sys
import os

# Add project root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from backend.main import app
from backend.database.connection import SessionLocal, engine, Base
from backend.database.models import User, Paper, PaperSection, PaperKeyword, SearchLog
from backend.services.search_engine import search_papers

client = TestClient(app)


def seed_test_search_data():
    """Seeds test research papers into MySQL for search testing."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        user = db.query(User).filter(User.username == "search_tester").first()
        if not user:
            user = User(
                username="search_tester",
                email="tester@example.com",
                password_hash="testpass",
                full_name="Search Tester"
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        # Paper 1: Deep Learning / Transformers
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
            db.add(PaperKeyword(paper_id=p1.id, keyword="neural network", relevance_score=0.80))

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


def run_search_tests():
    print("=" * 65)
    print(" Running Search Engine Service Tests")
    print("=" * 65)

    seed_test_search_data()
    db = SessionLocal()

    try:
        # Test 1: Search for 'transformer attention'
        res1 = search_papers("transformer attention", db)
        assert res1["status"] == "success"
        assert res1["total_results"] >= 1
        top_match = res1["results"][0]
        assert "Attention" in top_match["title"]
        assert top_match["score"] > 0
        assert len(top_match["snippet"]) > 0
        assert "..." in top_match["snippet"] or len(top_match["snippet"]) < 200
        print(f"[PASS] Matched query 'transformer attention' -> Top Paper: '{top_match['title']}' (Score: {top_match['score']})")
        print(f"       Snippet: \"{top_match['snippet']}\"")
        print(f"       Matched Keywords: {top_match['matched_keywords']}")

        # Test 2: Search for 'convolutional vision'
        res2 = search_papers("convolutional vision", db)
        assert res2["total_results"] >= 1
        top_cnn = res2["results"][0]
        assert "Convolutional" in top_cnn["title"]
        print(f"[PASS] Matched query 'convolutional vision' -> Top Paper: '{top_cnn['title']}' (Score: {top_cnn['score']})")

        # Test 3: Search with no matching results
        res3 = search_papers("quantum thermodynamics astrophysics", db)
        assert res3["total_results"] == 0
        assert len(res3["results"]) == 0
        print(f"[PASS] Non-matching query returned clean zero-result message: \"{res3['message']}\"")

        # Test 4: Verify REST API GET /search/?q=attention
        api_res = client.get("/search/?q=attention")
        assert api_res.status_code == 200
        api_data = api_res.json()
        assert api_data["status"] == "success"
        assert api_data["total_results"] >= 1
        print(f"[PASS] REST API GET /search/?q=attention passed successfully.")

        # Test 5: Verify GET /search/history
        hist_res = client.get("/search/history")
        assert hist_res.status_code == 200
        assert len(hist_res.json()["history"]) >= 1
        print(f"[PASS] Search history endpoint verified.")

        print("=" * 65)
        print("[OK] All Search Engine Tests Passed Successfully!")
        print("=" * 65)

    finally:
        db.close()


if __name__ == "__main__":
    run_search_tests()
