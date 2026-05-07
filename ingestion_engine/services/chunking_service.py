import re
from abc import ABC, abstractmethod

from ingestion_engine.config import settings


class ChunkingStrategy(ABC):

    @abstractmethod
    def chunk(self, text: str) -> list[str]:
        ...


class WordChunker(ChunkingStrategy):
    """
    Splits text by raw word count with overlap.
    Fast and simple. Default strategy.
    Weakness: can split mid-sentence at chunk boundaries.
    """

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


class SentenceChunker(ChunkingStrategy):
    """
    Splits text on sentence boundaries before grouping into chunks.
    Produces cleaner, more semantically complete chunks than WordChunker.
    Better for retrieval — sentences are not cut mid-clause.

    Use in eval to compare against WordChunker:
        chunker = ChunkingService(strategy=SentenceChunker())
    """

    def __init__(self, size: int = None, overlap: int = None):
        self.size = size or settings.chunk_size
        self.overlap = overlap or settings.chunk_overlap
        self._splitter = re.compile(r"(?<=[.!?])\s+")

    def chunk(self, text: str) -> list[str]:
        sentences = [s.strip() for s in self._splitter.split(text) if s.strip()]

        chunks = []
        current_words: list[str] = []

        for sentence in sentences:
            sentence_words = sentence.split()

            if current_words and len(current_words) + len(sentence_words) > self.size:
                chunks.append(" ".join(current_words))
                current_words = current_words[-self.overlap:] if self.overlap else []

            current_words.extend(sentence_words)

        if current_words:
            chunks.append(" ".join(current_words))

        return chunks


class ChunkingService:

    def __init__(self, strategy: ChunkingStrategy = None):
        self.strategy = strategy or WordChunker()

    def chunk_text(self, text: str) -> list[str]:
        return self.strategy.chunk(text)
