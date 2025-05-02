# backend/src/chatbot/router.py
import re
import logging
from datetime import date
from decimal import Decimal
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

# Import models and dependencies
from models import User, Expense, CategoryEnum
from database import get_db
from src.auth.dependencies import get_current_active_user
from .schemas import ChatbotQuery, ChatbotResponse
# Import the new data structure and default response
from .faqs import (
    FAQ_KEYWORD_MAP,
    DEFAULT_RESPONSE,
    DATA_QUERY_KEYWORDS,      # Import new list
    REDIRECT_TO_EXPENSE_BOT_RESPONSE
)
# Import NLP service
from .nlp_service import parse_expense_query, INTENT_QUERY_SUM, INTENT_QUERY_LIST, INTENT_ADD_EXPENSE, INTENT_UNKNOWN
# Import TF-IDF service
from .tfidf_service import TfidfMatcher

# Initialize TF-IDF matcher
try:
    tfidf_matcher = TfidfMatcher(FAQ_KEYWORD_MAP)
    logging.info("TF-IDF matcher initialized successfully")
except Exception as e:
    logging.error(f"Error initializing TF-IDF matcher: {e}")
    tfidf_matcher = None

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

# --- Endpoints ---
@router.post("/support", response_model=ChatbotResponse)
async def handle_support_query(
    payload: ChatbotQuery,
    # current_user: User = Depends(get_current_active_user) # Keep user dependency
):
    """Handles queries for the general support chatbot (Home Page).

    Prioritizes:
    1. Data-specific queries -> Redirect to Expense Chatbot
    2. TF-IDF based matching for FAQ responses
    3. Keyword-based matching as fallback
    4. Default response if no match found
    """

    user_query = clean_query(payload.query)
    # We might need the full query for some checks, and words for others
    query_words = set(user_query.split())

    # 1. Check for Data Query Keywords (requiring specific data retrieval)
    for keyword in DATA_QUERY_KEYWORDS:
        # Check if keyword phrase appears in the full cleaned query
        if keyword in user_query:
            return ChatbotResponse(data=REDIRECT_TO_EXPENSE_BOT_RESPONSE)

    # 2. Try TF-IDF matching first (more robust)
    if tfidf_matcher:
        tfidf_match = tfidf_matcher.match(payload.query)
        if tfidf_match:
            response, score = tfidf_match
            logging.info(f"TF-IDF matched query '{payload.query}' with score {score:.2f}")
            return ChatbotResponse(data=response)
    
    # 3. Fall back to keyword matching if TF-IDF fails or is not available
    matched_response = None
    # Iterate through topics for clarity, though direct keyword matching is primary
    for topic, data in FAQ_KEYWORD_MAP.items():
        for keyword in data["keywords"]:
            # Check if keyword is a distinct word OR if it's part of the query string
            # (Handles single words like 'logout' and phrases like 'add expense')
            if keyword in query_words or keyword in user_query:
                matched_response = data["response"]
                logging.info(f"Keyword matched query '{payload.query}' to '{keyword}'")
                break # Stop checking keywords for this topic
        if matched_response:
            break # Stop checking topics

    # 4. Return matched response or default
    if matched_response:
        return ChatbotResponse(data=matched_response)
    else:
        logging.info(f"No match found for query '{payload.query}'")
        return ChatbotResponse(data=DEFAULT_RESPONSE)


