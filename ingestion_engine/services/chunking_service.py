class ChunkingService:

    @staticmethod
    def chunk_text(text: str, size=800, overlap=100) -> list[str]:
        words = text.split()
        chunks = []

        start = 0
        while start < len(words):
            end = start + size
            chunks.append(" ".join(words[start:end]))
            start = end - overlap

        return chunks
