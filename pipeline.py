"""
pipeline.py — run once to ingest, chunk, embed, and store all documents.

Usage:
    python pipeline.py

This will read every .txt file from documents/, split into chunks,
embed with sentence-transformers, and persist to ./chroma_db.
Re-running clears and rebuilds the collection.
"""

import os
import glob
import chromadb
from sentence_transformers import SentenceTransformer

DOCUMENTS_DIR = "documents"
CHROMA_DIR = "chroma_db"
COLLECTION_NAME = "unofficial_guide"

CHUNK_SIZE = 400    # characters — fits one review or one coherent Reddit comment
CHUNK_OVERLAP = 60  # characters — preserves sentence continuity at boundaries


# ── 1. Ingestion ─────────────────────────────────────────────────────────────

def load_documents(documents_dir: str) -> list[dict]:
    """Load all .txt files from documents_dir. Returns list of {text, source}."""
    docs = []
    pattern = os.path.join(documents_dir, "*.txt")
    paths = sorted(glob.glob(pattern))
    if not paths:
        raise FileNotFoundError(f"No .txt files found in '{documents_dir}/'")
    for path in paths:
        with open(path, encoding="utf-8") as f:
            text = f.read().strip()
        # Collapse runs of blank lines to a single blank line
        while "\n\n\n" in text:
            text = text.replace("\n\n\n", "\n\n")
        source = os.path.basename(path)
        docs.append({"text": text, "source": source})
    print(f"Loaded {len(docs)} documents.")
    return docs


# ── 2. Chunking ───────────────────────────────────────────────────────────────

MIN_CHUNK_LEN = 80  # discard fragments shorter than this


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """
    Split text into overlapping character-based chunks.
    Tries to break on a newline near the chunk boundary rather than mid-sentence.
    """
    chunks = []
    start = 0
    length = len(text)
    while start < length:
        end = min(start + chunk_size, length)
        # Try to snap the cut to a newline within the last 80 chars of the window
        if end < length:
            snap_window = text[max(0, end - 80): end]
            last_nl = snap_window.rfind("\n")
            if last_nl != -1:
                snapped = max(0, end - 80) + last_nl + 1
                if snapped > start + MIN_CHUNK_LEN:  # only snap if enough content before it
                    end = snapped
        chunk = text[start:end].strip()
        if len(chunk) >= MIN_CHUNK_LEN:
            chunks.append(chunk)
        if end >= length:
            break  # reached end of document — stop (prevents 1-char stepping)
        start = end - overlap
    return chunks


def chunk_documents(docs: list[dict]) -> list[dict]:
    """Chunk all documents. Returns list of {text, source, chunk_index}."""
    all_chunks = []
    for doc in docs:
        chunks = chunk_text(doc["text"])
        for i, chunk in enumerate(chunks):
            all_chunks.append({
                "text": chunk,
                "source": doc["source"],
                "chunk_index": i,
            })
    print(f"Created {len(all_chunks)} chunks from {len(docs)} documents.")
    return all_chunks


# ── 3. Embedding + Vector Store ───────────────────────────────────────────────

def build_index(chunks: list[dict], chroma_dir: str = CHROMA_DIR) -> None:
    """Embed chunks with all-MiniLM-L6-v2 and store in ChromaDB."""
    print("Loading embedding model (all-MiniLM-L6-v2)...")
    model = SentenceTransformer("all-MiniLM-L6-v2")

    print("Embedding chunks...")
    texts = [c["text"] for c in chunks]
    embeddings = model.encode(texts, show_progress_bar=True, convert_to_list=True)

    print(f"Connecting to ChromaDB at '{chroma_dir}'...")
    client = chromadb.PersistentClient(path=chroma_dir)

    # Delete and recreate so re-runs start fresh
    try:
        client.delete_collection(COLLECTION_NAME)
        print(f"Cleared existing '{COLLECTION_NAME}' collection.")
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    ids = [f"{c['source']}__chunk{c['chunk_index']}" for c in chunks]
    metadatas = [{"source": c["source"], "chunk_index": c["chunk_index"]} for c in chunks]

    # ChromaDB add() has a limit per call; batch in groups of 500
    batch_size = 500
    for i in range(0, len(chunks), batch_size):
        collection.add(
            ids=ids[i: i + batch_size],
            embeddings=embeddings[i: i + batch_size],
            documents=texts[i: i + batch_size],
            metadatas=metadatas[i: i + batch_size],
        )

    print(f"Stored {len(chunks)} chunks in ChromaDB collection '{COLLECTION_NAME}'.")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    docs = load_documents(DOCUMENTS_DIR)
    chunks = chunk_documents(docs)
    build_index(chunks)
    print("\nDone. Run `python app.py` to start the query interface.")
