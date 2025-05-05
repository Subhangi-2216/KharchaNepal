# backend/src/chatbot/router.py
import re
import logging
import difflib
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any, Tuple, Set

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
    DATA_QUERY_KEYWORDS,
    EXPENSE_RELATED_KEYWORDS,
    REDIRECT_TO_EXPENSE_BOT_RESPONSE
)
# Import NLP service with confidence thresholds
from .nlp_service import (
    parse_expense_query,
    INTENT_QUERY_SUM,
    INTENT_QUERY_LIST,
    INTENT_ADD_EXPENSE,
    INTENT_UNKNOWN,
    HIGH_CONFIDENCE,
    MEDIUM_CONFIDENCE,
    LOW_CONFIDENCE,
    VERY_LOW_CONFIDENCE
)
# Import enhanced TF-IDF service
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
    2. Enhanced TF-IDF based matching for FAQ responses
    3. Keyword-based matching as fallback
    4. Fuzzy matching for handling typos
    5. Default response if no match found
    """
    # Log the incoming query
    logging.info(f"Support chatbot received query: '{payload.query}'")

    # Clean the query for basic checks
    user_query = clean_query(payload.query)
    query_words = set(user_query.split())

    # 1. Check for Data Query Keywords (requiring specific data retrieval)
    for keyword in DATA_QUERY_KEYWORDS:
        # Check if keyword phrase appears in the full cleaned query
        if keyword in user_query:
            logging.info(f"Redirecting to Expense Chatbot due to data query keyword: '{keyword}'")
            return ChatbotResponse(
                response_type="redirect",
                data=REDIRECT_TO_EXPENSE_BOT_RESPONSE
            )

    # 2. Check for expense-related keywords that should be handled by the Expense Chatbot
    expense_keywords_count = 0
    for keyword in EXPENSE_RELATED_KEYWORDS:
        if keyword in user_query:
            expense_keywords_count += 1

    # If multiple expense-related keywords are found, redirect to Expense Chatbot
    if expense_keywords_count >= 2:
        logging.info(f"Redirecting to Expense Chatbot due to multiple expense-related keywords: {expense_keywords_count}")
        return ChatbotResponse(
            response_type="redirect",
            data=REDIRECT_TO_EXPENSE_BOT_RESPONSE
        )

    # 3. Try enhanced TF-IDF matching (with multiple strategies)
    if tfidf_matcher:
        try:
            match_result = tfidf_matcher.match(payload.query)
            if match_result:
                response, confidence = match_result

                # Log detailed match information
                logging.info(f"Matched query '{payload.query}' with confidence {confidence:.2f}")

                return ChatbotResponse(
                    response_type="answer",
                    data=response
                )
        except Exception as e:
            logging.error(f"Error in TF-IDF matching: {e}")

    # 4. Fall back to simple keyword matching if TF-IDF fails or is not available
    matched_response = None
    best_match_keyword = None

    # Iterate through topics for clarity
    for topic, data in FAQ_KEYWORD_MAP.items():
        for keyword in data["keywords"]:
            # Check if keyword is a distinct word OR if it's part of the query string
            if keyword in query_words or keyword in user_query:
                matched_response = data["response"]
                best_match_keyword = keyword
                logging.info(f"Keyword matched query '{payload.query}' to '{keyword}'")
                break  # Stop checking keywords for this topic
        if matched_response:
            break  # Stop checking topics

    # 5. Return matched response or default
    if matched_response:
        return ChatbotResponse(
            response_type="answer",
            data=matched_response
        )
    else:
        logging.info(f"No match found for query '{payload.query}'")
        return ChatbotResponse(
            response_type="no_match",
            data=DEFAULT_RESPONSE
        )


@router.post("/query", response_model=ChatbotResponse)
async def handle_expense_query(
    payload: ChatbotQuery,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Handles queries for the expense chatbot.

    This endpoint:
    1. Parses the natural language query to extract intent and entities with confidence scores
    2. Performs database operations based on the intent
    3. Returns a structured response with detailed information
    """
    try:
        # Log the incoming query
        logging.info(f"Expense chatbot received query: '{payload.query}'")

        # Parse the query using enhanced NLP service
        parsed_result = parse_expense_query(payload.query)

        # Extract key information
        intent = parsed_result["intent"]
        entities = parsed_result["entities"]
        confidence = parsed_result["confidence"]
        confidence_level = parsed_result.get("confidence_level", "unknown")

        # Log detailed parsing results
        logging.info(f"Parsed intent: {intent}, confidence: {confidence:.2f} ({confidence_level})")
        logging.info(f"Extracted entities: {entities}")

        if "explanation" in parsed_result:
            logging.debug(f"Confidence explanation: {parsed_result['explanation']}")

        # Check for intent alternatives
        if "intent_alternatives" in parsed_result and parsed_result["intent_alternatives"]:
            alt_intent = parsed_result["intent_alternatives"][0]["intent"]
            alt_confidence = parsed_result["intent_alternatives"][0]["confidence"]
            logging.info(f"Alternative intent: {alt_intent}, confidence: {alt_confidence:.2f}")

        # Check confidence threshold
        if confidence < 0.3:
            # Provide more helpful error message based on what was understood
            error_message = "I'm not sure I understood your query. Could you please rephrase it?"

            # If we have some entities but low confidence, mention what was understood
            understood_parts = []

            if "amount" in entities:
                understood_parts.append(f"amount ({entities['amount']})")

            if "category" in entities:
                understood_parts.append(f"category ({entities['category']})")

            if "start_date" in entities:
                date_str = entities["start_date"].strftime("%Y-%m-%d")
                understood_parts.append(f"date ({date_str})")

            if "merchant" in entities:
                understood_parts.append(f"merchant ({entities['merchant']})")

            if understood_parts:
                error_message += f" I understood the following: {', '.join(understood_parts)}."

            return ChatbotResponse(
                response_type="error",
                data=error_message
            )

        # Handle different intents
        if intent == INTENT_QUERY_SUM:
            return await handle_query_sum(db, current_user, entities)

        elif intent == INTENT_QUERY_LIST:
            return await handle_query_list(db, current_user, entities)

        elif intent == INTENT_ADD_EXPENSE:
            return await handle_add_expense(db, current_user, entities)

        else:
            # Check if we have any entities that might help guide the user
            if entities:
                entity_types = []
                if "amount" in entities:
                    entity_types.append("amount")
                if "category" in entities:
                    entity_types.append("category")
                if "start_date" in entities:
                    entity_types.append("date")
                if "merchant" in entities:
                    entity_types.append("merchant")

                if entity_types:
                    return ChatbotResponse(
                        response_type="error",
                        data=f"I understood {', '.join(entity_types)} but I'm not sure what you want to do with this information. Try asking about your expenses or adding a new expense."
                    )

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
    """Handle queries about expense totals with improved error handling and response formatting."""
    try:
        # Log the query details
        logging.info(f"Handling sum query for user {current_user.id} with entities: {entities}")

        # Build query based on entities
        query = select(func.sum(Expense.amount)).where(Expense.user_id == current_user.id)

        # Track applied filters for better response formatting
        applied_filters = []

        # Add date filters if present
        if "start_date" in entities:
            query = query.where(Expense.date >= entities["start_date"])
            applied_filters.append(f"from {entities['start_date'].strftime('%Y-%m-%d')}")

        if "end_date" in entities:
            query = query.where(Expense.date <= entities["end_date"])
            applied_filters.append(f"to {entities['end_date'].strftime('%Y-%m-%d')}")

        # Add category filter if present
        category_name = None
        if "category" in entities:
            try:
                category_enum = getattr(CategoryEnum, entities["category"].upper(), None)
                if category_enum:
                    query = query.where(Expense.category == category_enum)
                    category_name = category_enum.value
                    applied_filters.append(f"category '{category_name}'")
                else:
                    # If category doesn't match any enum, log it
                    logging.warning(f"Unknown category: {entities['category']}")
                    return ChatbotResponse(
                        response_type="error",
                        data=f"Sorry, '{entities['category']}' is not a valid category. Valid categories are: {', '.join([c.value for c in CategoryEnum])}"
                    )
            except Exception as category_error:
                logging.error(f"Error processing category: {category_error}")
                return ChatbotResponse(
                    response_type="error",
                    data=f"Sorry, I couldn't process the category '{entities['category']}'. Valid categories are: {', '.join([c.value for c in CategoryEnum])}"
                )

        # Execute query
        try:
            result = await db.execute(query)
            total_amount = result.scalar_one_or_none() or Decimal('0.0')
        except Exception as db_error:
            logging.error(f"Database error in sum query: {db_error}")
            return ChatbotResponse(
                response_type="error",
                data="Sorry, I encountered a database error while calculating your expenses."
            )

        # Format response
        response_text = format_sum_response(total_amount, entities, applied_filters)

        # Add additional information for zero results
        if total_amount == Decimal('0.0'):
            # Check if there are any expenses at all for this user
            check_query = select(func.count(Expense.id)).where(Expense.user_id == current_user.id)
            check_result = await db.execute(check_query)
            total_count = check_result.scalar_one_or_none() or 0

            if total_count == 0:
                response_text += " You don't have any expenses recorded yet."
            else:
                response_text += " Try adjusting your filters to see more results."

        return ChatbotResponse(
            response_type="answer",
            data=response_text
        )

    except Exception as e:
        logging.error(f"Error handling query_sum: {e}", exc_info=True)
        return ChatbotResponse(
            response_type="error",
            data="Sorry, I had trouble calculating your expenses. Please try again with a simpler query."
        )


