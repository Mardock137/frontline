"""Abstract interface for embedding providers.

Every concrete embedding adapter (Voyage AI, OpenAI, Cohere, ...) must
implement this interface so the rest of the codebase can swap providers
without changes.
"""

from abc import ABC, abstractmethod


class BaseEmbeddingInterface(ABC):
    """Uniform contract shared by every embedding integration."""

    def __init__(self, model: str, dimension: int) -> None:
        self.model = model
        self.dimension = dimension

    @abstractmethod
    async def embed(
        self,
        texts: list[str],
        *,
        input_type: str = "document",
    ) -> list[list[float]]:
        """Return one embedding vector for each input text.

        Args:
            texts: List of non-empty strings to embed.
            input_type: ``"document"`` when embedding chunks to store, or
                ``"query"`` when embedding a user query. Some providers
                (Voyage included) produce different vectors for these two
                cases, so the distinction matters for retrieval quality.

        Returns:
            A list of vectors with ``len(result) == len(texts)`` and
            ``len(vector) == self.dimension`` for each vector.
        """
        raise NotImplementedError
