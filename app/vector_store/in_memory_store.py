from functools import lru_cache


class InMemoryEmbeddingStore:
    # This temporary store keeps embeddings in process memory until pgvector is added later.
    def __init__(self) -> None:
        self._data: dict[int, list[float]] = {}

    def upsert(self, log_id: int, embedding: list[float]) -> None:
        # save/update the embedding by log id for quick retrieval during development.
        self._data[log_id] = embedding

    def get(self, log_id: int) -> list[float] | None:
        # return None when an embedding is not found for the requested log id.
        return self._data.get(log_id)


@lru_cache
def get_embedding_store() -> InMemoryEmbeddingStore:
    # expose one shared in-memory store instance for the current app process.
    return InMemoryEmbeddingStore()
