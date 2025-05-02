# backend/tests/unit/chatbot/test_nlp_service.py
"""
Unit tests for the NLP service.
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal

from src.chatbot.nlp_service import (
    parse_expense_query,
    clean_text,
    detect_intent,
    extract_date_info,
    extract_category,
    extract_amount,
    extract_merchant,
    calculate_confidence,
    INTENT_QUERY_SUM,
    INTENT_QUERY_LIST,
    INTENT_ADD_EXPENSE,
    INTENT_UNKNOWN
)

# --- Test parse_expense_query ---

def test_parse_expense_query_sum():
    """Test parsing a sum query."""
    query = "How much did I spend on food last month?"
    result = parse_expense_query(query)
    
    assert result["intent"] == INTENT_QUERY_SUM
    assert "category" in result["entities"]
    assert result["entities"]["category"] == "Food"
    assert "start_date" in result["entities"]
    assert "end_date" in result["entities"]
    assert result["confidence"] > 0.5

def test_parse_expense_query_list():
    """Test parsing a list query."""
    query = "Show me my travel expenses this week"
    result = parse_expense_query(query)
    
    assert result["intent"] == INTENT_QUERY_LIST
    assert "category" in result["entities"]
    assert result["entities"]["category"] == "Travel"
    assert "start_date" in result["entities"]
    assert "end_date" in result["entities"]
    assert result["confidence"] > 0.5

def test_parse_expense_query_add():
    """Test parsing an add expense query."""
    query = "Add a new expense of Rs 500 for food at Restaurant ABC yesterday"
    result = parse_expense_query(query)
    
    assert result["intent"] == INTENT_ADD_EXPENSE
    assert "amount" in result["entities"]
    assert result["entities"]["amount"] == Decimal("500")
    assert "category" in result["entities"]
    assert result["entities"]["category"] == "Food"
    assert "merchant" in result["entities"]
    assert "Restaurant ABC" in result["entities"]["merchant"]
    assert "start_date" in result["entities"]
    assert "end_date" in result["entities"]
    assert result["confidence"] > 0.5

def test_parse_expense_query_unknown():
    """Test parsing an unknown query."""
    query = "What is the meaning of life?"
    result = parse_expense_query(query)
    
    assert result["intent"] == INTENT_UNKNOWN
    assert result["confidence"] < 0.5

# --- Test clean_text ---

def test_clean_text():
    """Test text cleaning."""
    text = "  How Much did I spend?  "
    result = clean_text(text)
    
    assert result == "how much did i spend"

# --- Test detect_intent ---

def test_detect_intent_sum():
    """Test detecting sum intent."""
    query = "how much did i spend on food"
    doc = None  # Mock doc object
    intent, confidence = detect_intent(query, doc)
    
    assert intent == INTENT_QUERY_SUM
    assert confidence > 0.5

def test_detect_intent_list():
    """Test detecting list intent."""
    query = "show me my expenses"
    doc = None  # Mock doc object
    intent, confidence = detect_intent(query, doc)
    
    assert intent == INTENT_QUERY_LIST
    assert confidence > 0.5

def test_detect_intent_add():
    """Test detecting add intent."""
    query = "add a new expense"
    doc = None  # Mock doc object
    intent, confidence = detect_intent(query, doc)
    
    assert intent == INTENT_ADD_EXPENSE
    assert confidence > 0.5

def test_detect_intent_unknown():
    """Test detecting unknown intent."""
    query = "hello world"
    doc = None  # Mock doc object
    intent, confidence = detect_intent(query, doc)
    
    assert intent == INTENT_UNKNOWN
    assert confidence < 0.5

# --- Test extract_date_info ---

def test_extract_date_info_today():
    """Test extracting today's date."""
    query = "expenses today"
    doc = None  # Mock doc object
    date_info = extract_date_info(query, doc)
    
    today = date.today()
    assert date_info["start_date"] == today
    assert date_info["end_date"] == today

def test_extract_date_info_yesterday():
    """Test extracting yesterday's date."""
    query = "expenses yesterday"
    doc = None  # Mock doc object
    date_info = extract_date_info(query, doc)
    
    yesterday = date.today() - timedelta(days=1)
    assert date_info["start_date"] == yesterday
    assert date_info["end_date"] == yesterday

def test_extract_date_info_this_week():
    """Test extracting this week's date range."""
    query = "expenses this week"
    doc = None  # Mock doc object
    date_info = extract_date_info(query, doc)
    
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())
    assert date_info["start_date"] == start_of_week
    assert date_info["end_date"] == today

def test_extract_date_info_last_week():
    """Test extracting last week's date range."""
    query = "expenses last week"
    doc = None  # Mock doc object
    date_info = extract_date_info(query, doc)
    
    today = date.today()
    start_of_last_week = today - timedelta(days=today.weekday() + 7)
    end_of_last_week = today - timedelta(days=today.weekday() + 1)
    assert date_info["start_date"] == start_of_last_week
    assert date_info["end_date"] == end_of_last_week

