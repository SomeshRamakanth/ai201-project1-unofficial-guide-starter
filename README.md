# The Unofficial Guide — Project 1

## Domain

Student-generated knowledge about CS professors and courses at Lakewood State University. This covers Rate My Professor-style reviews, Reddit threads with exam tips and course selection advice, and an informal student survival guide. This knowledge is valuable because official course descriptions only list topics and prerequisites — they say nothing about teaching style, exam difficulty, actual weekly workload, or whether office hours are useful. Students currently have to dig through fragmented subreddit threads and review sites. This system makes it searchable in plain language.

---

## Document Sources

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | Rate My Professor | Reviews | documents/rmp_hartley_data_structures.txt |
| 2 | Rate My Professor | Reviews | documents/rmp_chen_algorithms.txt |
| 3 | Rate My Professor | Reviews | documents/rmp_webb_operating_systems.txt |
| 4 | Rate My Professor | Reviews | documents/rmp_lopez_machine_learning.txt |
| 5 | Rate My Professor | Reviews | documents/rmp_park_databases.txt |
| 6 | Rate My Professor | Reviews | documents/rmp_novak_networks.txt |
| 7 | Reddit r/LakewoodStateCS | Forum thread | documents/reddit_best_professors.txt |
| 8 | Reddit r/LakewoodStateCS | Forum thread | documents/reddit_exam_tips.txt |
| 9 | Reddit r/LakewoodStateCS | Forum thread | documents/reddit_workload.txt |
| 10 | Reddit r/LakewoodStateCS | Forum thread | documents/reddit_course_selection.txt |
| 11 | CS Student Council | Student guide | documents/student_guide_cs_dept.txt |

---

## Chunking Strategy

**Chunk size:** 400 characters

**Overlap:** 60 characters

**Why these choices fit your documents:** The corpus is review-style and Reddit-style text — each review is a short paragraph (2–5 sentences, roughly 150–450 characters). A 400-character chunk captures roughly one full review or one coherent Reddit comment without merging two different reviewers' opinions into a single chunk, which would confuse retrieval. Using 500+ characters risked combining two perspectives into one chunk. The 60-character overlap preserves sentence continuity at boundaries — important when a reviewer's key conclusion (e.g., "exams are fair once you do the practice problems") starts near the end of a chunk. A newline-snapping heuristic in `chunk_text()` prefers to break at paragraph boundaries rather than mid-sentence.

**Final chunk count:** 105 chunks across 11 documents (~9.5 chunks per document on average).

---

## Sample Chunks

Five representative chunks drawn from the final index, showing different document types and how content is preserved at boundaries.

---

**Chunk 1** — `rmp_park_databases.txt` (index 8)
> 's databases class is the one. He's friendly, class meets twice a week and is never overwhelming. The SQL content is genuinely useful for anyone going into software roles. He drops the lowest homework grade and gives a generous final exam. Good option when you need to balance a tough semester.

*Self-contained? Yes — describes Park's course policies and grading in one coherent thought.*

---

**Chunk 2** — `reddit_course_selection.txt` (index 6)
> up distributed systems coursework later. Novak is one of the better professors — her office hours alone make it worth it.
>
> u/rising_sophomore [OP]: Is Park's Databases worth taking if I want to go into ML?
>
> u/gradschool_bound: SQL is essential for any data work. Park's class covers it at a reasonable depth. The class won't be your hardest but the knowledge is directly applicable — querying, joins, normalization...

*Self-contained? Yes — a full Q&A exchange with a clear question and direct answer.*

---

**Chunk 3** — `reddit_best_professors.txt` (index 3)
> the teaches sticks. I still remember his lecture on amortized complexity word for word.
>
> u/cs_junior_lsu [OP]: What about for systems? I need to take OS next semester.
>
> u/nightowl_coder: Webb for OS is fine. He's not exciting but he's fair and knows his material. The real learning in that class comes from the projects, not the lectures. His office hours are okay but don't expect him to lavish feedback on you...

*Self-contained? Yes — captures a thread exchange about OS and Webb's teaching style.*

---

