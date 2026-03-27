from functools import lru_cache

from sentence_transformers import SentenceTransformer

from app.core.config import get_settings


class EmbeddingService:
    # This service owns model loading and text-to-vector conversion.
    def __init__(self, model_name: str) -> None:
        self._model_name = model_name
        self._model: SentenceTransformer | None = None

    def _load_model(self) -> SentenceTransformer:
        # We lazily load the model so app startup stays fast and the model is loaded only when needed.
        if self._model is None:
            self._model = SentenceTransformer(self._model_name)
        return self._model

    def embed_text(self, text: str) -> list[float]:
        # We generate a single dense embedding vector for the input text.
        model = self._load_model()
        vector = model.encode(text, convert_to_numpy=True)
        return vector.astype(float).tolist()

@lru_cache
def get_embedding_service() -> EmbeddingService:
    # We cache one service instance so the model is reused across requests in the same process.
    settings = get_settings()
    return EmbeddingService(model_name=settings.embedding_model_name)