@router.post("/query", response_model=ChatbotResponse)
async def handle_expense_query(
    payload: ChatbotQuery,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Handles queries for the expense chatbot.
    
    This endpoint:
    1. Parses the natural language query to extract intent and entities
    2. Performs database operations based on the intent
    3. Returns a structured response
    """
    try:
        # Parse the query using NLP service
        logging.info(f"Processing expense query: {payload.query}")
        parsed_result = parse_expense_query(payload.query)
        
        intent = parsed_result["intent"]
        entities = parsed_result["entities"]
        confidence = parsed_result["confidence"]
        
        logging.info(f"Parsed intent: {intent}, confidence: {confidence}")
        logging.info(f"Extracted entities: {entities}")
        
        # Check confidence threshold
        if confidence < 0.3:
            return ChatbotResponse(
                response_type="error",
                data="I'm not sure I understood your query. Could you please rephrase it?"
            )
        
        # Handle different intents
        if intent == INTENT_QUERY_SUM:
            return await handle_query_sum(db, current_user, entities)
        
        elif intent == INTENT_QUERY_LIST:
            return await handle_query_list(db, current_user, entities)
        
        elif intent == INTENT_ADD_EXPENSE:
            return await handle_add_expense(db, current_user, entities)
        
        else:
            return ChatbotResponse(
                response_type="error",
                data="I'm not sure what you're asking. Try asking about your expenses or adding a new expense."
            )
            
    except Exception as e:
        logging.error(f"Error processing expense query: {e}", exc_info=True)
        return ChatbotResponse(
            response_type="error",
            data="Sorry, I encountered an error processing your request."
        )


async def handle_query_sum(
    db: AsyncSession,
    current_user: User,
    entities: Dict[str, Any]
) -> ChatbotResponse:
    """Handle queries about expense totals."""
    try:
        # Build query based on entities
        query = select(func.sum(Expense.amount)).where(Expense.user_id == current_user.id)
        
        # Add date filters if present
        if "start_date" in entities:
            query = query.where(Expense.date >= entities["start_date"])
        if "end_date" in entities:
            query = query.where(Expense.date <= entities["end_date"])
        
        # Add category filter if present
        if "category" in entities:
            category_enum = getattr(CategoryEnum, entities["category"].upper(), None)
            if category_enum:
                query = query.where(Expense.category == category_enum)
        
        # Execute query
        result = await db.execute(query)
        total_amount = result.scalar_one_or_none() or Decimal('0.0')
        
        # Format response
        response_text = format_sum_response(total_amount, entities)
        
        return ChatbotResponse(
            response_type="answer",
            data=response_text
        )
    
    except Exception as e:
        logging.error(f"Error handling query_sum: {e}", exc_info=True)
        return ChatbotResponse(
            response_type="error",
            data="Sorry, I had trouble calculating your expenses."
        )


async def handle_query_list(
    db: AsyncSession,
    current_user: User,
    entities: Dict[str, Any]
) -> ChatbotResponse:
    """Handle queries about listing expenses."""
    try:
        # Build query based on entities
        query = select(Expense).where(Expense.user_id == current_user.id)
        
        # Add date filters if present
        if "start_date" in entities:
            query = query.where(Expense.date >= entities["start_date"])
        if "end_date" in entities:
            query = query.where(Expense.date <= entities["end_date"])
        
        # Add category filter if present
        if "category" in entities:
            category_enum = getattr(CategoryEnum, entities["category"].upper(), None)
            if category_enum:
                query = query.where(Expense.category == category_enum)
        
        # Order by date (most recent first) and limit to 5 expenses
        query = query.order_by(Expense.date.desc()).limit(5)
        
        # Execute query
        result = await db.execute(query)
        expenses = result.scalars().all()
        
        # Format response
        response_text = format_list_response(expenses, entities)
        
        return ChatbotResponse(
            response_type="answer",
            data=response_text
        )
    
    except Exception as e:
        logging.error(f"Error handling query_list: {e}", exc_info=True)
        return ChatbotResponse(
            response_type="error",
            data="Sorry, I had trouble retrieving your expenses."
        )


async def handle_add_expense(
    db: AsyncSession,
    current_user: User,
    entities: Dict[str, Any]
) -> ChatbotResponse:
    """Handle requests to add a new expense."""
    try:
        # Check for required fields
        if "amount" not in entities:
            return ChatbotResponse(
                response_type="error",
                data="I need an amount to add an expense. Please specify how much you spent."
            )
        
        # Set defaults for missing fields
        expense_date = entities.get("start_date", date.today())
        merchant_name = entities.get("merchant", "Unknown Merchant")
        
        # Handle category
        category_str = entities.get("category", "Other")
        try:
            category_enum = getattr(CategoryEnum, category_str.upper())
        except AttributeError:
            category_enum = CategoryEnum.OTHER
        
        # Create expense object
        expense = Expense(
            user_id=current_user.id,
            date=expense_date,
            merchant_name=merchant_name,
            amount=entities["amount"],
            currency="NPR",  # Default currency
            category=category_enum,
            is_ocr_entry=False  # Manual entry via chatbot
        )
        
        # Save to database
        db.add(expense)
        await db.commit()
        await db.refresh(expense)
        
        # Format confirmation message
        response_text = (
            f"Expense added successfully! "
            f"NPR {expense.amount} for {expense.category.value} "
            f"at {expense.merchant_name} on {expense.date.strftime('%Y-%m-%d')}."
        )
        
        return ChatbotResponse(
            response_type="confirmation",
            data=response_text
        )
    
    except Exception as e:
        await db.rollback()
        logging.error(f"Error handling add_expense: {e}", exc_info=True)
        return ChatbotResponse(
            response_type="error",
            data="Sorry, I couldn't add your expense. Please try again."
        )


def format_sum_response(total_amount: Decimal, entities: Dict[str, Any]) -> str:
    """Format the response for sum queries."""
    # Start with the total amount
    response = f"You spent NPR {total_amount:.2f}"
    
    # Add category if present
    if "category" in entities:
        response += f" on {entities['category']}"
    
    # Add date range if present
    if "start_date" in entities and "end_date" in entities:
        if entities["start_date"] == entities["end_date"]:
            response += f" on {entities['start_date'].strftime('%Y-%m-%d')}"
        else:
            response += (f" from {entities['start_date'].strftime('%Y-%m-%d')} "
                        f"to {entities['end_date'].strftime('%Y-%m-%d')}")
    elif "start_date" in entities:
        response += f" since {entities['start_date'].strftime('%Y-%m-%d')}"
    elif "end_date" in entities:
        response += f" until {entities['end_date'].strftime('%Y-%m-%d')}"
    
    response += "."
    return response


def format_list_response(expenses: List[Expense], entities: Dict[str, Any]) -> str:
    """Format the response for list queries."""
    if not expenses:
        # No expenses found
        response = "I couldn't find any expenses"
        
        # Add category if present
        if "category" in entities:
            response += f" for {entities['category']}"
        
        # Add date range if present
        if "start_date" in entities and "end_date" in entities:
            if entities["start_date"] == entities["end_date"]:
                response += f" on {entities['start_date'].strftime('%Y-%m-%d')}"
            else:
                response += (f" from {entities['start_date'].strftime('%Y-%m-%d')} "
                            f"to {entities['end_date'].strftime('%Y-%m-%d')}")
        elif "start_date" in entities:
            response += f" since {entities['start_date'].strftime('%Y-%m-%d')}"
        elif "end_date" in entities:
            response += f" until {entities['end_date'].strftime('%Y-%m-%d')}"
        
        response += "."
        return response
    
    # Format header
    response = "Here are your recent expenses"
    
    # Add category if present
    if "category" in entities:
        response += f" for {entities['category']}"
    
    # Add date range if present
    if "start_date" in entities and "end_date" in entities:
        if entities["start_date"] == entities["end_date"]:
            response += f" on {entities['start_date'].strftime('%Y-%m-%d')}"
        else:
            response += (f" from {entities['start_date'].strftime('%Y-%m-%d')} "
                        f"to {entities['end_date'].strftime('%Y-%m-%d')}")
    elif "start_date" in entities:
        response += f" since {entities['start_date'].strftime('%Y-%m-%d')}"
    elif "end_date" in entities:
        response += f" until {entities['end_date'].strftime('%Y-%m-%d')}"
    
    response += ":\n\n"
    
    # Add expense list
    for expense in expenses:
        response += (f"- {expense.date.strftime('%Y-%m-%d')}: "
                    f"NPR {expense.amount:.2f} for {expense.category.value} "
                    f"at {expense.merchant_name}\n")
    
    return response