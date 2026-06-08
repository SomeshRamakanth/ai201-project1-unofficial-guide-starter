# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Domain

Student-generated knowledge about CS professors and courses at Lakewood State University. This covers Rate My Professor-style reviews, Reddit threads with exam tips and course selection advice, and an informal student survival guide. This knowledge is valuable because official course descriptions only list topics and prerequisites — they say nothing about teaching style, exam difficulty, actual weekly workload, or whether office hours are useful. Students currently have to dig through fragmented subreddit threads and review sites. This system makes it searchable in plain language.

---

## Document Sources

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | Rate My Professor (simulated) | Reviews | documents/rmp_hartley_data_structures.txt |
| 2 | Rate My Professor (simulated) | Reviews | documents/rmp_chen_algorithms.txt |
| 3 | Rate My Professor (simulated) | Reviews | documents/rmp_webb_operating_systems.txt |
| 4 | Rate My Professor (simulated) | Reviews | documents/rmp_lopez_machine_learning.txt |
| 5 | Rate My Professor (simulated) | Reviews | documents/rmp_park_databases.txt |
| 6 | Rate My Professor (simulated) | Reviews | documents/rmp_novak_networks.txt |
| 7 | Reddit r/LakewoodStateCS (simulated) | Forum thread | documents/reddit_best_professors.txt |
| 8 | Reddit r/LakewoodStateCS (simulated) | Forum thread | documents/reddit_exam_tips.txt |
| 9 | Reddit r/LakewoodStateCS (simulated) | Forum thread | documents/reddit_workload.txt |
| 10 | Reddit r/LakewoodStateCS (simulated) | Forum thread | documents/reddit_course_selection.txt |
| 11 | CS Student Council (simulated) | Student guide | documents/student_guide_cs_dept.txt |

---

## Chunking Strategy

**Chunk size:** 400 characters

**Overlap:** 60 characters

**Why these choices fit your documents:** The corpus is review-style and Reddit-style text — each review is a short paragraph (2–5 sentences, roughly 150–450 characters). A 400-character chunk captures roughly one full review or one coherent Reddit comment without merging two different reviewers' opinions into a single chunk, which would confuse retrieval. Using 500+ characters risked combining two perspectives into one chunk. The 60-character overlap preserves sentence continuity at boundaries — important when a reviewer's key conclusion (e.g., "exams are fair once you do the practice problems") starts near the end of a chunk. A newline-snapping heuristic in `chunk_text()` prefers to break at paragraph boundaries rather than mid-sentence.

**Final chunk count:** 105 chunks across 11 documents (~9.5 chunks per document on average).

---

## Embedding Model

**Model used:** `all-MiniLM-L6-v2` via `sentence-transformers` (runs locally, no API key required)

**Production tradeoff reflection:** For a production system several tradeoffs matter. Context length: `all-MiniLM-L6-v2` has a 256-token limit, fine for short reviews but would silently truncate longer documents — `text-embedding-3-large` (OpenAI) or `embed-v3` (Cohere) handle up to 8k tokens. Multilingual support: if the student body posts in multiple languages, a multilingual model like `paraphrase-multilingual-MiniLM-L12-v2` would be needed. Domain specificity: general-purpose embeddings may not capture CS jargon well — a model fine-tuned on student review data would improve retrieval precision on queries like "professor who gives partial credit" or "easy grader." Latency: local models are fast with no network overhead, but require sufficient CPU/RAM; API-hosted models add ~100–300ms of latency but shift compute costs to the provider. For this project, local + free is correct.

---

## Grounded Generation

**System prompt grounding instruction:**

The system prompt in `rag.py` contains the following explicit rules given to the LLM before every query:

> "Answer ONLY using information from the provided context. Do not use any prior knowledge about universities, professors, or courses."
> "Every factual claim in your answer must be traceable to at least one context chunk. End your answer with a 'Sources:' section listing the filenames of every chunk you drew from."
> "If the context does not contain enough information to answer the question, say: 'I don't have enough information in the documents to answer that reliably.' Do not guess or invent details."

The context is formatted as numbered blocks (`[1] Source: filename\n...`) so the model can reference specific chunks when citing.

**How source attribution is surfaced in the response:** Every answer from the LLM ends with a `Sources:` section naming the document filenames it drew from. The Gradio UI additionally shows a "Retrieved from:" block below the answer listing each source file with its cosine similarity score, so users can see not just which documents were cited but how closely they matched the query.

---