def test_extract_date_info_this_month():
    """Test extracting this month's date range."""
    query = "expenses this month"
    doc = None  # Mock doc object
    date_info = extract_date_info(query, doc)
    
    today = date.today()
    start_of_month = date(today.year, today.month, 1)
    assert date_info["start_date"] == start_of_month
    assert date_info["end_date"] == today

def test_extract_date_info_last_month():
    """Test extracting last month's date range."""
    query = "expenses last month"
    doc = None  # Mock doc object
    date_info = extract_date_info(query, doc)
    
    today = date.today()
    if today.month == 1:
        start_of_last_month = date(today.year - 1, 12, 1)
    else:
        start_of_last_month = date(today.year, today.month - 1, 1)
    end_of_last_month = date(today.year, today.month, 1) - timedelta(days=1)
    assert date_info["start_date"] == start_of_last_month
    assert date_info["end_date"] == end_of_last_month

# --- Test extract_category ---

def test_extract_category_direct():
    """Test extracting category from direct mention."""
    query = "food expenses"
    doc = None  # Mock doc object
    category = extract_category(query, doc)
    
    assert category == "Food"

def test_extract_category_phrase():
    """Test extracting category from a phrase."""
    query = "household bill expenses"
    doc = None  # Mock doc object
    category = extract_category(query, doc)
    
    assert category == "Household Bill"

def test_extract_category_none():
    """Test extracting category when none is mentioned."""
    query = "my expenses"
    doc = None  # Mock doc object
    category = extract_category(query, doc)
    
    assert category is None

# --- Test extract_amount ---

def test_extract_amount_with_currency():
    """Test extracting amount with currency symbol."""
    query = "rs 500"
    doc = None  # Mock doc object
    amount = extract_amount(query, doc)
    
    assert amount == Decimal("500")

def test_extract_amount_with_decimal():
    """Test extracting amount with decimal point."""
    query = "rs 500.50"
    doc = None  # Mock doc object
    amount = extract_amount(query, doc)
    
    assert amount == Decimal("500.50")

def test_extract_amount_none():
    """Test extracting amount when none is mentioned."""
    query = "my expenses"
    doc = None  # Mock doc object
    amount = extract_amount(query, doc)
    
    assert amount is None

# --- Test extract_merchant ---

def test_extract_merchant_with_at():
    """Test extracting merchant with 'at' keyword."""
    query = "expense at Restaurant ABC"
    doc = None  # Mock doc object
    merchant = extract_merchant(query, doc)
    
    assert merchant == "Restaurant ABC"

def test_extract_merchant_with_from():
    """Test extracting merchant with 'from' keyword."""
    query = "expense from Shop XYZ"
    doc = None  # Mock doc object
    merchant = extract_merchant(query, doc)
    
    assert merchant == "Shop XYZ"

def test_extract_merchant_none():
    """Test extracting merchant when none is mentioned."""
    query = "my expenses"
    doc = None  # Mock doc object
    merchant = extract_merchant(query, doc)
    
    assert merchant is None

# --- Test calculate_confidence ---

def test_calculate_confidence_add_expense_complete():
    """Test confidence calculation for complete add_expense intent."""
    intent = INTENT_ADD_EXPENSE
    intent_confidence = 0.7
    entities = {
        "amount": Decimal("500"),
        "merchant": "Restaurant ABC",
        "category": "Food"
    }
    confidence = calculate_confidence(intent, intent_confidence, entities)
    
    assert confidence > 0.7  # Should be boosted

def test_calculate_confidence_add_expense_incomplete():
    """Test confidence calculation for incomplete add_expense intent."""
    intent = INTENT_ADD_EXPENSE
    intent_confidence = 0.7
    entities = {}  # No entities
    confidence = calculate_confidence(intent, intent_confidence, entities)
    
    assert confidence < 0.7  # Should be reduced

def test_calculate_confidence_query_sum_complete():
    """Test confidence calculation for complete query_sum intent."""
    intent = INTENT_QUERY_SUM
    intent_confidence = 0.7
    entities = {
        "category": "Food",
        "start_date": date.today(),
        "end_date": date.today()
    }
    confidence = calculate_confidence(intent, intent_confidence, entities)
    
    assert confidence > 0.7  # Should be boosted

def test_calculate_confidence_query_sum_incomplete():
    """Test confidence calculation for incomplete query_sum intent."""
    intent = INTENT_QUERY_SUM
    intent_confidence = 0.7
    entities = {}  # No entities
    confidence = calculate_confidence(intent, intent_confidence, entities)
    
    assert confidence < 0.7  # Should be reduced