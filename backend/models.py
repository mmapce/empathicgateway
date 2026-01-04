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
    pii_types: List[str] = []
    intent: str
    explainability: Dict[str, float] = {}

class ConfigRequest(BaseModel):
    fast_limit: Optional[int] = None
    normal_limit: Optional[int] = None

class StatsResponse(BaseModel):
    total_requests: int
    fast_lane_active: int
    normal_lane_active: int
    fast_lane_limit: int
    normal_lane_limit: int
