from app.modules.chat.rag import NO_CONTEXT_ANSWER, answer_question, build_citations


def test_answer_question_returns_fallback_when_no_matches():
    result = answer_question(question="how does auth work", matches=[])

    assert result["answer"] == NO_CONTEXT_ANSWER
    assert result["citations"] == []


def test_build_citations_extracts_only_public_fields():
    matches = [
        {
            "id": "repo:file.py:function:foo",
            "repositoryId": "repo",
            "filePath": "file.py",
            "name": "foo",
            "type": "function",
            "startLine": 1,
            "endLine": 3,
            "similarity": 0.9,
        }
    ]

    citations = build_citations(matches)

    assert citations == [
        {
            "name": "foo",
            "type": "function",
            "filePath": "file.py",
            "startLine": 1,
            "endLine": 3,
        }
    ]


def test_answer_question_calls_llm_and_grounds_answer_in_real_matches():
    """Real integration test against the live Groq API — no mocking. Confirms
    the LLM actually receives and uses the retrieved context, not just that
    the plumbing compiles."""
    matches = [
        {
            "id": "repo:app/core/security.py:function:verify_password",
            "repositoryId": "repo",
            "filePath": "app/core/security.py",
            "name": "verify_password",
            "type": "function",
            "startLine": 10,
            "endLine": 12,
            "similarity": 0.83,
        }
    ]

    result = answer_question(question="how do we check a user's password?", matches=matches)

    assert "verify_password" in result["answer"]
    assert result["citations"] == build_citations(matches)
