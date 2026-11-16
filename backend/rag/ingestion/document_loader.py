import os
from typing import List, Dict, Any

class DocumentLoader:
    @staticmethod
    def load_document(file_path: str) -> List[Dict[str, Any]]:
        """
        Loads document content and returns a list of pages/sections with text and page numbers.
        Returns: [{"text": str, "page_number": int}]
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()

        if ext == ".pdf":
            return DocumentLoader._load_pdf(file_path)
        elif ext == ".docx":
            return DocumentLoader._load_docx(file_path)
        elif ext in [".txt", ".md"]:
            return DocumentLoader._load_txt(file_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}. Supported formats: .pdf, .docx, .txt")

    @staticmethod
    def _load_pdf(file_path: str) -> List[Dict[str, Any]]:
        import fitz  # PyMuPDF
        pages = []
        doc = fitz.open(file_path)
        try:
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text("text")
                if text.strip():
                    pages.append({
                        "text": text,
                        "page_number": page_num + 1
                    })
        finally:
            doc.close()
        return pages

    @staticmethod
    def _load_docx(file_path: str) -> List[Dict[str, Any]]:
        import docx
        doc = docx.Document(file_path)
        paragraphs = []
        for p in doc.paragraphs:
            if p.text.strip():
                paragraphs.append(p.text)
        
        # Group into pseudo-pages or single cohesive text
        full_text = "\n\n".join(paragraphs)
        return [{"text": full_text, "page_number": 1}] if full_text.strip() else []

    @staticmethod
    def _load_txt(file_path: str) -> List[Dict[str, Any]]:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
        return [{"text": text, "page_number": 1}] if text.strip() else []
