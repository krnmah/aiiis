from functools import lru_cache
import logging

from sentence_transformers import SentenceTransformer

from app.core.config import get_settings

logger = logging.getLogger("app.embeddings")


class EmbeddingService:
    # this service handles model loading and text-to-vector conversion.
    def __init__(self, model_name: str) -> None:
        self._model_name = model_name
        self._model: SentenceTransformer | None = None

    def _load_model(self) -> SentenceTransformer:
        # lazy load keeps startup fast and only loads model on first embedding request.
        if self._model is None:
            logger.info("embedding_model_load_started", extra={"model_name": self._model_name})
            self._model = SentenceTransformer(self._model_name)
            logger.info("embedding_model_load_complete", extra={"model_name": self._model_name})
        return self._model

    def embed_text(self, text: str) -> list[float]:
        # generate one dense embedding vector for this input text.
        model = self._load_model()
        vector = model.encode(text, convert_to_numpy=True)
        logger.info("embedding_generated", extra={"embedding_dimension": int(vector.shape[0])})
        return vector.astype(float).tolist()

@lru_cache
def get_embedding_service() -> EmbeddingService:
    # keep one cached instance so the same model is reused across requests.
    settings = get_settings()
    return EmbeddingService(model_name=settings.embedding_model_name)
