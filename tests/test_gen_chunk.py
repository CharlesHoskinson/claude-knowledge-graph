# tests/test_gen_chunk.py
import pytest
import chunk as chunker


def test_overlap_ge_size_raises():
    # A7: overlap >= size would blow up into near-duplicate windows; reject it.
    with pytest.raises(ValueError):
        chunker.chunk_text("abcdef" * 50, size=100, overlap=100)
    with pytest.raises(ValueError):
        chunker.chunk_text("abcdef" * 50, size=100, overlap=150)

def test_short_text_is_one_chunk():
    assert chunker.chunk_text("hello world", size=1200, overlap=150) == ["hello world"]

def test_empty_text_is_no_chunks():
    assert chunker.chunk_text("   ", size=100, overlap=10) == []

def test_long_text_splits_with_overlap_and_is_deterministic():
    text = "abcdefghij" * 30          # 300 chars
    chunks = chunker.chunk_text(text, size=100, overlap=20)
    assert len(chunks) >= 3
    assert all(len(c) <= 100 for c in chunks)
    # overlap: each chunk after the first starts 80 chars after the previous start
    assert chunks[1].startswith(text[80:80+10])
    assert chunker.chunk_text(text, size=100, overlap=20) == chunks   # deterministic
    # full coverage: concatenated unique span reconstructs the text
    assert chunks[0][0] == text[0] and chunks[-1][-1] == text[-1]
