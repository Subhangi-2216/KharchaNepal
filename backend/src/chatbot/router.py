# backend/src/chatbot/router.py
import re
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

# Assuming User model might be needed if chatbot becomes user-aware later
from models import User
from src.auth.dependencies import get_current_active_user # Keep auth dependency for potential future use
from .schemas import ChatbotQuery, ChatbotResponse
# Import the new data structure and default response
from .faqs import (
    FAQ_KEYWORD_MAP,
    DEFAULT_RESPONSE,
    DATA_QUERY_KEYWORDS,      # Import new list
    REDIRECT_TO_EXPENSE_BOT_RESPONSE
)

router = APIRouter(
    prefix="/api/chatbot",
    tags=["Chatbot"],
    # Apply auth dependency, even if not strictly used by this specific endpoint yet
    dependencies=[Depends(get_current_active_user)],
    responses={404: {"description": "Not found"}},
)

# --- Pydantic Models ---
class ChatbotQuery(BaseModel):
    query: str = Field(..., min_length=1) # Ensure query is non-empty

class ChatbotResponse(BaseModel):
    response_type: str = "answer"
    data: str

# --- Helper Function ---
def clean_query(query: str) -> str:
    """Lowercase and remove basic punctuation for matching."""
    query = query.lower()
    query = re.sub(r'[^\w\s]', '', query) # Remove punctuation
    return query.strip()

# --- Endpoint ---
@router.post("/support", response_model=ChatbotResponse)
async def handle_support_query(
    payload: ChatbotQuery,
    # current_user: User = Depends(get_current_active_user) # Keep user dependency
):
    """Handles queries for the general support chatbot (Home Page).

    Prioritizes:
    1. Data-specific queries -> Redirect to Expense Chatbot
    2. Navigation/General queries -> Provide direct answer
    3. Fallback to default response
    """

    user_query = clean_query(payload.query)
    # We might need the full query for some checks, and words for others
    query_words = set(user_query.split())

    # 1. Check for Data Query Keywords (requiring specific data retrieval)
    for keyword in DATA_QUERY_KEYWORDS:
        # Check if keyword phrase appears in the full cleaned query
        if keyword in user_query:
            return ChatbotResponse(data=REDIRECT_TO_EXPENSE_BOT_RESPONSE)

    # 2. Check Navigation/General Keywords from FAQ map
    matched_response = None
    # Iterate through topics for clarity, though direct keyword matching is primary
    for topic, data in FAQ_KEYWORD_MAP.items():
        for keyword in data["keywords"]:
            # Check if keyword is a distinct word OR if it's part of the query string
            # (Handles single words like 'logout' and phrases like 'add expense')
            if keyword in query_words or keyword in user_query:
                matched_response = data["response"]
                break # Stop checking keywords for this topic
        if matched_response:
            break # Stop checking topics

    # 3. Return matched response or default
    if matched_response:
        return ChatbotResponse(data=matched_response)
    else:
        return ChatbotResponse(data=DEFAULT_RESPONSE)