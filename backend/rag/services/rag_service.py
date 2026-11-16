import os
import uuid
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.database.models import PolicyDocument, PolicyChunk
from backend.rag.ingestion.document_loader import DocumentLoader
from backend.rag.ingestion.text_cleaner import TextCleaner
from backend.rag.ingestion.chunking import DocumentChunker
from backend.rag.retrieval.vector_store import vector_store
from backend.rag.prompts.policy_prompt import build_policy_prompt
from backend.schemas.policy import PolicyAskResponse, PolicySourceItem

class RAGService:
    def __init__(self):
        self.chunker = DocumentChunker(chunk_size=800, chunk_overlap=150)
        self.vector_store = vector_store

    def ingest_document(
        self,
        file_path: str,
        title: str,
        department: str,
        db: Session,
        document_id: Optional[str] = None
    ) -> PolicyDocument:
        """
        Full ingestion pipeline:
        1. Validate file
        2. Extract text & pages
        3. Clean text
        4. Chunk with metadata
        5. Upsert to ChromaDB
        6. Save metadata and chunks to SQLite
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Document file not found: {file_path}")

        file_size = os.path.getsize(file_path)
        filename = os.path.basename(file_path)
        ext = os.path.splitext(filename)[1].lower().lstrip(".")

        doc_id = document_id or f"DOC-{uuid.uuid4().hex[:8].upper()}"

        # Fetch or create PolicyDocument in SQLite
        doc_record = db.query(PolicyDocument).filter(PolicyDocument.document_id == doc_id).first()
        if not doc_record:
            doc_record = PolicyDocument(
                document_id=doc_id,
                title=title or filename,
                filename=filename,
                file_path=file_path,
                file_type=ext.upper(),
                department=department or "General",
                status="PROCESSING",
                chunk_count=0,
                file_size_bytes=file_size
            )
            db.add(doc_record)
            db.commit()
            db.refresh(doc_record)
        else:
            doc_record.status = "PROCESSING"
            doc_record.title = title or doc_record.title
            doc_record.department = department or doc_record.department
            doc_record.file_size_bytes = file_size
            doc_record.updated_at = datetime.utcnow()
            db.commit()

        try:
            # 1. Extract text and pages
            raw_pages = DocumentLoader.load_document(file_path)
            if not raw_pages:
                raise ValueError("No text could be extracted from document.")

            # 2. Clean each page
            cleaned_pages = []
            for p in raw_pages:
                cleaned = TextCleaner.clean(p["text"])
                if cleaned:
                    cleaned_pages.append({
                        "text": cleaned,
                        "page_number": p.get("page_number", 1)
                    })

            # 3. Chunk pages
            metadata = {
                "document_id": doc_id,
                "document_name": doc_record.title,
                "department": doc_record.department
            }
            chunks = self.chunker.chunk_pages(cleaned_pages, metadata)
            if not chunks:
                raise ValueError("Document yielded 0 valid text chunks after chunking.")

            # 4. Clean up any previous chunks in Chroma and SQLite
            self.vector_store.delete_by_document_id(doc_id)
            db.query(PolicyChunk).filter(PolicyChunk.document_id == doc_id).delete()
            db.commit()

            # 5. Insert chunks into Chroma
            self.vector_store.add_chunks(chunks)

            # 6. Insert chunks into SQLite
            for c in chunks:
                db_chunk = PolicyChunk(
                    chunk_id=c["chunk_id"],
                    document_id=doc_id,
                    chunk_index=c["chunk_index"],
                    content=c["content"],
                    token_count=c["token_count"],
                    page_number=c.get("page_number"),
                    section_header=c.get("section_header"),
                    chroma_id=c["chunk_id"]
                )
                db.add(db_chunk)

            # 7. Update document status
            doc_record.status = "INDEXED"
            doc_record.chunk_count = len(chunks)
            doc_record.error_message = None
            doc_record.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(doc_record)

            return doc_record

        except Exception as e:
            db.rollback()
            doc_record.status = "FAILED"
            doc_record.error_message = str(e)
            doc_record.updated_at = datetime.utcnow()
            db.commit()
            raise e

    def delete_document(self, document_id: str, db: Session) -> bool:
        """
        Removes document from ChromaDB and SQLite.
        """
        doc = db.query(PolicyDocument).filter(PolicyDocument.document_id == document_id).first()
        if not doc:
            return False

        # Delete from Chroma
        self.vector_store.delete_by_document_id(document_id)

        # Delete from SQLite (cascades to PolicyChunk)
        db.delete(doc)
        db.commit()
        return True

    def ask_policy(
        self,
        query: str,
        department: Optional[str] = None,
        top_k: int = 4
    ) -> PolicyAskResponse:
        """
        Retrieves grounded policy context and synthesizes an accurate answer.
        """
        start_time = time.time()
        
        # 1. Semantic Retrieval
        chunks = self.vector_store.query(query, top_k=top_k, department=department)

        # 2. Similarity and sufficiency check
        # Chroma L2 similarity score: 1 / (1 + distance). A score >= 0.48 indicates strong semantic relevance.
        min_relevance_threshold = 0.48
        relevant_chunks = [c for c in chunks if c.get("similarity_score", 0) >= min_relevance_threshold]

        if not relevant_chunks:
            exec_time = round((time.time() - start_time) * 1000, 2)
            return PolicyAskResponse(
                query=query,
                answer="The available hospital policy documents do not contain sufficient information to answer this question. Please contact the Hospital Administration or relevant Department Head for operational clarification.",
                sources=[],
                confidence_score=chunks[0]["similarity_score"] if chunks else 0.0,
                retrieval_count=0,
                insufficient_information=True,
                department=department,
                execution_time_ms=exec_time
            )

        # 3. Format source citations
        sources = []
        for c in relevant_chunks:
            sources.append(PolicySourceItem(
                document_id=c.get("document_id", ""),
                document_name=c.get("document_name", "Policy Document"),
                department=c.get("department", "General"),
                page_number=c.get("page_number"),
                chunk_index=c.get("chunk_index", 0),
                similarity_score=c.get("similarity_score", 0.0),
                content_snippet=c.get("content", "")[:250] + "..." if len(c.get("content", "")) > 250 else c.get("content", "")
            ))

        # 4. Generate Grounded Answer via LLM or Grounded Synthesizer
        answer = self._generate_answer(query, relevant_chunks)
        confidence = round(sum(c["similarity_score"] for c in relevant_chunks) / len(relevant_chunks), 3)
        exec_time = round((time.time() - start_time) * 1000, 2)

        return PolicyAskResponse(
            query=query,
            answer=answer,
            sources=sources,
            confidence_score=confidence,
            retrieval_count=len(relevant_chunks),
            insufficient_information=False,
            department=department,
            execution_time_ms=exec_time
        )

    def _generate_answer(self, query: str, chunks: List[Dict[str, Any]]) -> str:
        """
        Invokes local Ollama (qwen2.5:3b) with grounded prompt, or falls back to grounded extraction.
        """
        try:
            from backend.services.llm_client import llm_client
            if llm_client.is_ollama_available(timeout=1.0):
                prompt = build_policy_prompt(query, chunks)
                system_msg = (
                    "You are CareCoord's Hospital Policy Agent. "
                    "Answer the user query strictly using the provided hospital policy excerpts. "
                    "Include citations such as [Document: ..., Page ...]. "
                    "Do NOT give clinical diagnosis, medical treatment, or invent hospital rules."
                )
                llm_text = llm_client.generate(
                    prompt=prompt,
                    system_prompt=system_msg,
                    temperature=0.2,
                    timeout=6
                )
                if llm_text and len(llm_text.strip()) > 10:
                    return llm_text.strip()
        except Exception:
            pass

        # Robust Grounded Synthesizer for offline / testing / fallback (<0.05s)
        return self._synthesize_grounded_answer(query, chunks)

    def _synthesize_grounded_answer(self, query: str, chunks: List[Dict[str, Any]]) -> str:
        """
        Deterministic, grounded extraction from top chunks with strict citations.
        """
        query_words = set(query.lower().replace("?", "").replace(".", "").split())
        # Filter stop words
        stop_words = {"what", "is", "the", "how", "are", "do", "for", "in", "to", "of", "and", "a", "an", "can", "i"}
        keywords = query_words - stop_words

        primary_chunk = chunks[0]
        doc_name = primary_chunk.get("document_name", "Policy Document")
        dept = primary_chunk.get("department", "General")
        page = f"Page {primary_chunk.get('page_number')}" if primary_chunk.get('page_number') else "Section 1"

        # Find best matching sentences across top chunks
        matching_sentences = []
        for c in chunks[:2]:
            content = c.get("content", "")
            sentences = [s.strip() for s in content.replace("\n", " ").split(".") if s.strip()]
            for s in sentences:
                s_words = set(s.lower().split())
                overlap = len(keywords.intersection(s_words))
                if overlap >= 1:
                    matching_sentences.append((overlap, s))

        matching_sentences.sort(key=lambda x: x[0], reverse=True)
        if matching_sentences:
            selected_facts = ". ".join([s[1] for s in matching_sentences[:4]]) + "."
            answer_text = (
                f"According to the **{doc_name}** ({dept}, {page}):\n\n"
                f"{selected_facts}\n\n"
                f"*Source: {doc_name} [{dept}]*"
            )
        else:
            first_paras = primary_chunk.get("content", "").strip()[:400]
            answer_text = (
                f"According to the **{doc_name}** ({dept}, {page}):\n\n"
                f"{first_paras}...\n\n"
                f"*Source: {doc_name} [{dept}]*"
            )

        return answer_text

# Global singleton instance
rag_service = RAGService()
