# backend/src/chatbot/nlp_service.py
"""
NLP service for parsing expense chatbot queries.
This module handles the natural language processing for the expense chatbot,
extracting intents and entities from user queries.

Enhanced with:
- Improved date extraction with better regex patterns and validation
- Enhanced amount extraction with better currency handling
- Improved merchant extraction with better heuristics
- Enhanced category extraction with case-insensitive and fuzzy matching
- Improved intent detection with better confidence calculation
"""

import re
import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, Optional, List, Tuple, Set
import difflib  # For fuzzy matching

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

# Define confidence thresholds
HIGH_CONFIDENCE = 0.8
MEDIUM_CONFIDENCE = 0.6
LOW_CONFIDENCE = 0.4
VERY_LOW_CONFIDENCE = 0.2

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
    Parse a natural language query to extract intent and entities with confidence scores.

    Args:
        query: The user's natural language query

    Returns:
        A dictionary containing:
        - intent: The detected intent (query_sum, query_list, add_expense, unknown)
        - entities: A dictionary of extracted entities with confidence scores
        - confidence: Overall confidence score for the parsing (0.0-1.0)
        - explanation: Detailed explanation of confidence calculation
    """
    # Clean and normalize query
    clean_query = clean_text(query)

    # Process with spaCy
    doc = nlp(clean_query)

    # Detect intent with confidence and evidence
    intent_data = detect_intent(clean_query, doc)

    # Extract entities with confidence scores
    entities = {}
    entity_details = {}

    # Extract date entities (common for all intents)
    date_info = extract_date_info(clean_query, doc)
    if date_info:
        # Store date confidence separately
        if "confidence" in date_info:
            date_confidence = date_info.pop("confidence")
            entity_details["date"] = {
                "confidence": date_confidence,
                "source": "date extraction"
            }
        entities.update(date_info)

    # Extract category (common for all intents)
    category_data = extract_category(clean_query, doc)
    if category_data and "category" in category_data:
        entities["category"] = category_data["category"]
        entity_details["category"] = {
            "confidence": category_data.get("confidence", MEDIUM_CONFIDENCE),
            "source": category_data.get("source", "category extraction")
        }
        # Include alternatives if available
        if "alternatives" in category_data:
            entity_details["category"]["alternatives"] = category_data["alternatives"]

    # Extract intent-specific entities
    intent = intent_data.get("intent", INTENT_UNKNOWN)

    # Always extract amount and merchant for all intents
    # This helps with confidence calculation and potential multi-intent queries

    # Extract amount
    amount_data = extract_amount(clean_query, doc)
    if amount_data and "amount" in amount_data:
        entities["amount"] = amount_data["amount"]
        entity_details["amount"] = {
            "confidence": amount_data.get("confidence", MEDIUM_CONFIDENCE),
            "source": amount_data.get("source", "amount extraction")
        }
        # Include alternatives if available
        if "alternatives" in amount_data:
            entity_details["amount"]["alternatives"] = amount_data["alternatives"]

    # Extract merchant
    merchant_data = extract_merchant(clean_query, doc)
    if merchant_data and "merchant" in merchant_data:
        entities["merchant"] = merchant_data["merchant"]
        entity_details["merchant"] = {
            "confidence": merchant_data.get("confidence", MEDIUM_CONFIDENCE),
            "source": merchant_data.get("source", "merchant extraction")
        }
        # Include alternatives if available
        if "alternatives" in merchant_data:
            entity_details["merchant"]["alternatives"] = merchant_data["alternatives"]

    # Calculate overall confidence with detailed explanation
    confidence_data = calculate_confidence(intent_data, entity_details)

    # Prepare the result
    result = {
        "intent": intent,
        "intent_confidence": intent_data.get("confidence", VERY_LOW_CONFIDENCE),
        "intent_evidence": intent_data.get("evidence", []),
        "entities": entities,
        "entity_details": entity_details,
        "confidence": confidence_data.get("confidence", VERY_LOW_CONFIDENCE),
        "confidence_level": confidence_data.get("confidence_level", "very low"),
        "explanation": confidence_data.get("explanation", [])
    }

    # Include intent alternatives if available
    if "alternatives" in intent_data:
        result["intent_alternatives"] = intent_data["alternatives"]

    # Add debug information in development mode
    if logging.getLogger().level <= logging.DEBUG:
        logging.debug(f"Parse result: {result}")

    return result

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

    # Remove punctuation (more robustly)
    text = re.sub(r'[^\w\s\']', '', text) # Keep apostrophes for contractions

    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    return text

def detect_intent(query: str, doc: Any) -> Dict[str, Any]:
    """
    Detect the intent of the query with confidence score and supporting evidence.

    Args:
        query: Cleaned user query
        doc: spaCy processed document

    Returns:
        Dictionary with intent, confidence, and supporting evidence
    """
    result = {}
    intent_scores = {}

    # Enhanced keywords for each intent
    add_keywords = {
        "high": ["add expense", "create expense", "log expense", "record expense", "new expense", "save expense"],
        "medium": ["add", "create", "log", "record", "new", "save", "spent", "paid", "bought", "purchased"],
        "low": ["expense for", "cost me", "paid for", "bought at"]
    }

    sum_keywords = {
        "high": ["how much spent", "total spent", "sum of expenses", "spent on", "paid for", "cost of", "amount spent"],
        "medium": ["how much", "total", "sum", "amount", "spent", "paid", "cost"],
        "low": ["expenses for", "spending on", "money for"]
    }

    list_keywords = {
        "high": ["show expenses", "list expenses", "display expenses", "view expenses", "find expenses", "get expenses"],
        "medium": ["show", "list", "display", "see", "view", "find", "search", "get", "what are"],
        "low": ["tell me about", "give me", "i want to see"]
    }

    # Check for add_expense intent
    add_score = 0
    add_evidence = []

    # Check for high-confidence add keywords (exact phrases)
    for keyword in add_keywords["high"]:
        if keyword in query:
            add_score += HIGH_CONFIDENCE
            add_evidence.append(f"High-confidence keyword: '{keyword}'")

    # Check for medium-confidence add keywords
    for keyword in add_keywords["medium"]:
        if re.search(r'\b' + re.escape(keyword) + r'\b', query, re.IGNORECASE):
            add_score += MEDIUM_CONFIDENCE
            add_evidence.append(f"Medium-confidence keyword: '{keyword}'")

    # Check for low-confidence add keywords
    for keyword in add_keywords["low"]:
        if keyword in query:
            add_score += LOW_CONFIDENCE
            add_evidence.append(f"Low-confidence keyword: '{keyword}'")

    # Boost add_score if there are MONEY or CARDINAL entities (likely an amount)
    amount_entities = [ent for ent in doc.ents if ent.label_ in ["MONEY", "CARDINAL"]]
    if amount_entities:
        add_score += MEDIUM_CONFIDENCE
        add_evidence.append(f"Contains {len(amount_entities)} MONEY/CARDINAL entities")

    # Check for sum intent
    sum_score = 0
    sum_evidence = []

    # Check for high-confidence sum keywords
    for keyword in sum_keywords["high"]:
        if keyword in query:
            sum_score += HIGH_CONFIDENCE
            sum_evidence.append(f"High-confidence keyword: '{keyword}'")

    # Check for medium-confidence sum keywords
    for keyword in sum_keywords["medium"]:
        if re.search(r'\b' + re.escape(keyword) + r'\b', query, re.IGNORECASE):
            sum_score += MEDIUM_CONFIDENCE
            sum_evidence.append(f"Medium-confidence keyword: '{keyword}'")

    # Check for low-confidence sum keywords
    for keyword in sum_keywords["low"]:
        if keyword in query:
            sum_score += LOW_CONFIDENCE
            sum_evidence.append(f"Low-confidence keyword: '{keyword}'")

    # Check for list intent
    list_score = 0
    list_evidence = []

    # Check for high-confidence list keywords
    for keyword in list_keywords["high"]:
        if keyword in query:
            list_score += HIGH_CONFIDENCE
            list_evidence.append(f"High-confidence keyword: '{keyword}'")

    # Check for medium-confidence list keywords
    for keyword in list_keywords["medium"]:
        if re.search(r'\b' + re.escape(keyword) + r'\b', query, re.IGNORECASE):
            list_score += MEDIUM_CONFIDENCE
            list_evidence.append(f"Medium-confidence keyword: '{keyword}'")

    # Check for low-confidence list keywords
    for keyword in list_keywords["low"]:
        if keyword in query:
            list_score += LOW_CONFIDENCE
            list_evidence.append(f"Low-confidence keyword: '{keyword}'")

    # Special case: "what" at the start is often a list query
    if query.startswith("what"):
        # But only if it mentions expenses or categories
        expense_related_keywords = ["expense", "spent", "paid", "category", "merchant"]
        if any(exp_kw in query for exp_kw in expense_related_keywords) or any(cat in query.lower() for cat in CATEGORY_MAPPING):
            list_score += MEDIUM_CONFIDENCE
            list_evidence.append("Starts with 'what' and mentions expenses/categories")
        else:
            # If "what" but no expense context, could be an unknown question
            list_score += VERY_LOW_CONFIDENCE
            list_evidence.append("Starts with 'what' but no expense context")

    # Normalize scores to avoid bias from number of keywords
    if add_evidence:
        add_score = min(add_score, 1.0)
    if sum_evidence:
        sum_score = min(sum_score, 1.0)
    if list_evidence:
        list_score = min(list_score, 1.0)

    # Store scores
    intent_scores[INTENT_ADD_EXPENSE] = (add_score, add_evidence)
    intent_scores[INTENT_QUERY_SUM] = (sum_score, sum_evidence)
    intent_scores[INTENT_QUERY_LIST] = (list_score, list_evidence)

    # Get the intent with the highest score
    if intent_scores:
        # Sort by score (highest first)
        sorted_intents = sorted(intent_scores.items(), key=lambda x: x[1][0], reverse=True)
        best_intent, (best_score, best_evidence) = sorted_intents[0]

        # If the best score is too low, default to unknown
        if best_score < VERY_LOW_CONFIDENCE:
            result["intent"] = INTENT_UNKNOWN
            result["confidence"] = VERY_LOW_CONFIDENCE
            result["evidence"] = ["No clear intent detected"]
        else:
            result["intent"] = best_intent
            result["confidence"] = best_score
            result["evidence"] = best_evidence

            # Include alternatives if they're close in score
            alternatives = []
            for intent, (score, evidence) in sorted_intents[1:]:
                # Only include if the score is at least 70% of the best score
                if score >= best_score * 0.7:
                    alternatives.append({
                        "intent": intent,
                        "confidence": score,
                        "evidence": evidence[:2]  # Limit evidence to top 2 items
                    })
            if alternatives:
                result["alternatives"] = alternatives
    else:
        # Default to unknown intent with very low confidence
        result["intent"] = INTENT_UNKNOWN
        result["confidence"] = VERY_LOW_CONFIDENCE
        result["evidence"] = ["No intent keywords detected"]

    return result

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

    # Common relative date patterns - Order matters (more specific first)
    # Enhanced with more variations and case-insensitive matching
    relative_patterns = {
        r"today|now": (today, today),
        r"yesterday": (today - timedelta(days=1), today - timedelta(days=1)),
        r"last\s+week|previous\s+week": (today - timedelta(days=today.weekday() + 7),
                                         today - timedelta(days=today.weekday() + 1)),
        r"this\s+week|current\s+week": (today - timedelta(days=today.weekday()), today),
        r"last\s+month|previous\s+month": (date(today.year - 1 if today.month == 1 else today.year,
                                              12 if today.month == 1 else today.month - 1, 1),
                                          date(today.year, today.month, 1) - timedelta(days=1)),
        r"this\s+month|current\s+month": (date(today.year, today.month, 1), today),
        r"last\s+year|previous\s+year": (date(today.year - 1, 1, 1),
                                         date(today.year, 1, 1) - timedelta(days=1)),
        r"this\s+year|current\s+year": (date(today.year, 1, 1), today),
        # Add more specific patterns
        r"last\s+(\d+)\s+days?": lambda match: (
            today - timedelta(days=int(match.group(1))), today
        ),
        r"past\s+(\d+)\s+days?": lambda match: (
            today - timedelta(days=int(match.group(1))), today
        ),
        r"last\s+(\d+)\s+weeks?": lambda match: (
            today - timedelta(weeks=int(match.group(1))), today
        ),
        r"last\s+(\d+)\s+months?": lambda match: (
            date(today.year - (1 if today.month <= int(match.group(1)) % 12 else 0),
                 (today.month - int(match.group(1))) % 12 or 12, 1),
            today
        )
    }

    # Check for date range patterns like "from X to Y"
    range_match = re.search(r'from\s+(.+?)\s+to\s+(.+?)(?:\s|$)', query, re.IGNORECASE)
    if range_match:
        start_text = range_match.group(1)
        end_text = range_match.group(2)

        start_date_obj = dateparser.parse(
            start_text,
            settings={'PREFER_DATES_FROM': 'past', 'STRICT_PARSING': False}
        )
        end_date_obj = dateparser.parse(
            end_text,
            settings={'PREFER_DATES_FROM': 'past', 'STRICT_PARSING': False}
        )

        if start_date_obj and end_date_obj:
            date_info["start_date"] = start_date_obj.date()
            date_info["end_date"] = end_date_obj.date()
            # Ensure start date is before end date
            if date_info["start_date"] > date_info["end_date"]:
                date_info["start_date"], date_info["end_date"] = date_info["end_date"], date_info["start_date"]
            return date_info

    # Check for relative date patterns
    matched_relative = False
    for pattern_str, date_value in relative_patterns.items():
        # Use case-insensitive matching
        match = re.search(r'\b' + pattern_str + r'\b', query, re.IGNORECASE)
        if match:
            if callable(date_value):
                # Handle dynamic patterns with lambda functions
                start_date, end_date = date_value(match)
            else:
                # Static date values
                start_date, end_date = date_value

            date_info["start_date"] = start_date
            date_info["end_date"] = end_date
            date_info["confidence"] = HIGH_CONFIDENCE  # High confidence for explicit patterns
            matched_relative = True
            break  # Stop after first match

    # If no relative match, extract DATE entities from spaCy
    if not matched_relative:
        date_entities = [ent for ent in doc.ents if ent.label_ == "DATE"]
        parsed_dates = []
        confidence = MEDIUM_CONFIDENCE  # Default confidence for spaCy entities

        if date_entities:
            # Try to parse dates with dateparser
            for ent in date_entities:
                # Use dateparser settings for better parsing
                parsed_date_obj = dateparser.parse(
                    ent.text,
                    settings={
                        'PREFER_DATES_FROM': 'past',
                        'STRICT_PARSING': False,
                        'DATE_ORDER': 'DMY'  # Prefer day-month-year format for ambiguous dates
                    }
                )
                if parsed_date_obj:
                    parsed_date = parsed_date_obj.date()
                    # Validate the date is reasonable (not too far in the future)
                    if parsed_date <= today + timedelta(days=365):  # Allow up to 1 year in future
                        parsed_dates.append(parsed_date)
                    else:
                        # If date is too far in future, it might be a parsing error
                        # (e.g., phone number interpreted as year)
                        logging.warning(f"Ignoring likely invalid future date: {parsed_date} from '{ent.text}'")
                        confidence = LOW_CONFIDENCE  # Lower confidence if we had to ignore dates

        # Also try to find dates in the text directly with dateparser
        # This can catch dates that spaCy missed
        if not parsed_dates:
            # Look for common date patterns
            date_patterns = [
                r'\d{1,2}[-/\.]\d{1,2}[-/\.]\d{2,4}',  # DD/MM/YYYY or MM/DD/YYYY
                r'\d{1,2}(?:st|nd|rd|th)?\s+(?:of\s+)?(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*(?:\s+\d{2,4})?',  # 1st of January 2023
                r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2}(?:st|nd|rd|th)?(?:\s+\d{2,4})?'  # January 1st 2023
            ]

            for pattern in date_patterns:
                matches = re.finditer(pattern, query, re.IGNORECASE)
                for match in matches:
                    parsed_date_obj = dateparser.parse(
                        match.group(0),
                        settings={
                            'PREFER_DATES_FROM': 'past',
                            'STRICT_PARSING': False,
                            'DATE_ORDER': 'DMY'  # Prefer day-month-year format for ambiguous dates
                        }
                    )
                    if parsed_date_obj:
                        parsed_date = parsed_date_obj.date()
                        # Validate the date is reasonable
                        if parsed_date <= today + timedelta(days=365):
                            parsed_dates.append(parsed_date)
                            confidence = MEDIUM_CONFIDENCE  # Medium confidence for regex matches

        if parsed_dates:
            # If one date, assume start=end
            if len(parsed_dates) == 1:
                date_info["start_date"] = parsed_dates[0]
                date_info["end_date"] = parsed_dates[0]
            # If multiple dates, assume range (min/max)
            else:
                date_info["start_date"] = min(parsed_dates)
                date_info["end_date"] = max(parsed_dates)

            date_info["confidence"] = confidence

    # If we have dates, validate them
    if "start_date" in date_info and "end_date" in date_info:
        # Ensure start date is not after end date
        if date_info["start_date"] > date_info["end_date"]:
            date_info["start_date"], date_info["end_date"] = date_info["end_date"], date_info["start_date"]

        # If dates are too far apart (more than 1 year), it might be an error
        if (date_info["end_date"] - date_info["start_date"]).days > 365:
            logging.warning(f"Date range suspiciously large: {date_info['start_date']} to {date_info['end_date']}")
            if "confidence" in date_info:
                date_info["confidence"] *= 0.8  # Reduce confidence

    return date_info

def extract_category(query: str, doc: Any) -> Dict[str, Any]:
    """
    Extract expense category from the query with confidence score.

    Args:
        query: Cleaned user query
        doc: spaCy processed document

    Returns:
        Dictionary with category and confidence score, or empty dict if no category found
    """
    result = {}
    category_candidates = []

    # 1. Direct keyword matching (highest confidence)
    # Prioritize longer matches first (e.g., "household bill" over "bill")
    sorted_keywords = sorted(CATEGORY_MAPPING.keys(), key=len, reverse=True)

    for keyword in sorted_keywords:
        # Use word boundaries to ensure whole word match (case-insensitive)
        if re.search(r'\b' + re.escape(keyword) + r'\b', query, re.IGNORECASE):
            category_candidates.append((CATEGORY_MAPPING[keyword], HIGH_CONFIDENCE, "Direct keyword match"))
            break  # Stop after first match to avoid duplicates

    # 2. Fuzzy matching for typos and misspellings (medium confidence)
    if not category_candidates:
        # Get all words from the query
        words = query.split()

        for word in words:
            # Skip very short words
            if len(word) < 3:
                continue

            # Try fuzzy matching against category keywords
            for keyword in sorted_keywords:
                # Skip very short keywords
                if len(keyword) < 3:
                    continue

                # Calculate similarity ratio
                similarity = difflib.SequenceMatcher(None, word.lower(), keyword.lower()).ratio()

                # If similarity is high enough, consider it a match
                if similarity >= 0.8:  # 80% similarity threshold
                    category_candidates.append((CATEGORY_MAPPING[keyword], MEDIUM_CONFIDENCE * similarity, "Fuzzy keyword match"))

    # 3. Check for category-related entities from spaCy (lower confidence)
    if not category_candidates:
        # Look for PRODUCT entities that might indicate categories
        product_entities = [ent for ent in doc.ents if ent.label_ == "PRODUCT"]

        for ent in product_entities:
            ent_text_lower = ent.text.lower()

            # Direct match
            if ent_text_lower in CATEGORY_MAPPING:
                category_candidates.append((CATEGORY_MAPPING[ent_text_lower], MEDIUM_CONFIDENCE, "PRODUCT entity match"))
                continue

            # Fuzzy match
            for keyword in sorted_keywords:
                similarity = difflib.SequenceMatcher(None, ent_text_lower, keyword.lower()).ratio()
                if similarity >= 0.8:
                    category_candidates.append((CATEGORY_MAPPING[keyword], LOW_CONFIDENCE * similarity, "PRODUCT entity fuzzy match"))

    # 4. Context-based inference (lowest confidence)
    if not category_candidates:
        # Look for words that might indicate categories based on context
        context_indicators = {
            "Food": ["eat", "eating", "ate", "food", "meal", "restaurant", "lunch", "dinner", "breakfast", "snack", "grocery", "groceries"],
            "Travel": ["travel", "trip", "flight", "train", "bus", "taxi", "car", "gas", "fuel", "transportation"],
            "Entertainment": ["movie", "cinema", "concert", "show", "game", "entertainment", "fun", "ticket", "tickets"],
            "Household Bill": ["bill", "utility", "utilities", "rent", "electricity", "water", "internet", "phone", "household"],
            "Other": ["other", "miscellaneous", "misc", "general", "expense"]
        }

        # Count occurrences of context indicators for each category
        category_scores = {category: 0 for category in context_indicators.keys()}

        for category, indicators in context_indicators.items():
            for indicator in indicators:
                if re.search(r'\b' + re.escape(indicator) + r'\b', query, re.IGNORECASE):
                    category_scores[category] += 1

        # Get the category with the highest score
        max_score = max(category_scores.values())
        if max_score > 0:
            # Get all categories with the max score
            top_categories = [category for category, score in category_scores.items() if score == max_score]

            # If there's a tie, prefer more specific categories over "Other"
            if len(top_categories) > 1 and "Other" in top_categories:
                top_categories.remove("Other")

            category_candidates.append((top_categories[0], VERY_LOW_CONFIDENCE, "Context inference"))

    # Process results
    if category_candidates:
        # Sort by confidence (highest first)
        category_candidates.sort(key=lambda x: -x[1])

        # Get the highest confidence category
        best_category, best_confidence, source = category_candidates[0]

        result["category"] = best_category
        result["confidence"] = best_confidence
        result["source"] = source

        # Include alternatives if available
        if len(category_candidates) > 1:
            alternatives = []
            for category, conf, src in category_candidates[1:]:
                # Only include if different from the best category
                if category != best_category:
                    alternatives.append({
                        "category": category,
                        "confidence": conf,
                        "source": src
                    })
            if alternatives:
                result["alternatives"] = alternatives[:2]  # Limit to top 2 alternatives

    return result

def extract_amount(query: str, doc: Any) -> Dict[str, Any]:
    """
    Extract amount from the query with confidence score.

    Args:
        query: Cleaned user query
        doc: spaCy processed document

    Returns:
        Dictionary with amount and confidence score, or empty dict if no amount found
    """
    result = {}
    amounts_found = []
    confidences = []

    # Look for MONEY entities first (highest confidence)
    money_entities = [ent for ent in doc.ents if ent.label_ == "MONEY"]

    if money_entities:
        for ent in money_entities:
            # Clean the text: remove currency symbols, commas
            # More robust cleaning to handle various formats
            amount_text = re.sub(r'[^\d.]', '', ent.text)
            try:
                amount = Decimal(amount_text)
                if amount > 0:  # Ignore zero or negative amounts
                    amounts_found.append(amount)
                    confidences.append((amount, HIGH_CONFIDENCE, "MONEY entity"))
            except Exception:
                continue  # Ignore if conversion fails

    # Look for currency patterns with numbers
    # Enhanced regex to catch more currency formats
    currency_patterns = [
        # NPR/Rs followed by number
        r'(?:rs\.?|npr\.?|रु\.?|₨\.?|₹)\s*(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?)',
        # Number followed by NPR/Rs
        r'(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?)\s*(?:rs\.?|npr\.?|रु\.?|₨\.?|₹)',
        # Number with expense context
        r'(?:amount|cost|price|paid|spent|total)(?:\s+of)?\s+(?:rs\.?|npr\.?|रु\.?|₨\.?|₹)?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?)',
        # Number with expense context (reversed)
        r'(?:rs\.?|npr\.?|रु\.?|₨\.?|₹)?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?)\s+(?:amount|cost|price|total)'
    ]

    for pattern in currency_patterns:
        matches = re.finditer(pattern, query, re.IGNORECASE)
        for match in matches:
            # Remove commas from the number
            amount_text = match.group(1).replace(',', '')
            try:
                amount = Decimal(amount_text)
                if amount > 0:  # Ignore zero or negative amounts
                    amounts_found.append(amount)
                    confidences.append((amount, HIGH_CONFIDENCE, "Currency pattern"))
            except Exception:
                continue

    # If no high-confidence matches, look for CARDINAL entities
    if not confidences:
        cardinal_entities = [ent for ent in doc.ents if ent.label_ == "CARDINAL"]
        for ent in cardinal_entities:
            # Clean the text and check if it looks like a number
            amount_text = re.sub(r'[^\d.]', '', ent.text)
            if amount_text:
                try:
                    amount = Decimal(amount_text)
                    if amount > 0:  # Ignore zero or negative amounts
                        # Check context to determine if it's likely an amount
                        start = max(0, ent.start_char - 20)
                        end = min(len(query), ent.end_char + 20)
                        context = query[start:end]

                        # Higher confidence if amount-related words are nearby
                        if re.search(r'\b(amount|cost|price|paid|spent|total|rs|npr)\b', context, re.IGNORECASE):
                            confidences.append((amount, MEDIUM_CONFIDENCE, "CARDINAL with amount context"))
                        else:
                            # Lower confidence for bare numbers without context
                            confidences.append((amount, LOW_CONFIDENCE, "CARDINAL entity"))
                except Exception:
                    continue

    # Fallback: Look for standalone numbers that might be amounts
    if not confidences:
        # Find numbers not attached to other words
        number_pattern = r'\b(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?)\b'
        matches = re.finditer(number_pattern, query)
        for match in matches:
            amount_text = match.group(1).replace(',', '')
            try:
                amount = Decimal(amount_text)
                if amount > 0:  # Ignore zero or negative amounts
                    confidences.append((amount, VERY_LOW_CONFIDENCE, "Standalone number"))
            except Exception:
                continue

    # Process the results
    if confidences:
        # Sort by confidence (highest first), then by amount (largest first for ties)
        confidences.sort(key=lambda x: (-x[1], -x[0]))

        # Get the highest confidence amount
        best_amount, best_confidence, source = confidences[0]

        # Validate the amount (basic sanity check)
        if best_amount > 1000000:  # Very large amount (> 1 million)
            logging.warning(f"Suspiciously large amount detected: {best_amount} from {source}")
            best_confidence *= 0.7  # Reduce confidence

        result["amount"] = best_amount
        result["confidence"] = best_confidence
        result["source"] = source

        # Include alternatives if available and significantly different
        if len(confidences) > 1:
            alternatives = []
            for amount, conf, src in confidences[1:]:
                # Only include if significantly different (>10% difference)
                if abs((amount - best_amount) / best_amount) > 0.1:
                    alternatives.append({
                        "amount": amount,
                        "confidence": conf,
                        "source": src
                    })
            if alternatives:
                result["alternatives"] = alternatives[:2]  # Limit to top 2 alternatives

    return result

def extract_merchant(query: str, doc: Any) -> Dict[str, Any]:
    """
    Extract merchant name from the query with confidence score.

    Args:
        query: Cleaned user query
        doc: spaCy processed document

    Returns:
        Dictionary with merchant name and confidence score, or empty dict if no merchant found
    """
    result = {}

    # Look for ORG and FAC (facility) entities
    org_entities = [ent for ent in doc.ents if ent.label_ in ["ORG", "FAC"]]

    # Also look for PROPN (proper noun) sequences that might be merchant names
    propn_sequences = []
    current_sequence = []

    for token in doc:
        if token.pos_ == "PROPN":
            current_sequence.append(token)
        elif current_sequence:
            if len(current_sequence) >= 1:  # At least one proper noun
                propn_sequences.append(current_sequence)
            current_sequence = []

    # Add the last sequence if it exists
    if current_sequence and len(current_sequence) >= 1:
        propn_sequences.append(current_sequence)

    # Convert token sequences to text
    propn_texts = [" ".join([token.text for token in seq]) for seq in propn_sequences]

    # Merchant indicator keywords
    merchant_indicators = ["at", "from", "in", "near", "to", "shop", "store", "restaurant", "cafe", "bought", "purchased"]

    # 1. Look for entities near merchant indicator keywords (highest confidence)
    merchant_candidates = []

    # Check ORG/FAC entities first
    for ent in org_entities:
        # Check context around the entity (wider window)
        start = max(0, ent.start_char - 25)
        end = min(len(query), ent.end_char + 25)
        context = query[start:end]

        # Check if any merchant indicator is near the entity
        for indicator in merchant_indicators:
            if re.search(r'\b' + re.escape(indicator) + r'\b\s+' + re.escape(ent.text.lower()), context, re.IGNORECASE):
                merchant_candidates.append((ent.text, HIGH_CONFIDENCE, "ORG/FAC with indicator"))
                break

    # 2. Check proper noun sequences near merchant indicators
    for propn_text in propn_texts:
        # Skip very short proper nouns (likely not merchants)
        if len(propn_text) < 3:
            continue

        # Check context around the proper noun
        propn_pos = query.lower().find(propn_text.lower())
        if propn_pos >= 0:
            start = max(0, propn_pos - 25)
            end = min(len(query), propn_pos + len(propn_text) + 25)
            context = query[start:end]

            # Check if any merchant indicator is near the proper noun
            for indicator in merchant_indicators:
                if re.search(r'\b' + re.escape(indicator) + r'\b\s+', context, re.IGNORECASE) and \
                   propn_pos > context.lower().find(indicator.lower()):
                    merchant_candidates.append((propn_text, MEDIUM_CONFIDENCE, "PROPN with indicator"))
                    break

    # 3. If no candidates with indicators, consider all ORG/FAC entities (medium confidence)
    if not merchant_candidates and org_entities:
        for ent in org_entities:
            merchant_candidates.append((ent.text, MEDIUM_CONFIDENCE, "ORG/FAC entity"))

    # 4. If still no candidates, consider proper noun sequences (lower confidence)
    if not merchant_candidates and propn_texts:
        for propn_text in propn_texts:
            if len(propn_text) >= 3:  # Skip very short proper nouns
                merchant_candidates.append((propn_text, LOW_CONFIDENCE, "PROPN sequence"))

    # 5. Regex fallback for patterns like "at [Proper Noun Phrase]" (lowest confidence)
    if not merchant_candidates:
        # Enhanced pattern to catch more variations
        patterns = [
            r'\b(?:at|from|in|to)\s+([A-Z][a-zA-Z\s]+?)(?:\s+(?:on|for|when|yesterday|today|last|this|with|and|but|or|if|then|while|during|after|before|because|since|until|though|although|unless|once|while|where|whereas|whether)|\s*$)',
            r'\b(?:bought|purchased|ordered|got|paid)\s+(?:from|at)\s+([A-Z][a-zA-Z\s]+?)(?:\s+|$)',
            r'\b(?:shop|store|restaurant|cafe|market)\s+(?:called|named)?\s+([A-Z][a-zA-Z\s]+?)(?:\s+|$)'
        ]

        for pattern in patterns:
            match = re.search(pattern, query)
            if match:
                merchant_candidates.append((match.group(1).strip(), VERY_LOW_CONFIDENCE, "Regex pattern"))
                break

    # Process results
    if merchant_candidates:
        # Sort by confidence (highest first)
        merchant_candidates.sort(key=lambda x: -x[1])

        # Get the highest confidence merchant
        best_merchant, best_confidence, source = merchant_candidates[0]

        # Clean up the merchant name
        best_merchant = best_merchant.strip()

        # Validate the merchant name
        if len(best_merchant) < 2:  # Too short to be a valid merchant name
            return {}

        if len(best_merchant.split()) > 5:  # Too many words, likely not a merchant name
            best_confidence *= 0.7  # Reduce confidence

        result["merchant"] = best_merchant
        result["confidence"] = best_confidence
        result["source"] = source

        # Include alternatives if available
        if len(merchant_candidates) > 1:
            alternatives = []
            for merchant, conf, src in merchant_candidates[1:]:
                # Only include if different from the best merchant
                if merchant.lower() != best_merchant.lower():
                    alternatives.append({
                        "merchant": merchant.strip(),
                        "confidence": conf,
                        "source": src
                    })
            if alternatives:
                result["alternatives"] = alternatives[:2]  # Limit to top 2 alternatives

    return result

def calculate_confidence(intent_data: Dict[str, Any], entities: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate overall confidence score for the parsing with detailed explanation.

    Args:
        intent_data: Dictionary with intent, confidence, and evidence
        entities: Dictionary of extracted entities with their confidence scores

    Returns:
        Dictionary with overall confidence score and explanation
    """
    result = {}

    # Get intent and base confidence
    intent = intent_data.get("intent", INTENT_UNKNOWN)
    base_confidence = intent_data.get("confidence", VERY_LOW_CONFIDENCE)

    # Start with base confidence from intent
    confidence = base_confidence
    confidence_factors = [f"Base intent confidence: {base_confidence:.2f}"]

    # Get entity confidences
    amount_data = entities.get("amount", {})
    merchant_data = entities.get("merchant", {})
    category_data = entities.get("category", {})
    date_data = {}
    if "start_date" in entities:
        date_data["confidence"] = entities.get("confidence", MEDIUM_CONFIDENCE)

    # Adjust based on required entities for each intent
    if intent == INTENT_ADD_EXPENSE:
        # For add_expense, we need at least amount
        if not amount_data:
            confidence *= 0.5
            confidence_factors.append("Missing required 'amount' entity: -50%")
        else:
            amount_confidence = amount_data.get("confidence", MEDIUM_CONFIDENCE)
            # Weight the amount confidence (higher importance for add_expense)
            weighted_amount_confidence = amount_confidence * 1.5
            confidence = (confidence + weighted_amount_confidence) / 2
            confidence_factors.append(f"Amount entity confidence: {amount_confidence:.2f} (weighted: {weighted_amount_confidence:.2f})")

        # Boost if we have merchant
        if merchant_data:
            merchant_confidence = merchant_data.get("confidence", MEDIUM_CONFIDENCE)
            confidence = (confidence + merchant_confidence) / 2
            confidence_factors.append(f"Merchant entity confidence: {merchant_confidence:.2f}")

        # Boost if we have category
        if category_data:
            category_confidence = category_data.get("confidence", MEDIUM_CONFIDENCE)
            confidence = (confidence + category_confidence) / 2
            confidence_factors.append(f"Category entity confidence: {category_confidence:.2f}")

    elif intent in [INTENT_QUERY_SUM, INTENT_QUERY_LIST]:
        # For queries, we need at least category or date
        if not category_data and not date_data:
            confidence *= 0.5
            confidence_factors.append("Missing both 'category' and 'date' entities: -50%")
        else:
            # If we have category, factor in its confidence
            if category_data:
                category_confidence = category_data.get("confidence", MEDIUM_CONFIDENCE)
                confidence = (confidence + category_confidence) / 2
                confidence_factors.append(f"Category entity confidence: {category_confidence:.2f}")

            # If we have date, factor in its confidence
            if date_data:
                date_confidence = date_data.get("confidence", MEDIUM_CONFIDENCE)
                confidence = (confidence + date_confidence) / 2
                confidence_factors.append(f"Date entity confidence: {date_confidence:.2f}")

    # Check for intent alternatives that might be close
    if "alternatives" in intent_data:
        # If there's a close alternative, reduce confidence slightly
        confidence *= 0.9
        confidence_factors.append(f"Close alternative intent detected: -10%")

    # Cap at 1.0
    confidence = min(confidence, 1.0)

    # Classify confidence level
    confidence_level = "very low"
    if confidence >= HIGH_CONFIDENCE:
        confidence_level = "high"
    elif confidence >= MEDIUM_CONFIDENCE:
        confidence_level = "medium"
    elif confidence >= LOW_CONFIDENCE:
        confidence_level = "low"

    result["confidence"] = confidence
    result["confidence_level"] = confidence_level
    result["explanation"] = confidence_factors

    return result