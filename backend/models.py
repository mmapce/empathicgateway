from pydantic import BaseModel, Field
from typing import Optional, Dict, List

class ChatRequest(BaseModel):
    text: str = Field(..., max_length=512, description="User query text, limited to 512 chars")
    user_id: Optional[str] = "anonymous"

class ChatResponse(BaseModel):
    ticket_id: str
    priority: int
    label: str
    wait_time: str
    message: str
    confidence: float
    pii_detected: bool
    pii_types: List[str] = []  # New: List of detected PII types
    intent: str # Added for Explainability
    explainability: Dict[str, float] = {}
