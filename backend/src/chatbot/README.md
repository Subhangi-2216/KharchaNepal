# Chatbot Module for Kharcha Nepal

This module implements two chatbot functionalities for the Kharcha Nepal expense tracker:

1. **Support Chatbot**: Provides answers to general questions about the application.
2. **Expense Chatbot**: Allows users to query their expenses and add new expenses using natural language.

## Features

### Support Chatbot

- Keyword-based matching for FAQ responses
- TF-IDF based matching for more robust FAQ responses
- Redirection to Expense Chatbot for data-specific queries

### Expense Chatbot

- Natural language processing for intent recognition
- Entity extraction for dates, amounts, merchants, and categories
- Database interaction for querying expenses and adding new expenses
- Structured responses for different query types

## Implementation

### Support Chatbot

The support chatbot uses a combination of keyword matching and TF-IDF vectorization to match user queries to predefined FAQ responses. It also detects when a query is about expense data and redirects the user to the Expense Chatbot.

### Expense Chatbot

The expense chatbot uses spaCy for natural language processing to:

1. Detect the intent of the query (sum, list, add)
2. Extract entities like dates, amounts, merchants, and categories
3. Interact with the database based on the intent and entities
4. Format the response based on the query type

## API Endpoints

### Support Chatbot

```
POST /api/chatbot/support
```

Request body:
```json
{
  "query": "How do I add an expense?"
}
```

Response:
```json
{
  "response_type": "answer",
  "data": "To add an expense, go to the Expenses page. You have two options: 1. Add expenses manually by filling out the form, or 2. Use OCR by uploading a bill/receipt via the \"Scan Receipt\" button."
}
```

### Expense Chatbot

```
POST /api/chatbot/query
```

Request body:
```json
{
  "query": "How much did I spend on food last month?"
}
```

Response:
```json
{
  "response_type": "answer",
  "data": "You spent NPR 1500.00 on Food from 2023-01-01 to 2023-01-31."
}
```

## Dependencies

- spaCy with en_core_web_sm model
- dateparser
- scikit-learn (for TF-IDF vectorization)

## Testing

Unit tests for the NLP service and integration tests for the chatbot endpoints are available in the `tests` directory.

To run the tests:

```bash
pytest tests/unit/chatbot
pytest tests/integration/test_chatbot_endpoints.py
```