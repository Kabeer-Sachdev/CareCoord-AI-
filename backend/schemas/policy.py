from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class PolicySourceItem(BaseModel):
    document_id: str
    document_name: str
    department: str = "General"
    page_number: Optional[int] = None
    chunk_index: int = 0
    similarity_score: float = 0.0
    content_snippet: str

class PolicyAskRequest(BaseModel):
    query: str = Field(..., min_length=3, description="Policy question to search and answer")
    department: Optional[str] = Field(None, description="Optional department filter")
    top_k: Optional[int] = Field(4, ge=1, le=10, description="Number of chunks to retrieve")

class PolicyAskResponse(BaseModel):
    query: str
    answer: str
    sources: List[PolicySourceItem] = []
    confidence_score: float = 0.0
    retrieval_count: int = 0
    insufficient_information: bool = False
    department: Optional[str] = None
    execution_time_ms: float = 0.0

class PolicyChunkResponse(BaseModel):
    chunk_id: str
    document_id: str
    chunk_index: int
    content: str
    token_count: int
    page_number: Optional[int] = None
    section_header: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class PolicyDocumentResponse(BaseModel):
    id: int
    document_id: str
    title: str
    filename: str
    file_type: str
    department: str
    status: str
    chunk_count: int
    file_size_bytes: int
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
