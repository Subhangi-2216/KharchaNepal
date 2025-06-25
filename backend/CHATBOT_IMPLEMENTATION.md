# Chatbot Implementation for Kharcha Nepal

This document outlines the implementation of the chatbot functionality for the Kharcha Nepal expense tracking application.

## Features Implemented

1. **NLP Service for Expense Chatbot**
   - Intent recognition (query_sum, query_list, add_expense)
   - Entity extraction (dates, amounts, merchants, categories)
   - Confidence scoring

2. **Expense Chatbot Endpoint**
   - Database interaction for querying expenses
   - Database interaction for adding new expenses
   - Structured responses for different query types

3. **Enhanced Support Chatbot**
   - TF-IDF based matching for more robust FAQ responses
   - Fallback to keyword matching

4. **Tests**
   - Unit tests for the NLP service
   - Integration tests for the chatbot endpoints

## Dependencies

- spaCy with en_core_web_sm model
- dateparser
- scikit-learn (for TF-IDF vectorization)

## Installation

1. **Install Python Dependencies**
   ```bash
   cd backend
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Install spaCy Model**
   ```bash
   python install_spacy_model.py
   ```

## Testing

1. **Run Unit Tests**
   ```bash
   cd backend
   source .venv/bin/activate
   pytest tests/unit/chatbot
   ```

2. **Run Integration Tests**
   ```bash
   cd backend
   source .venv/bin/activate
   pytest tests/integration/test_chatbot_endpoints.py
   ```

## Usage

1. **Start the Server**
   ```bash
   cd backend
   source .venv/bin/activate
   uvicorn main:app --reload
   ```

2. **Test the Support Chatbot Endpoint**
   - Use a tool like Postman or curl to send a POST request to `/api/chatbot/support` with a query
   - Example curl command:
     ```bash
     curl -X POST "http://localhost:8000/api/chatbot/support" \
       -H "Authorization: Bearer YOUR_TOKEN" \
       -H "Content-Type: application/json" \
       -d '{"query": "How do I add an expense?"}'
     ```

3. **Test the Expense Chatbot Endpoint**
   - Use a tool like Postman or curl to send a POST request to `/api/chatbot/query` with a query
   - Example curl command:
     ```bash
     curl -X POST "http://localhost:8000/api/chatbot/query" \
       -H "Authorization: Bearer YOUR_TOKEN" \
       -H "Content-Type: application/json" \
       -d '{"query": "How much did I spend on food last month?"}'
     ```

## Code Structure

- `src/chatbot/nlp_service.py`: NLP service for parsing expense chatbot queries
- `src/chatbot/tfidf_service.py`: TF-IDF service for more robust FAQ matching
- `src/chatbot/router.py`: API endpoints for both chatbots
- `src/chatbot/faqs.py`: FAQ data for the support chatbot
- `src/chatbot/schemas.py`: Pydantic models for request and response schemas
- `tests/unit/chatbot/test_nlp_service.py`: Unit tests for the NLP service
- `tests/integration/test_chatbot_endpoints.py`: Integration tests for the chatbot endpoints

## Future Improvements

1. **Improve NLP Accuracy**
   - Fine-tune the spaCy model for better entity recognition
   - Add more training data for intent recognition

2. **Enhance TF-IDF Matching**
   - Add more FAQ entries
   - Implement a feedback loop to improve matching over time

3. **Add More Query Types**
   - Support for more complex queries (e.g., "What's my average spending on food?")
   - Support for queries with multiple conditions (e.g., "Show me expenses over 1000 NPR for travel")

4. **Implement Conversational Context**
   - Remember previous queries for follow-up questions
   - Support for multi-turn conversations