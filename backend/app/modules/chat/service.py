from app.modules.chat.rag import answer_question
from app.modules.search.service import search_workspace_code

# Cap retrieved components handed to the LLM: too few risks missing the
# actually-relevant one, too many wastes tokens (cost + latency) on
# marginally-similar matches that just add noise to the prompt.
DEFAULT_RETRIEVAL_LIMIT = 8


async def ask_question(*, workspace_id: str, question: str) -> dict:
    matches = await search_workspace_code(
        workspace_id=workspace_id, query=question, limit=DEFAULT_RETRIEVAL_LIMIT
    )
    return answer_question(question=question, matches=matches)
