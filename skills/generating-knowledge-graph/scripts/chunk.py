#!/usr/bin/env python3
"""Deterministic character-window chunking with overlap."""

def chunk_text(text, size=1200, overlap=150):
    text = text.strip()
    if not text:
        return []
    if len(text) <= size:
        return [text]
    step = max(1, size - overlap)
    chunks = []
    start = 0
    while start < len(text):
        chunks.append(text[start:start + size])
        if start + size >= len(text):
            break
        start += step
    return chunks
