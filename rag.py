"""
rag.py — retrieval and grounded generation functions.

Used by app.py and evaluate.py. Does not run on its own.
"""

import os
import chromadb
from sentence_transformers import SentenceTransformer
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

CHROMA_DIR = "chroma_db"
COLLECTION_NAME = "unofficial_guide"
TOP_K = 5
GROQ_MODEL = "llama-3.3-70b-versatile"

# Module-level singletons — loaded once, reused across calls
_model: SentenceTransformer | None = None
_collection = None
_groq_client: Groq | None = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def _get_collection():
    global _collection
    if _collection is None:
        client = chromadb.PersistentClient(path=CHROMA_DIR)
        _collection = client.get_collection(COLLECTION_NAME)
    return _collection


def _get_groq() -> Groq:
    global _groq_client
    if _groq_client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "GROQ_API_KEY not found. Copy .env.example to .env and add your key."
            )
        _groq_client = Groq(api_key=api_key)
    return _groq_client


# ── Retrieval ─────────────────────────────────────────────────────────────────

def retrieve(query: str, top_k: int = TOP_K) -> list[dict]:
    """
    Embed the query and return the top_k most similar chunks.
    Each result: {text, source, chunk_index, distance}
    """
    model = _get_model()
    collection = _get_collection()

    query_embedding = model.encode([query], convert_to_list=True)[0]
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    chunks = []
    for text, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        chunks.append({
            "text": text,
            "source": meta["source"],
            "chunk_index": meta["chunk_index"],
            "distance": dist,
        })
    return chunks


# ── Generation ────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are The Unofficial Guide — a helpful assistant that answers questions about \
CS professors and courses at Lakewood State University using only the student-generated \
documents provided below as context.

Rules you must follow without exception:
1. Answer ONLY using information from the provided context. Do not use any prior knowledge \
about universities, professors, or courses.
2. Every factual claim in your answer must be traceable to at least one context chunk. \
End your answer with a "Sources:" section listing the filenames of every chunk you drew from.
3. If the context does not contain enough information to answer the question, say: \
"I don't have enough information in the documents to answer that reliably." \
Do not guess or invent details.
4. Be concise and direct. Students asking this question want a useful answer, not a wall of text.
"""


def generate(query: str, chunks: list[dict]) -> str:
    """
    Generate a grounded answer using the retrieved chunks.
    Returns the full response text including source citations.
    """
    if not chunks:
        return (
            "I don't have enough information in the documents to answer that reliably. "
            "Try rephrasing your question or asking about a specific professor or course."
        )

    # Format context blocks — numbered so the model can reference them
    context_blocks = []
    for i, chunk in enumerate(chunks, 1):
        context_blocks.append(
            f"[{i}] Source: {chunk['source']}\n{chunk['text']}"
        )
    context_str = "\n\n---\n\n".join(context_blocks)

    user_message = f"Context:\n\n{context_str}\n\n---\n\nQuestion: {query}"

    client = _get_groq()
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0.2,  # low temperature for factual grounding
        max_tokens=600,
    )

    return response.choices[0].message.content


# ── Combined query function ────────────────────────────────────────────────────

def query(question: str) -> tuple[str, list[dict]]:
    """Retrieve chunks and generate an answer. Returns (answer, chunks)."""
    chunks = retrieve(question)
    answer = generate(question, chunks)
    return answer, chunks