**Chunk 4** — `student_guide_cs_dept.txt` (index 2)
> doing every practice problem he posts, not just reading through them. His class has a steep curve by the end; very few students fail if they engage with the material. Best used for: building a real foundation in CS fundamentals.
>
> Prof. Sandra Chen (Algorithms, CS302)
> Difficulty: Moderate-High. Reward: Very High. Chen is universally praised for the quality of her feedback. Assignments come back wit...

*Self-contained? Mostly — covers Hartley's conclusion and the start of Chen's profile. The 60-char overlap is visible here, bridging two adjacent sections.*

---

**Chunk 5** — `rmp_chen_algorithms.txt` (index 0)
> SOURCE: Rate My Professor — Prof. Sandra Chen, CS302 Algorithms, Lakewood State University
>
> REVIEW 1 | Rating: 5/5 | Difficulty: 4/5
> Chen is the gold standard for feedback in this department. Every assignment comes back with detailed written comments — not just points off but an explanation of exactly where your reasoning broke down and what a correct approach looks like. I've never had a pro...

*Self-contained? Yes — a complete review with rating, context, and the reviewer's main point intact.*

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

**How source attribution is surfaced in the response:** Every answer from the LLM ends with a `Sources:` section naming the document filenames it drew from. The Gradio UI additionally shows a "Retrieved from:" block below the answer listing each source file, so users can see exactly which documents the answer came from.

---

## Retrieval Test Results

Three queries tested against the vector store. Top-5 chunks returned for each, with distance scores (lower = more similar).

---

**Query 1: "Which CS professor gives the most useful feedback?"**

| Rank | Source | Distance | Snippet |
|------|--------|----------|---------|
| 1 | `reddit_best_professors.txt` | 0.2289 | *"Best CS professors for feedback and learning?" — thread where multiple students name Chen as the top choice for feedback* |
| 2 | `student_guide_cs_dept.txt` | 0.3471 | *Hartley profile mentioning practice problems and steep curve* |
| 3 | `rmp_webb_operating_systems.txt` | 0.3898 | *Webb review: "no surprises on exams"* |
| 4 | `student_guide_cs_dept.txt` | 0.4124 | *Chen profile: "universally praised for the quality of her feedback"* |
| 5 | `rmp_hartley_data_structures.txt` | 0.4133 | *Hartley review header* |

**Why the top results are relevant:** Rank 1 is a Reddit thread explicitly titled "Best CS professors for feedback" — the query maps directly to this document's topic. Rank 4 contains the phrase "universally praised for the quality of her feedback" which is a near-exact semantic match. The distance of 0.23 on rank 1 is very strong (well below the 0.5 concern threshold), confirming high-confidence retrieval. Ranks 3 and 5 are weaker but still within the useful range.

---

**Query 2: "How hard are exams in Data Structures with Hartley?"**

| Rank | Source | Distance | Snippet |
|------|--------|----------|---------|
| 1 | `student_guide_cs_dept.txt` | 0.3091 | *Hartley profile: "exams are among the hardest in the department"* |
| 2 | `reddit_workload.txt` | 0.3266 | *"Hartley's Data Structures (CS201) is hard but the workload is more manageable than its reputation suggests"* |
| 3 | `rmp_hartley_data_structures.txt` | 0.3300 | *Review mentioning class average ~65 before curve* |
| 4 | `rmp_hartley_data_structures.txt` | 0.3552 | *"Do every single practice problem he posts"* |
| 5 | `rmp_hartley_data_structures.txt` | 0.3738 | *Hartley review file header + Review 1* |

**Why the top results are relevant:** Three of the top 5 are from `rmp_hartley_data_structures.txt` — the most directly relevant source. The student guide (rank 1) summarizes the same information in a single paragraph. All distances are below 0.38, indicating confident, on-topic retrieval. This query performed best overall.

---

**Query 3: "What is the workload like in Machine Learning with Lopez?"**

