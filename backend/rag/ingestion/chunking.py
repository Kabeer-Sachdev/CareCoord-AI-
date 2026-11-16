from typing import List, Dict, Any
import re

class DocumentChunker:
    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 150):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_pages(self, pages: List[Dict[str, Any]], metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Splits pages into overlapping chunks while preserving metadata.
        pages: [{"text": str, "page_number": int}]
        metadata: {"document_id": str, "document_name": str, "department": str}
        """
        chunks = []
        chunk_index = 0

        for page in pages:
            text = page.get("text", "")
            page_number = page.get("page_number", 1)

            if not text.strip():
                continue

            page_chunks = self._split_text(text)
            for chunk_text in page_chunks:
                clean_chunk = chunk_text.strip()
                if len(clean_chunk) < 20:
                    continue

                # Detect header/title if present (e.g., first line)
                lines = [l.strip() for l in clean_chunk.split("\n") if l.strip()]
                section_header = lines[0][:100] if lines else None

                chunks.append({
                    "chunk_id": f"{metadata.get('document_id', 'DOC')}-CHK-{chunk_index + 1:04d}",
                    "document_id": metadata.get("document_id"),
                    "document_name": metadata.get("document_name"),
                    "department": metadata.get("department", "General"),
                    "chunk_index": chunk_index,
                    "content": clean_chunk,
                    "token_count": len(clean_chunk.split()),
                    "page_number": page_number,
                    "section_header": section_header
                })
                chunk_index += 1

        return chunks

    def _split_text(self, text: str) -> List[str]:
        """
        Splits text into chunks of roughly `chunk_size` characters with `chunk_overlap`.
        Tries to break at paragraph or sentence boundaries.
        """
        if len(text) <= self.chunk_size:
            return [text]

        chunks = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = start + self.chunk_size
            if end >= text_len:
                chunks.append(text[start:])
                break

            # Try to find a paragraph break
            slice_window = text[start:end]
            p_break = slice_window.rfind("\n\n")
            if p_break != -1 and p_break > self.chunk_size // 2:
                split_point = start + p_break + 2
            else:
                # Try to find sentence break
                s_break = max(slice_window.rfind(". "), slice_window.rfind(".\n"), slice_window.rfind("? "), slice_window.rfind("! "))
                if s_break != -1 and s_break > self.chunk_size // 3:
                    split_point = start + s_break + 2
                else:
                    # Fallback to whitespace
                    w_break = slice_window.rfind(" ")
                    if w_break != -1 and w_break > self.chunk_size // 4:
                        split_point = start + w_break + 1
                    else:
                        split_point = end

            chunks.append(text[start:split_point])
            start = max(start + 1, split_point - self.chunk_overlap)

        return chunks
