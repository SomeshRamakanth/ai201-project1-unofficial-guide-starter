"""
app.py — Gradio query interface for The Unofficial Guide.

Usage:
    python app.py

Make sure you have run `python pipeline.py` first to build the index.
"""

import gradio as gr
from rag import retrieve, generate


def ask(question: str) -> dict:
    """Retrieve chunks and generate a grounded answer. Returns {answer, sources}."""
    chunks = retrieve(question)
    answer = generate(question, chunks)
    sources = list(dict.fromkeys(c["source"] for c in chunks))  # unique, ordered
    return {"answer": answer, "sources": sources}


def handle_query(question: str):
    if not question.strip():
        return "", ""
    result = ask(question)
    sources_text = "\n".join(f"• {s}" for s in result["sources"])
    return result["answer"], sources_text


with gr.Blocks(title="The Unofficial Guide — Lakewood State CS") as demo:
    gr.Markdown(
        """
# The Unofficial Guide
### Student knowledge about CS professors & courses at Lakewood State University

Ask questions like:
- *"Which professor gives the most useful feedback?"*
- *"How hard are exams in Data Structures with Hartley?"*
- *"Which CS course has the lightest workload?"*
- *"What do students say about office hours in Computer Networks?"*
        """
    )

    inp = gr.Textbox(
        label="Your question",
        placeholder="Ask about CS professors or courses...",
        autofocus=True,
    )
    btn = gr.Button("Ask", variant="primary")
    answer = gr.Textbox(label="Answer", lines=10)
    sources = gr.Textbox(label="Retrieved from", lines=4)

    gr.Examples(
        examples=[
            "Which CS professor gives the most useful feedback on assignments?",
            "How hard are exams in Data Structures with Hartley?",
            "Which CS professor is the easiest grader?",
            "How heavy is the workload in Machine Learning with Lopez?",
            "What do students say about office hours in Computer Networks?",
            "Should I take Chen's Algorithms before Lopez's Machine Learning?",
            "What's the best course sequence for students interested in ML?",
            "Is Professor Park's databases class worth taking?",
        ],
        inputs=inp,
        label="Example questions",
    )

    btn.click(fn=handle_query, inputs=inp, outputs=[answer, sources])
    inp.submit(fn=handle_query, inputs=inp, outputs=[answer, sources])

    gr.Markdown(
        "_Answers are drawn from student reviews, Reddit threads, and the CS department "
        "survival guide. Always verify important decisions with official sources._"
    )

if __name__ == "__main__":
    demo.launch()
