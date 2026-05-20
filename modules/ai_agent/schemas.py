from pydantic import BaseModel
from typing import Optional, List, Any


class AIChatRequest(BaseModel):
    message: str
    session_id: Optional[int] = None


class ToolLog(BaseModel):
    name: str
    args: dict
    result: Any


class AIChatResponse(BaseModel):
    session_id: int
    reply: str
    tool_calls: List[ToolLog] = []