## Evaluation Report

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | Which CS professor gives the most useful feedback on assignments? | Sandra Chen — detailed written feedback, thoughtful office hours | Correctly identified Chen; cited detailed written comments and office-hour structure | Relevant (best dist: 0.23) | Accurate |
| 2 | How hard are exams in Data Structures with Hartley? | Hard; derivation questions, ~65% avg before curve | "Hard", "brutal", "among the hardest in the department"; mentioned derivation and generous partial credit | Relevant (best dist: 0.31) | Accurate |
| 3 | Which CS professor is the easiest grader? | Kevin Park (DB Systems) — easy A, ~4-5 hrs/week | Said it didn't have enough info — couldn't name the professor even though answer was in the documents | Partially relevant (retrieved "easiest graded course" chunk but not Park review chunks) | Inaccurate |
| 4 | How heavy is the workload in Machine Learning with Lopez? | Very heavy (~15-16 hrs/week); PyTorch projects + final project | Correctly said 15+ hrs/week, front-loaded theory and brutal weeks 7-15 | Partially relevant (best dist: 0.43; OS chunk appeared in top-2) | Partially accurate |
| 5 | What do students say about office hours in Computer Networks? | Novak's office hours exceptional — stays late, step-by-step help | Correctly described Novak's office hours: step-by-step, stays late, queue system | Relevant (best dist: 0.41, though a Chen chunk appeared first) | Accurate |

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

**Question that failed:** "Which CS professor is the easiest grader?"

**What the system returned:** "I don't have enough information in the documents to answer that reliably. The provided context does mention that one course is 'the easiest graded course in the upper-level CS electives,' but it does not specify the professor's name for that particular statement."

**Root cause (tied to a specific pipeline stage):** This is a retrieval failure at the chunking stage. The relevant information was split across chunk boundaries: one chunk from `reddit_best_professors.txt` contained the phrase "the easiest graded course in the upper-level CS electives" (which matched the query semantically), but the professor's name — "Park" — was in a different chunk further in the same document. The LLM received the first chunk (mentioning the course's easiness) but not the adjacent chunk that named Prof. Kevin Park. The model correctly refused to guess, but the right answer was sitting in documents that ranked 6th or lower. Separately, the `rmp_park_databases.txt` reviews that say "Easy A if you show up" use the phrase "easy A" rather than "easy grader" — `all-MiniLM-L6-v2` did not map these semantically close enough to surface them in the top-5.

**What you would change to fix it:** Two options: (1) Increase top-k from 5 to 8 to retrieve more candidate chunks and give the LLM a better chance of having both the "easiest" description and the professor's name in context; (2) Use larger chunks (600+ characters) for the Reddit-style thread documents so that a comment mentioning both the course quality and the professor's name lands in a single chunk rather than being split. Option 2 would directly fix this case at the chunking stage rather than compensating at the retrieval stage.

---

## Spec Reflection

**One way the spec helped you during implementation:**

Writing the chunking strategy in planning.md before writing any code forced me to think about what a "unit of meaning" looked like in the corpus. Review text is naturally paragraph-sized, which justified the 400-character limit. Without that pre-thinking I might have defaulted to a larger chunk size and ended up merging different reviewers' opinions into single chunks — a retrieval problem that would have been hard to diagnose after the fact.

**One way your implementation diverged from the spec, and why:**

The spec called for a simple character split. During implementation I added a newline-snapping heuristic in `chunk_text()` — if a chunk boundary falls near a paragraph break, the cut snaps to the break rather than splitting mid-sentence. This was not in the original planning.md but emerged naturally when I saw the raw text structure of the documents.

---

## AI Usage

**Instance 1**

- *What I gave the AI:* The Chunking Strategy section from planning.md (chunk size 400, overlap 60, newline-snapping requirement) and asked it to implement `chunk_text()` in pipeline.py.
- *What it produced:* A character-split function with overlap that also tries to snap to the nearest newline within the last 80 characters of a chunk window.
- *What I changed or overrode:* Changed the snap window from 50 to 80 characters after testing on the review documents, where paragraph breaks sometimes appeared 60–70 characters before the chunk boundary.

**Instance 2**

- *What I gave the AI:* The Grounded Generation requirement from the project spec ("responses should not rely on the model's general knowledge") and asked it to write the system prompt for `rag.py`.
- *What it produced:* A four-rule system prompt that prohibits answering from prior knowledge, requires a Sources section, requires a specific "I don't have enough information" fallback, and instructs the model to be concise.
- *What I changed or overrode:* Added the explicit instruction about formatting context as numbered blocks (`[1] Source: filename`) so the model could reference specific chunks. The original produced prompt did not specify how to cite, resulting in vague attributions like "based on the documents."
