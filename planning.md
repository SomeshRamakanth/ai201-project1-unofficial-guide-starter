# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

Student-generated knowledge about CS professors and courses at Lakewood State University. This includes Rate My Professor-style reviews, Reddit threads with exam tips and course selection advice, and informal student guides. This knowledge is valuable because official course descriptions only list topics and prerequisites — they say nothing about a professor's teaching style, how hard exams actually are, whether office hours are useful, or which courses have brutal workloads. Students currently have to dig through fragmented subreddit threads and review sites to piece this together. This system makes it searchable in plain language.

---

## Documents

| # | Source | Description | URL or location |
|---|--------|-------------|-----------------|
| 1 | Rate My Professor (simulated) | Reviews for Prof. Alan Hartley — Data Structures | documents/rmp_hartley_data_structures.txt |
| 2 | Rate My Professor (simulated) | Reviews for Prof. Sandra Chen — Algorithms | documents/rmp_chen_algorithms.txt |
| 3 | Rate My Professor (simulated) | Reviews for Prof. Marcus Webb — Operating Systems | documents/rmp_webb_operating_systems.txt |
| 4 | Rate My Professor (simulated) | Reviews for Prof. Diana Lopez — Machine Learning | documents/rmp_lopez_machine_learning.txt |
| 5 | Rate My Professor (simulated) | Reviews for Prof. Kevin Park — Database Systems | documents/rmp_park_databases.txt |
| 6 | Rate My Professor (simulated) | Reviews for Prof. Rachel Novak — Computer Networks | documents/rmp_novak_networks.txt |
| 7 | Reddit r/LakewoodStateCS (simulated) | Thread: "Best CS professors for feedback and learning?" | documents/reddit_best_professors.txt |
| 8 | Reddit r/LakewoodStateCS (simulated) | Thread: "Tips for surviving CS exams — what actually helped?" | documents/reddit_exam_tips.txt |
| 9 | Reddit r/LakewoodStateCS (simulated) | Thread: "Which CS courses have the worst workload?" | documents/reddit_workload.txt |
| 10 | Reddit r/LakewoodStateCS (simulated) | Thread: "Course selection advice for CS sophomores" | documents/reddit_course_selection.txt |
| 11 | Student blog (simulated) | Informal guide to the CS department | documents/student_guide_cs_dept.txt |

---

## Chunking Strategy

**Chunk size:** 400 characters

**Overlap:** 60 characters

**Reasoning:** The corpus is review-style and Reddit-style text — each review is a short paragraph (2–5 sentences). A 400-character chunk captures roughly one full review or one coherent comment without splitting a single opinion across two chunks. Using 500+ characters risked merging two different reviewers' opinions into a single chunk, which would confuse retrieval. The 60-character overlap preserves sentence continuity at boundaries — important when a reviewer's key point (e.g., "exams are straightforward once you do the practice problems") starts near the end of a chunk.

---

## Retrieval Approach

**Embedding model:** `all-MiniLM-L6-v2` via `sentence-transformers`

**Top-k:** 5

**Production tradeoff reflection:** For a production system I'd weigh several factors. Context length: all-MiniLM-L6-v2 has a 256-token limit, which is fine for short reviews but would truncate longer documents — OpenAI's `text-embedding-3-large` or Cohere's `embed-v3` handle up to 8k tokens. Multilingual support: if the student body speaks multiple languages, a multilingual model like `paraphrase-multilingual-MiniLM-L12-v2` would be necessary. Domain specificity: general-purpose embeddings may not understand CS jargon well — a fine-tuned model on student review data would likely improve retrieval precision. Latency: running sentence-transformers locally is fast and free, but an API-hosted model adds network latency while removing the need for local GPU/CPU resources. For this project, local + free is the right tradeoff.

---

## Evaluation Plan

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | Which CS professor gives the most useful feedback on assignments? | Prof. Sandra Chen (Algorithms) — multiple reviews mention detailed written feedback and quick response to office hour questions |
| 2 | How hard are exams in Data Structures with Hartley? | Hard — Hartley's exams require deep understanding, not just memorization; students recommend doing all practice problems |
| 3 | Which CS professor is the easiest grader? | Prof. Kevin Park (Database Systems) — reviews consistently call it an easy A, though lectures are described as not very useful |
| 4 | How heavy is the workload in Machine Learning with Lopez? | Very heavy — weekly readings, coding projects in PyTorch, and a final project; students say it's worth it but plan for 15+ hrs/week |
| 5 | What do students say about office hours in Computer Networks? | Novak's office hours are described as extremely helpful — she works through problems step by step and stays late |

---

## Anticipated Challenges

1. **Chunk boundary splitting a key claim.** A review like "The midterm was brutal — 40% of the class failed — but Hartley curved everyone up 15 points" could be split so the retrieval chunk only contains the first half. The system would return a misleading answer about exam difficulty without the curve context. The 60-character overlap partially mitigates this, but edge cases will still occur.

2. **Synonym and nickname mismatch.** Students often refer to professors by last name only ("Chen's class"), by nickname, or by course number ("CS301"). The embedding model may not link "algorithms course" to "Chen" or "CS301" without seeing both terms in the same chunk. This is a known weakness of dense retrieval on short-text corpora without metadata filtering.

---

## Architecture

```
Raw .txt files in documents/
        │
        ▼
[1] Ingestion (ingest.py)
    • Load each .txt file
    • Strip extra whitespace
    • Tag each doc with source filename as metadata
        │
        ▼
[2] Chunking (pipeline.py → chunk_text())
    • Split by character with 400-char chunks, 60-char overlap
    • Preserve source metadata per chunk
        │
        ▼
[3] Embedding + Vector Store (pipeline.py → build_index())
    • Embed with sentence-transformers all-MiniLM-L6-v2
    • Store in ChromaDB (local, persistent at ./chroma_db)
        │
        ▼
[4] Retrieval (rag.py → retrieve())
    • Embed user query with same model
    • Return top-5 chunks by cosine similarity from ChromaDB
        │
        ▼
[5] Generation (rag.py → generate())
    • Format retrieved chunks as numbered context blocks
    • Send to Groq llama-3.3-70b-versatile with grounding system prompt
    • Response includes [Source: filename] citations
        │
        ▼
[6] Query Interface (app.py)
    • Gradio ChatInterface
    • Shows answer + source citations
```

---

## AI Tool Plan

**Milestone 3 — Ingestion and chunking:**
Give Claude the Chunking Strategy section and the document list from this file. Ask it to implement `load_documents()` and `chunk_text()` in `pipeline.py` — `load_documents()` should return a list of dicts with `text` and `source` keys, and `chunk_text()` should split using the 400/60 parameters specified above. Verify by printing chunk count and inspecting 3 random chunks to confirm they don't mid-sentence truncate a reviewer's main point.

**Milestone 4 — Embedding and retrieval:**
Give Claude the Architecture diagram and ask it to implement `build_index()` (embed + store in ChromaDB) and `retrieve()` (query ChromaDB, return top-5 chunks with sources) in `pipeline.py` and `rag.py`. Verify by running 2 test queries and checking that the returned chunks are topically relevant to the question.

**Milestone 5 — Generation and interface:**
Give Claude the Grounded Generation requirement and the system prompt spec. Ask it to implement `generate()` in `rag.py` and the Gradio `app.py`. Verify that every response includes at least one `[Source: ...]` citation and that the model declines to answer when no relevant chunks are retrieved.
