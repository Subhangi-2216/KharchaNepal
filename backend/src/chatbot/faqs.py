# backend/src/chatbot/faqs.py
from typing import Dict, List, TypedDict

# Keywords indicating a query requires specific data -> Redirect
DATA_QUERY_KEYWORDS: List[str] = [
    'balance', 'spent', 'amount', 'how much', 'give me', 'can i see',
    'summary for', 'total for', 'report for', 'last week', 'last month', 
]

# Keywords that might appear in expense queries but relate to HOW-TO (Navigation)
# These might overlap with FAQ_KEYWORD_MAP keys and are handled there.
# Examples: 'expense', 'report', 'category', 'date', 'generate', 'download' 

EXPENSE_RELATED_KEYWORDS: List[str] = [
    'expense', 'expenses', 'report', 'reports', 'amount', 'spent', 'spend', 
    'category', 'date', 'month', 'generate', 'download', 'how much', 
    'can i see', 'give me', 'summary', 'total' 
]

REDIRECT_TO_EXPENSE_BOT_RESPONSE: str = "Please refer to the Expenses page and use the Expense Chatbot for this purpose."

DEFAULT_RESPONSE: str = "I'm sorry, I couldn't understand your question. Please try asking something like \"How to upload expenses?\" or \"How to generate a report?\""

class FaqItem(TypedDict):
    keywords: List[str]
    response: str

FAQ_KEYWORD_MAP: Dict[str, FaqItem] = {
    "greeting": {
        "keywords": ["hello", "hi", "hey", "greetings", "good morning", "good afternoon"],
        "response": "Hello! How can I help you navigate the expense tracker today?"
    },
    "feeling": {
        "keywords": ["how are you", "how you feeling", "hows it going"],
        "response": "I'm just a bot, but I'm ready to help you with your navigation questions!"
    },
    "add_expense": { # Renamed from upload_expenses for clarity
        "keywords": ["add", "enter", "submit", "expense", "expenses", "new expense"],
        "response": "To add an expense, go to the Expenses page. You have two options: 1. Add expenses manually by filling out the form, or 2. Use OCR by uploading a bill/receipt via the \"Scan Receipt\" button."
    },
    "upload_bill": { # More specific for OCR upload action
        "keywords": ["upload", "ocr", "scan", "receipt", "bill", "picture", "image"],
        "response": "To upload a bill/receipt for OCR, go to the Expenses page and click \"Scan Receipt\". Upload the image. The system will extract details, but you will need to manually select the Category before saving."
    },
    "track_expenses": { # New entry
        "keywords": ["track", "view expenses", "list expenses", "history", "transactions"],
        "response": "To track your expenses, go to the Expenses page. You can view a list of all your recorded expenses and filter them by date or category."
    },
    "generate_report": {
        # Removed 'generate', 'report', 'download' from keywords here to avoid false data query triggers
        # Rely on more specific phrases or context handled by DATA_QUERY_KEYWORDS for redirection.
        "keywords": ["create report", "make report", "get report", "view report", "see report", "summary report", "excel report"],
        "response": "To generate a report, go to the Reports page. Select the start date, end date, and category (optional). Click \"Generate Report\" to preview and download the report in Excel format."
    },
    "update_profile": {
        "keywords": ["update", "change", "edit", "profile", "setting", "settings", "name", "email", "password"],
        "response": "To update your profile, go to the Settings page. You can change your name, email, or password."
    },
    "view_dashboard": { # New entry
        "keywords": ["dashboard", "home", "overview", "summary chart"],
        "response": "You can view your dashboard on the Home page. It shows a summary of your expenses by category for the last 30 days, monthly total, and largest expense."
    },
    "logout": { # New entry
        "keywords": ["logout", "log out", "sign out", "signout"],
        "response": "To log out, click on your profile icon/avatar in the top-right corner of the sidebar and select \"Logout\" from the dropdown menu."
    },
    "purpose": {
        "keywords": ["help", "purpose", "what can you do", "assist", "support", "navigation"],
        "response": "I can help you with general questions about how to navigate the application, like how to upload expenses, generate reports, or update settings."
    }
}


DEFAULT_RESPONSE = "I don't have an answer for that yet." 