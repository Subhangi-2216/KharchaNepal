# backend/src/chatbot/nlp_service.py
"""
NLP service for parsing expense chatbot queries.
This module handles the natural language processing for the expense chatbot,
extracting intents and entities from user queries.
"""

import re
import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, Optional, List, Tuple

import spacy
import dateparser

# Load spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
    logging.info("Successfully loaded spaCy model: en_core_web_sm")
except Exception as e:
    logging.error(f"Error loading spaCy model: {e}")
    # Fallback to simple model if needed
    nlp = spacy.blank("en")

# Define intent types
INTENT_QUERY_SUM = "query_sum"
INTENT_QUERY_LIST = "query_list"
INTENT_ADD_EXPENSE = "add_expense"
INTENT_UNKNOWN = "unknown"

# Define category mapping for fuzzy matching
CATEGORY_MAPPING = {
    "food": "Food",
    "meal": "Food",
    "restaurant": "Food",
    "lunch": "Food",
    "dinner": "Food",
    "breakfast": "Food",
    "snack": "Food",
    "grocery": "Food",
    "groceries": "Food",
    "travel": "Travel",
    "transportation": "Travel",
    "taxi": "Travel",
    "bus": "Travel",
    "flight": "Travel",
    "train": "Travel",
    "car": "Travel",
    "gas": "Travel",
    "fuel": "Travel",
    "entertainment": "Entertainment",
    "movie": "Entertainment",
    "cinema": "Entertainment",
    "concert": "Entertainment",
    "show": "Entertainment",
    "game": "Entertainment",
    "games": "Entertainment",
    "household": "Household Bill",
    "bill": "Household Bill",
    "bills": "Household Bill",
    "utility": "Household Bill",
    "utilities": "Household Bill",
    "rent": "Household Bill",
    "electricity": "Household Bill",
    "water": "Household Bill",
    "internet": "Household Bill",
    "phone": "Household Bill",
    "other": "Other",
    "miscellaneous": "Other",
    "misc": "Other"
}

def parse_expense_query(query: str) -> Dict[str, Any]:
    """
    Parse a natural language query to extract intent and entities.
    
    Args:
        query: The user's natural language query
        
    Returns:
        A dictionary containing:
        - intent: The detected intent (query_sum, query_list, add_expense, unknown)
        - entities: A dictionary of extracted entities (amount, date, category, merchant, etc.)
        - confidence: A confidence score for the parsing (0.0-1.0)
    """
    # Clean and normalize query
    clean_query = clean_text(query)
    
    # Process with spaCy
    doc = nlp(clean_query)
    
    # Detect intent
    intent, intent_confidence = detect_intent(clean_query, doc)
    
    # Extract entities based on intent
    entities = {}
    
    # Extract date entities (common for all intents)
    date_info = extract_date_info(clean_query, doc)
    if date_info:
        entities.update(date_info)
    
    # Extract category (common for all intents)
    category = extract_category(clean_query, doc)
    if category:
        entities["category"] = category
    
    # Extract intent-specific entities
    if intent == INTENT_ADD_EXPENSE:
        # For add_expense, extract amount and merchant
        amount = extract_amount(clean_query, doc)
        if amount:
            entities["amount"] = amount
        
        merchant = extract_merchant(clean_query, doc)
        if merchant:
            entities["merchant"] = merchant
    
    # Calculate overall confidence
    confidence = calculate_confidence(intent, intent_confidence, entities)
    
    return {
        "intent": intent,
        "entities": entities,
        "confidence": confidence
    }

def clean_text(text: str) -> str:
    """
    Clean and normalize text for better processing.
    
    Args:
        text: Input text
        
    Returns:
        Cleaned text
    """
    # Convert to lowercase
    text = text.lower()
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def detect_intent(query: str, doc: Any) -> Tuple[str, float]:
    """
    Detect the intent of the query.
    
    Args:
        query: Cleaned user query
        doc: spaCy processed document
        
    Returns:
        Tuple of (intent_type, confidence)
    """
    # Keywords for each intent
    add_keywords = ["add", "create", "log", "record", "new", "save", "spent", "paid", "bought"]
    sum_keywords = ["how much", "total", "sum", "spent on", "paid for", "cost of", "amount"]
    list_keywords = ["show", "list", "what", "display", "see", "view", "find", "search", "get"]
    
    # Check for add_expense intent
    if any(keyword in query for keyword in add_keywords):
        # Check if there's an amount mentioned (stronger signal for add_expense)
        amount_entities = [ent for ent in doc.ents if ent.label_ in ["MONEY", "CARDINAL"]]
        if amount_entities:
            return INTENT_ADD_EXPENSE, 0.8
        return INTENT_ADD_EXPENSE, 0.6
    
    # Check for query_sum intent
    if any(keyword in query for keyword in sum_keywords):
        return INTENT_QUERY_SUM, 0.7
    
    # Check for query_list intent
    if any(keyword in query for keyword in list_keywords):
        return INTENT_QUERY_LIST, 0.6
    
    # Default to unknown intent with low confidence
    return INTENT_UNKNOWN, 0.3

