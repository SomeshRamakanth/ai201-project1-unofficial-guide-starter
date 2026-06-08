"""
evaluate.py — run the 5 test questions and print a structured report.

Usage:
    python evaluate.py

Make sure you have run `python pipeline.py` first.
"""

from rag import query

TEST_CASES = [
    {
        "id": 1,
        "question": "Which CS professor gives the most useful feedback on assignments?",
        "expected": (
            "Prof. Sandra Chen (Algorithms, CS302). Multiple reviews describe detailed "
            "written comments explaining where reasoning broke down. Office hours are "
            "structured to guide thinking rather than give answers."
        ),
    },
    {
        "id": 2,
        "question": "How hard are exams in Data Structures with Hartley?",
        "expected": (
            "Hard. Hartley's exams require deep conceptual understanding — derivation "
            "questions, not memorization. Class averages around 65% before a curve. "
            "Students recommend doing every practice problem he posts."
        ),
    },
    {
        "id": 3,
        "question": "Which CS professor is the easiest grader?",
        "expected": (
            "Prof. Kevin Park (Database Systems, CS315). Reviews consistently describe "
            "it as an easy A with low weekly time commitment (~4-5 hrs). Grading is "
            "generous and he drops the lowest homework grade."
        ),
    },
    {
        "id": 4,
        "question": "How heavy is the workload in Machine Learning with Lopez?",
        "expected": (
            "Very heavy — ~15-16 hours per week. Weekly readings (including research "
            "papers), PyTorch coding assignments, and a substantial final project "
            "that occupies the last third of the semester. Students strongly advise "
            "not pairing it with another demanding course."
        ),
    },
    {
        "id": 5,
        "question": "What do students say about office hours in Computer Networks?",
        "expected": (
            "Novak's office hours are described as the best in the department. She "
            "works through problems step by step, stays late, and remembers each "
            "student's understanding from session to session. Office hours now use "
            "a queue system because demand is high."
        ),
    },
]

SEPARATOR = "=" * 72


def evaluate():
    print(SEPARATOR)
    print("THE UNOFFICIAL GUIDE — EVALUATION REPORT")
    print(SEPARATOR)

    for case in TEST_CASES:
        print(f"\nQ{case['id']}: {case['question']}")
        print("-" * 60)

        answer, chunks = query(case["question"])

        print(f"EXPECTED:\n{case['expected']}\n")
        print(f"SYSTEM RESPONSE:\n{answer}\n")

        print("RETRIEVED CHUNKS:")
        for i, chunk in enumerate(chunks, 1):
            snippet = chunk["text"][:120].replace("\n", " ")
            print(f"  [{i}] {chunk['source']} (dist={chunk['distance']:.4f}) — {snippet}...")

        print(SEPARATOR)


if __name__ == "__main__":
    evaluate()
