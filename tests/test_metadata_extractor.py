import sys
import os

# Add project root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.services.metadata_extractor import MetadataExtractor


def test_metadata_extraction_ieee_style():
    print("=" * 65)
    print(" Running Automatic Metadata Extractor Tests")
    print("=" * 65)

    sample_ieee_text = (
        "IEEE Transactions on Neural Networks and Learning Systems, Vol. 34, 2023\n"
        "Deep Residual Attention Networks for Image Classification\n"
        "Kaiming He, Xiangyu Zhang, Shaoqing Ren, Jian Sun\n"
        "Department of Computer Science, Microsoft Research, Redmond, WA, USA\n"
        "Email: {khe, xzhang}@microsoft.com\n\n"
        "Abstract—Deep convolutional neural networks have led to a series of breakthroughs in image classification. "
        "In this work, we present a residual learning framework to ease the training of networks that are substantially deeper.\n\n"
        "Index Terms—Deep learning, Residual Networks, Image Classification, Attention Mechanism.\n\n"
        "1 Introduction\n"
        "Deconstructive feature extraction has transformed modern computer vision."
    )

    fake_extraction_data = {
        "full_text": sample_ieee_text,
        "pages": [{"page_number": 1, "text": sample_ieee_text, "has_text": True}],
        "metadata": {
            "title": "",
            "author": "",
            "creation_date": "D:20230615143000"
        },
        "file_name": "deep_residual_attention_networks.pdf"
    }

    meta = MetadataExtractor.extract_all_metadata(fake_extraction_data)

    # 1. Verify Title (Skipped IEEE banner, captured actual title)
    assert "Deep Residual Attention Networks" in meta["title"], f"Title failed: {meta['title']}"
    print(f"[PASS] Extracted Title: '{meta['title']}'")

    # 2. Verify Authors (Filtered affiliation lines)
    assert "Kaiming He" in meta["authors"] and "Jian Sun" in meta["authors"], f"Authors failed: {meta['authors']}"
    print(f"[PASS] Extracted Authors: '{meta['authors']}'")

    # 3. Verify Abstract
    assert meta["abstract"] is not None and "residual learning framework" in meta["abstract"]
    print(f"[PASS] Extracted Abstract: '{meta['abstract'][:80]}...'")

    # 4. Verify Publication Year
    assert meta["publication_year"] == 2023
    print(f"[PASS] Extracted Publication Year: {meta['publication_year']}")

    # 5. Verify Explicit Keywords
    assert "Deep learning" in meta["explicit_keywords"] or "Residual Networks" in meta["explicit_keywords"]
    print(f"[PASS] Extracted Explicit Keywords: {meta['explicit_keywords']}")

    # 6. Verify Confidence Flags
    conf = meta["extraction_confidence"]
    assert conf["title_detected"] and conf["authors_detected"] and conf["abstract_detected"]
    print(f"[PASS] Confidence Scores: {conf}")

    print("=" * 65)
    print("[OK] All Metadata Extractor Tests Passed Successfully!")
    print("=" * 65)


if __name__ == "__main__":
    test_metadata_extraction_ieee_style()