def extract_date_info(query: str, doc: Any) -> Dict[str, Any]:
    """
    Extract date-related information from the query.
    
    Args:
        query: Cleaned user query
        doc: spaCy processed document
        
    Returns:
        Dictionary with date-related entities
    """
    date_info = {}
    
    # Check for relative date references
    today = date.today()
    
    # Common relative date patterns
    relative_patterns = {
        r"today": (today, today),
        r"yesterday": (today - timedelta(days=1), today - timedelta(days=1)),
        r"this week": (today - timedelta(days=today.weekday()), today),
        r"last week": (today - timedelta(days=today.weekday() + 7), today - timedelta(days=today.weekday() + 1)),
        r"this month": (date(today.year, today.month, 1), today),
        r"last month": (date(today.year - 1 if today.month == 1 else today.year, 
                            12 if today.month == 1 else today.month - 1, 1),
                        date(today.year, today.month, 1) - timedelta(days=1)),
        r"this year": (date(today.year, 1, 1), today),
        r"last year": (date(today.year - 1, 1, 1), date(today.year, 1, 1) - timedelta(days=1))
    }
    
    # Check for relative date patterns
    for pattern, (start_date, end_date) in relative_patterns.items():
        if re.search(pattern, query):
            date_info["start_date"] = start_date
            date_info["end_date"] = end_date
            return date_info
    
    # Extract DATE entities from spaCy
    date_entities = [ent for ent in doc.ents if ent.label_ == "DATE"]
    
    if date_entities:
        # Try to parse dates with dateparser
        for ent in date_entities:
            parsed_date = dateparser.parse(ent.text)
            if parsed_date:
                # If we find a single date, assume it's for a specific day
                date_info["start_date"] = parsed_date.date()
                date_info["end_date"] = parsed_date.date()
                break
    
    return date_info

def extract_category(query: str, doc: Any) -> Optional[str]:
    """
    Extract expense category from the query.
    
    Args:
        query: Cleaned user query
        doc: spaCy processed document
        
    Returns:
        Category string or None
    """
    # Check for direct category mentions
    for word in query.split():
        category = CATEGORY_MAPPING.get(word)
        if category:
            return category
    
    # Check for category phrases
    for phrase, category in CATEGORY_MAPPING.items():
        if phrase in query and len(phrase.split()) > 1:
            return category
    
    return None

def extract_amount(query: str, doc: Any) -> Optional[Decimal]:
    """
    Extract amount from the query.
    
    Args:
        query: Cleaned user query
        doc: spaCy processed document
        
    Returns:
        Decimal amount or None
    """
    # Look for MONEY entities first
    money_entities = [ent for ent in doc.ents if ent.label_ == "MONEY"]
    
    if money_entities:
        # Extract the numeric part
        for ent in money_entities:
            # Remove currency symbols and commas
            amount_text = re.sub(r'[^\d.]', '', ent.text)
            try:
                return Decimal(amount_text)
            except:
                continue
    
    # Look for CARDINAL entities near amount keywords
    cardinal_entities = [ent for ent in doc.ents if ent.label_ == "CARDINAL"]
    amount_keywords = ["rs", "rs.", "npr", "rupees", "amount"]
    
    for ent in cardinal_entities:
        # Check if entity is near amount keywords
        context = query[max(0, ent.start_char - 10):min(len(query), ent.end_char + 10)]
        if any(keyword in context for keyword in amount_keywords):
            # Remove non-numeric characters
            amount_text = re.sub(r'[^\d.]', '', ent.text)
            try:
                return Decimal(amount_text)
            except:
                continue
    
    # Regular expression fallback
    amount_patterns = [
        r'rs\.?\s*(\d+(?:\.\d+)?)',
        r'npr\s*(\d+(?:\.\d+)?)',
        r'rupees\s*(\d+(?:\.\d+)?)',
        r'(\d+(?:\.\d+)?)\s*rs',
        r'(\d+(?:\.\d+)?)\s*npr',
        r'(\d+(?:\.\d+)?)\s*rupees'
    ]
    
    for pattern in amount_patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            try:
                return Decimal(match.group(1))
            except:
                continue
    
    return None

def extract_merchant(query: str, doc: Any) -> Optional[str]:
    """
    Extract merchant name from the query.
    
    Args:
        query: Cleaned user query
        doc: spaCy processed document
        
    Returns:
        Merchant name or None
    """
    # Look for ORG entities
    org_entities = [ent for ent in doc.ents if ent.label_ == "ORG"]
    
    if org_entities:
        # Return the first organization entity
        return org_entities[0].text
    
    # Look for merchant keywords
    merchant_keywords = ["at", "from", "to", "for"]
    
    for keyword in merchant_keywords:
        pattern = rf'{keyword}\s+([A-Za-z0-9\s]+?)(?:\s+(?:on|for|amount|rs|npr|rupees)|$)'
        match = re.search(pattern, query)
        if match:
            return match.group(1).strip()
    
    return None

def calculate_confidence(intent: str, intent_confidence: float, entities: Dict[str, Any]) -> float:
    """
    Calculate overall confidence score for the parsing.
    
    Args:
        intent: Detected intent
        intent_confidence: Confidence score for intent detection
        entities: Extracted entities
        
    Returns:
        Overall confidence score (0.0-1.0)
    """
    # Base confidence from intent
    confidence = intent_confidence
    
    # Adjust based on required entities for each intent
    if intent == INTENT_ADD_EXPENSE:
        # For add_expense, we need at least amount
        if "amount" not in entities:
            confidence *= 0.5
        # Boost if we have merchant and category
        if "merchant" in entities:
            confidence *= 1.2
        if "category" in entities:
            confidence *= 1.1
    
    elif intent in [INTENT_QUERY_SUM, INTENT_QUERY_LIST]:
        # For queries, we need at least category or date
        if "category" not in entities and "start_date" not in entities:
            confidence *= 0.5
        # Boost if we have both
        if "category" in entities and "start_date" in entities:
            confidence *= 1.2
    
    # Cap at 1.0
    return min(confidence, 1.0)