async def handle_query_list(
    db: AsyncSession,
    current_user: User,
    entities: Dict[str, Any]
) -> ChatbotResponse:
    """Handle queries about listing expenses with improved error handling and response formatting."""
    try:
        # Log the query details
        logging.info(f"Handling list query for user {current_user.id} with entities: {entities}")

        # Build query based on entities
        query = select(Expense).where(Expense.user_id == current_user.id)

        # Track applied filters for better response formatting
        applied_filters = []

        # Add date filters if present
        if "start_date" in entities:
            query = query.where(Expense.date >= entities["start_date"])
            applied_filters.append(f"from {entities['start_date'].strftime('%Y-%m-%d')}")

        if "end_date" in entities:
            query = query.where(Expense.date <= entities["end_date"])
            applied_filters.append(f"to {entities['end_date'].strftime('%Y-%m-%d')}")

        # Add category filter if present
        category_name = None
        if "category" in entities:
            try:
                category_enum = getattr(CategoryEnum, entities["category"].upper(), None)
                if category_enum:
                    query = query.where(Expense.category == category_enum)
                    category_name = category_enum.value
                    applied_filters.append(f"category '{category_name}'")
                else:
                    # If category doesn't match any enum, log it
                    logging.warning(f"Unknown category: {entities['category']}")
                    return ChatbotResponse(
                        response_type="error",
                        data=f"Sorry, '{entities['category']}' is not a valid category. Valid categories are: {', '.join([c.value for c in CategoryEnum])}"
                    )
            except Exception as category_error:
                logging.error(f"Error processing category: {category_error}")
                return ChatbotResponse(
                    response_type="error",
                    data=f"Sorry, I couldn't process the category '{entities['category']}'. Valid categories are: {', '.join([c.value for c in CategoryEnum])}"
                )

        # Add merchant filter if present
        if "merchant" in entities:
            merchant_name = entities["merchant"]
            # Use ILIKE for case-insensitive partial matching
            query = query.where(Expense.merchant_name.ilike(f"%{merchant_name}%"))
            applied_filters.append(f"merchant containing '{merchant_name}'")

        # Count total matching expenses before applying limit
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await db.execute(count_query)
        total_count = count_result.scalar_one_or_none() or 0

        # Order by date (most recent first) and limit to 5 expenses
        query = query.order_by(Expense.date.desc()).limit(5)

        # Execute query
        try:
            result = await db.execute(query)
            expenses = result.scalars().all()
        except Exception as db_error:
            logging.error(f"Database error in list query: {db_error}")
            return ChatbotResponse(
                response_type="error",
                data="Sorry, I encountered a database error while retrieving your expenses."
            )

        # Format response
        response_text = format_list_response(expenses, entities, applied_filters, total_count)

        return ChatbotResponse(
            response_type="answer",
            data=response_text
        )

    except Exception as e:
        logging.error(f"Error handling query_list: {e}", exc_info=True)
        return ChatbotResponse(
            response_type="error",
            data="Sorry, I had trouble retrieving your expenses. Please try again with a simpler query."
        )


