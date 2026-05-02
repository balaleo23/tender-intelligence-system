from abc import ABC, abstractmethod

from ingestion_engine.config import settings


class ChunkingStrategy(ABC):

    @abstractmethod
    def chunk(self, text: str) -> list[str]:
        ...


class WordChunker(ChunkingStrategy):

    def __init__(self, size: int = None, overlap: int = None):
        self.size = size or settings.chunk_size
        self.overlap = overlap or settings.chunk_overlap

    def chunk(self, text: str) -> list[str]:
        words = text.split()
        chunks = []
        start = 0
        while start < len(words):
            end = start + self.size
            chunks.append(" ".join(words[start:end]))
            start = end - self.overlap
        return chunks


class ChunkingService:

    def __init__(self, strategy: ChunkingStrategy = None):
        self.strategy = strategy or WordChunker()

    def chunk_text(self, text: str) -> list[str]:
        return self.strategy.chunk(text)