| Rank | Source | Distance | Snippet |
|------|--------|----------|---------|
| 1 | `student_guide_cs_dept.txt` | 0.4451 | *Systems programming section — not about ML* |
| 2 | `reddit_workload.txt` | 0.5468 | *Lopez workload summary: ~15-16 hrs/week* |
| 3 | `reddit_workload.txt` | 0.5694 | *Park databases workload: ~4-5 hrs/week* |
| 4 | `reddit_workload.txt` | 0.5788 | *Ranked workload list including Lopez at top* |
| 5 | `reddit_workload.txt` | 0.5856 | *reddit_workload.txt header* |

**Why retrieval is weaker here:** The top result (dist: 0.45) is from the systems section of the student guide — a partial mismatch. The most relevant content (Lopez, 15-16 hrs/week) doesn't appear until rank 2 with a distance of 0.55. This is above the ideal threshold and reflects a semantic gap: the query says "Machine Learning with Lopez" but the most relevant chunks use "Lopez's ML course" or "CS410" — the embedding model doesn't fully bridge these phrasings. The system still produced a correct answer by synthesizing ranks 2–5, but retrieval quality here is the weakest of the three tests.

---

## Example Responses

**Response 1 — with source attribution (works well)**

> **Query:** Which CS professor gives the most useful feedback on assignments?
>
> **Answer:** According to the provided context, Prof. Sandra Chen is universally praised for the quality of her feedback. Assignments come back with detailed, constructive comments, and her office hours are structured to help students think, not just to give them answers.
>
> Sources: student_guide_cs_dept.txt, rmp_chen_algorithms.txt
>
> **Retrieved from:**
> • reddit_best_professors.txt
> • student_guide_cs_dept.txt
> • rmp_webb_operating_systems.txt
> • rmp_hartley_data_structures.txt

---

**Response 2 — with source attribution (multi-source reasoning)**

> **Query:** Should I take Algorithms before Machine Learning?
>
> **Answer:** Yes, it's recommended to take Chen's Algorithms before Lopez's Machine Learning. The algorithm analysis fundamentals taught in Chen's class — Big-O, dynamic programming, graph algorithms — are directly used in Machine Learning, and taking them in sequence will be beneficial.
>
> Sources: reddit_course_selection.txt, reddit_best_professors.txt
>
> **Retrieved from:**
> • reddit_course_selection.txt
> • reddit_best_professors.txt

---

**Response 3 — out-of-scope refusal**

> **Query:** What is the price of a meal plan at Lakewood State?
>
> **Answer:** I don't have enough information in the documents to answer that reliably.
>
> **Retrieved from:**
> • rmp_hartley_data_structures.txt
> • rmp_lopez_machine_learning.txt
> • rmp_park_databases.txt
> • student_guide_cs_dept.txt
> • reddit_course_selection.txt

The system retrieved documents (because ChromaDB always returns k results) but the LLM correctly identified that none of the retrieved chunks contained anything about meal plan pricing and declined to answer rather than generating a plausible-sounding fabrication.

---

## Query Interface

**Tool used:** Gradio (`app.py`) — run with `python app.py`, opens at `http://localhost:7860`

**Input fields:**
- **Your question** — a free-text box where the user types a plain-language question about CS professors or courses. Pressing Enter or clicking "Ask" submits it. Eight pre-written example questions are shown below the input for quick testing.

**Output fields:**
- **Answer** — the LLM-generated response, grounded in retrieved documents. Ends with a `Sources:` line listing the filenames cited.
- **Retrieved from** — a separate box showing which documents were pulled from the vector store (one bullet per unique source file).

**Sample interaction transcript:**

```
User input:  What do students say about office hours in Computer Networks?

Answer:      Students praise Prof. Novak's office hours in Computer Networks,
             saying they are the best they've experienced at Lakewood State
             University. She works through problems step by step, never makes
             students feel stupid, and stays past scheduled time to answer
             questions. Even with a queue system in place due to high demand,
             she ensures every student's questions are addressed.

             Sources: rmp_novak_networks.txt, student_guide_cs_dept.txt

Retrieved from:
             • rmp_chen_algorithms.txt
             • student_guide_cs_dept.txt
             • rmp_novak_networks.txt
             • student_guide_cs_dept.txt
             • rmp_novak_networks.txt
```

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