async def handle_add_expense(
    db: AsyncSession,
    current_user: User,
    entities: Dict[str, Any]
) -> ChatbotResponse:
    """Handle requests to add a new expense with improved validation and error handling."""
    try:
        # Log the add expense request
        logging.info(f"Handling add expense request for user {current_user.id} with entities: {entities}")

        # Check for required fields
        if "amount" not in entities:
            return ChatbotResponse(
                response_type="error",
                data="I need an amount to add an expense. Please specify how much you spent."
            )

        # Validate amount (must be positive)
        amount = entities["amount"]
        if amount <= 0:
            return ChatbotResponse(
                response_type="error",
                data=f"The amount must be positive. You provided: {amount}"
            )

        # Set defaults for missing fields
        expense_date = entities.get("start_date", date.today())

        # Validate date (not too far in the future)
        today = date.today()
        if expense_date > today + timedelta(days=30):
            return ChatbotResponse(
                response_type="error",
                data=f"The date {expense_date.strftime('%Y-%m-%d')} seems to be too far in the future. Please provide a more recent date."
            )

        # Get merchant name (with fallback)
        merchant_name = entities.get("merchant", "Unknown Merchant")

        # Handle category with better error handling
        category_str = entities.get("category", "Other")
        try:
            # Try to get the category enum
            category_enum = getattr(CategoryEnum, category_str.upper())
        except AttributeError:
            # If category doesn't match any enum, try to find the closest match
            closest_match = None
            highest_similarity = 0

            for category in CategoryEnum:
                similarity = difflib.SequenceMatcher(None, category_str.lower(), category.value.lower()).ratio()
                if similarity > highest_similarity and similarity >= 0.6:  # 60% similarity threshold
                    highest_similarity = similarity
                    closest_match = category

            if closest_match:
                category_enum = closest_match
                logging.info(f"Mapped category '{category_str}' to '{category_enum.value}' with similarity {highest_similarity:.2f}")
            else:
                # Default to OTHER if no close match found
                category_enum = CategoryEnum.OTHER
                logging.info(f"No close match found for category '{category_str}', defaulting to 'Other'")

        # Create expense object
        expense = Expense(
            user_id=current_user.id,
            date=expense_date,
            merchant_name=merchant_name,
            amount=amount,
            currency="NPR",  # Default currency
            category=category_enum,
            is_ocr_entry=False,  # Manual entry via chatbot
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        # Save to database with error handling
        try:
            db.add(expense)
            await db.commit()
            await db.refresh(expense)
        except Exception as db_error:
            await db.rollback()
            logging.error(f"Database error in add_expense: {db_error}")
            return ChatbotResponse(
                response_type="error",
                data="Sorry, I encountered a database error while adding your expense."
            )

        # Format confirmation message with improved formatting
        amount_str = f"{expense.amount:,.2f}"  # Format with thousand separators
        response_text = (
            f"Expense added successfully! "
            f"NPR {amount_str} for {expense.category.value} "
            f"at {expense.merchant_name} on {expense.date.strftime('%Y-%m-%d')}."
        )

        # Add a note if any fields were automatically determined
        auto_determined = []

        if "category" not in entities or entities["category"] != expense.category.value:
            auto_determined.append(f"category (set to '{expense.category.value}')")

        if "merchant" not in entities:
            auto_determined.append("merchant (set to 'Unknown Merchant')")

        if "start_date" not in entities:
            auto_determined.append(f"date (set to today: {today.strftime('%Y-%m-%d')})")

        if auto_determined:
            response_text += f"\n\nNote: I automatically determined the following: {', '.join(auto_determined)}."

        return ChatbotResponse(
            response_type="confirmation",
            data=response_text
        )

    except Exception as e:
        # Ensure rollback in case of error
        try:
            await db.rollback()
        except:
            pass

        logging.error(f"Error handling add_expense: {e}", exc_info=True)
        return ChatbotResponse(
            response_type="error",
            data="Sorry, I couldn't add your expense. Please try again with a clearer request."
        )


def format_sum_response(total_amount: Decimal, entities: Dict[str, Any], applied_filters: List[str] = None) -> str:
    """
    Format the response for sum queries with improved readability.

    Args:
        total_amount: The total amount from the query
        entities: Dictionary of extracted entities
        applied_filters: List of filter descriptions for better response formatting

    Returns:
        Formatted response string
    """
    # Start with the total amount
    response = f"You spent NPR {total_amount:.2f}"

    # If we have applied filters, use them for better formatting
    if applied_filters and len(applied_filters) > 0:
        if len(applied_filters) == 1:
            response += f" {applied_filters[0]}"
        else:
            # Join all filters with commas and 'and' for the last one
            filters_text = ", ".join(applied_filters[:-1]) + f" and {applied_filters[-1]}"
            response += f" {filters_text}"
    else:
        # Fallback to the old formatting if no applied_filters provided
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


def format_list_response(
    expenses: List[Expense],
    entities: Dict[str, Any],
    applied_filters: List[str] = None,
    total_count: int = None
) -> str:
    """
    Format the response for list queries with improved readability.

    Args:
        expenses: List of expense objects
        entities: Dictionary of extracted entities
        applied_filters: List of filter descriptions for better response formatting
        total_count: Total number of matching expenses (before limit)

    Returns:
        Formatted response string
    """
    if not expenses:
        # No expenses found
        response = "I couldn't find any expenses"

        # If we have applied filters, use them for better formatting
        if applied_filters and len(applied_filters) > 0:
            if len(applied_filters) == 1:
                response += f" {applied_filters[0]}"
            else:
                # Join all filters with commas and 'and' for the last one
                filters_text = ", ".join(applied_filters[:-1]) + f" and {applied_filters[-1]}"
                response += f" {filters_text}"
        else:
            # Fallback to the old formatting if no applied_filters provided
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

    # If we have applied filters, use them for better formatting
    if applied_filters and len(applied_filters) > 0:
        if len(applied_filters) == 1:
            response += f" {applied_filters[0]}"
        else:
            # Join all filters with commas and 'and' for the last one
            filters_text = ", ".join(applied_filters[:-1]) + f" and {applied_filters[-1]}"
            response += f" {filters_text}"
    else:
        # Fallback to the old formatting if no applied_filters provided
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

    # Add total count information if available
    if total_count is not None and total_count > len(expenses):
        response += f" (showing {len(expenses)} of {total_count} total)"

    response += ":\n\n"

    # Add expense list with improved formatting
    for expense in expenses:
        # Format the date
        date_str = expense.date.strftime('%Y-%m-%d')

        # Format the amount with thousand separators
        amount_str = f"{expense.amount:,.2f}"

        # Get the category value
        category_str = expense.category.value if expense.category else "Uncategorized"

        # Get the merchant name (or "Unknown" if not available)
        merchant_str = expense.merchant_name or "Unknown Merchant"

        # Add the formatted expense line
        response += (f"- {date_str}: NPR {amount_str} for {category_str} at {merchant_str}\n")

    # Add a note if there are more expenses than shown
    if total_count is not None and total_count > len(expenses):
        response += f"\nThere are {total_count - len(expenses)} more expenses matching your query."

    return response