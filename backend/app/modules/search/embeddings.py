from functools import lru_cache

from sentence_transformers import SentenceTransformer

# all-MiniLM-L6-v2: small (~80MB), fast on CPU, 384-dim vectors. Free, runs
# entirely locally — no API key, no per-call cost, no rate limit. Chosen over
# a larger model because ingestion needs to embed every function/class in a
# repository; a bigger model would be more accurate but too slow for that
# volume on a laptop CPU with no GPU. Explicit choice, not Chroma's implicit
# default, so upgrading this later is a one-line change in one place.
MODEL_NAME = "all-MiniLM-L6-v2"


@lru_cache
def _get_model() -> SentenceTransformer:
    # Loaded once per process and reused — loading the model (reading weights
    # off disk) is the slow part, not running it, so this must not happen
    # per-call.
    return SentenceTransformer(MODEL_NAME)


def component_to_text(*, name: str, type_: str, file_path: str, imports: list[str]) -> str:
    """Turns a parsed component's structured fields into one string worth
    embedding. Deliberately includes the file path and type as words, not
    just the bare identifier — 'validate_token' alone is ambiguous, but
    'function validate_token in app/core/security.py' embeds closer to a
    query like 'where do we check if a JWT is valid'."""
    import_hint = f" imports: {', '.join(imports[:5])}" if imports else ""
    return f"{type_} {name} in {file_path}{import_hint}"


def embed_text(text: str) -> list[float]:
    return _get_model().encode(text, normalize_embeddings=True).tolist()


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    return _get_model().encode(texts, normalize_embeddings=True).tolist()
