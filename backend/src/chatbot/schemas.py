# backend/src/chatbot/schemas.py
from pydantic import BaseModel, Field

class ChatbotQuery(BaseModel):
    query: str = Field(..., min_length=1) # Ensure query is non-empty

class ChatbotResponse(BaseModel):
    response_type: str = "answer" # Default type
    data: str 