from app.modules.chat.llm_client import generate_answer

SYSTEM_PROMPT = """You are a code assistant answering questions about a specific \
codebase. You are given a list of retrieved code components (name, type, file \
path, line numbers) found via semantic search — this is the ONLY information \
you know about this codebase. Do not invent, assume, or guess at code, files, \
or behavior not listed below.

Rules:
- If the retrieved components don't actually answer the question, say so \
plainly instead of guessing.
- Every claim you make about specific code must reference one of the given \
components by name and file path.
- Keep the answer concise — a few sentences, not an essay.
"""

NO_CONTEXT_ANSWER = (
    "I couldn't find anything in this repository's indexed code that looks "
    "relevant to that question. Try rephrasing, or make sure the repository "
    "has finished syncing."
)


def _format_context(matches: list[dict]) -> str:
    lines = []
    for m in matches:
        lines.append(
            f"- {m['type']} `{m['name']}` in {m['filePath']} "
            f"(lines {m['startLine']}-{m['endLine']}, similarity {m['similarity']:.2f})"
        )
    return "\n".join(lines)


def build_citations(matches: list[dict]) -> list[dict]:
    return [
        {
            "name": m["name"],
            "type": m["type"],
            "filePath": m["filePath"],
            "startLine": m["startLine"],
            "endLine": m["endLine"],
        }
        for m in matches
    ]


def answer_question(*, question: str, matches: list[dict]) -> dict:
    """Grounds an answer strictly in retrieved search matches — never calls
    the LLM at all if nothing relevant was retrieved, which is a stronger
    guarantee against fabricated citations than trusting the LLM to decline
    on its own when handed an empty context block."""
    if not matches:
        return {"answer": NO_CONTEXT_ANSWER, "citations": []}

    user_prompt = (
        f"Question: {question}\n\n"
        f"Retrieved code components:\n{_format_context(matches)}"
    )
    answer_text = generate_answer(system_prompt=SYSTEM_PROMPT, user_prompt=user_prompt)

    return {"answer": answer_text, "citations": build_citations(matches)}
