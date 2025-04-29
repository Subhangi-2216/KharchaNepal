**1\. Context:**

* We are building the backend API service for a personal expense tracker web application.  
* The frontend UI design includes features like:  
  * User authentication and profile settings.  
  * Manual expense entry (Merchant, Date, Amount NPR, Category).  
  * Bill upload with OCR to extract Merchant, Date, Amount (NPR), requiring manual Category selection post-OCR.  
  * A dashboard showing expense summaries (last 30 days by category).  
  * Expense reporting with date and category filters, downloadable as an Excel file.  
  * An "Expense Query Assistant" chatbot integrated into the Expenses page for database queries (e.g., "How much spent on Food last week?", "Add expense...").  
  * A simple "Support Assistant" chatbot on the Home page for predefined FAQs.  
* The primary currency for all transactions is Nepalese Rupees (NPR).  
* This backend needs to provide all necessary API endpoints and logic to support the described frontend functionality.

**2\. Project Description:**

Develop a robust and scalable backend API for the personal expense tracker. This includes setting up the project structure, implementing user authentication, defining database models, creating CRUD operations for expenses, integrating an OCR service/library for bill processing, implementing report generation logic, and building endpoints for the two distinct chatbot functionalities.

**3\. Suggested Technology Stack (Flexible \- Adapt if you have preferences):**

* **Language/Framework:** Python with FastAPI or Flask (Alternatively: Node.js with Express)  
* **Database:** PostgreSQL (Alternatively: MongoDB) \- Ensure data types can handle currency accurately (e.g., DECIMAL or storing cents as INTEGER).  
* **Authentication:** JWT (JSON Web Tokens) for securing endpoints.  
* **OCR:** Integration with a Python library (e.g., `pytesseract` wrapper for Tesseract OCR \- requires Tesseract installation) or a cloud-based OCR service API (e.g., Google Cloud Vision AI, AWS Textract). Start with a basic implementation assumption.  
* **Dependencies:** Use a requirements file (`requirements.txt` for Python, `package.json` for Node.js).

**4\. Rules & Guiding Principles:**

* **API Design:** Follow RESTful principles for API endpoint design. Use clear and consistent naming conventions.  
* **Authentication:** Secure all endpoints handling user-specific data using JWT authentication. Implement proper login/registration flows.  
* **Validation:** Implement input validation for all incoming API requests (payloads, query parameters).  
* **Error Handling:** Implement consistent and informative error handling. Return appropriate HTTP status codes and JSON error messages.  
* **Configuration:** Use environment variables for sensitive information (database credentials, JWT secret key, OCR API keys) and deployment-specific settings.  
* **Code Quality:** Write clean, well-commented, and maintainable code. Follow standard linting practices for the chosen language.  
* **Database:** Use an ORM (like SQLAlchemy for Python/PostgreSQL, Mongoose for Node.js/MongoDB) for database interactions where appropriate. Define clear models/schemas.  
* **Asynchronous Operations:** Consider asynchronous tasks for potentially long-running operations like OCR processing if using external APIs or complex local processing.

**5\. To-Do / Core Implementation Tasks:**

* **\[ \] Project Setup:** Initialize project structure (e.g., folders for routes/controllers, models, services, utils, config, tests). Set up virtual environment/dependencies.  
* **\[ \] Database Schema/Models:** Define models/schemas for:  
  * `User`: (id, name, email, hashed\_password, created\_at, updated\_at, profile\_image\_url)  
  * `Expense`: (id, user\_id, merchant\_name, date, amount, currency (default 'NPR'), category \[enum/string: Food, Travel, Entertainment, Household Bill, Other\], is\_ocr\_entry \[boolean\], ocr\_raw\_text \[optional text\], created\_at, updated\_at)  
* **\[ \] Authentication Module:**  
  * Implement user registration endpoint.  
  * Implement user login endpoint (returning JWT).  
  * Implement middleware/decorator for verifying JWT on protected routes.  
* **\[ \] User Settings API:**  
  * `GET /api/user/profile`: Fetch current user's details.  
  * `PUT /api/user/profile`: Update user's name, email.  
  * `PUT /api/user/password`: Update user's password.  
* **\[ \] Expense CRUD API:**  
  * `POST /api/expenses/manual`: Create an expense via manual input.  
  * `POST /api/expenses/ocr`: Handles file upload. Trigger OCR processing (internal function/service). Return extracted fields (date, amount, merchant) *or* save partially and require a follow-up PUT/PATCH after user selects category. *Decision: Let's assume it saves the expense with extracted data and marks `category` as null/pending, requiring a subsequent `PUT /api/expenses/{id}` to add the category.*  
  * `PUT /api/expenses/{id}`: Update an existing expense (e.g., to add category after OCR, or correct details).  
  * `GET /api/expenses`: List expenses for the authenticated user (implement filtering by date range and category, and pagination).  
  * `DELETE /api/expenses/{id}`: Delete an expense.  
* **\[ \] OCR Integration:**  
  * Implement a service/function that takes an image file (bytes or path).  
  * Calls the chosen OCR library/API.  
  * Parses the OCR result to extract relevant fields (Date, Total Amount, potential Merchant Name). Handle potential parsing errors gracefully.  
* **\[ \] Dashboard API:**  
  * `GET /api/dashboard/summary`: Calculate and return total expenses grouped by category for the last 30 days for the authenticated user.  
* **\[ \] Reporting API:**  
  * `GET /api/reports/data`: Accepts `startDate`, `endDate`, and `category` (optional, multiple) query parameters. Returns a JSON array of filtered expense data suitable for frontend conversion to Excel.  
* **\[ \] Chatbot API \- Expense Query:**  
  * `POST /api/chatbot/query`: Accepts a natural language query string.  
  * Implement basic NLP/parsing to understand intent (e.g., query amount, list expenses, add expense). *Start simple: focus on "how much spent on X category between Y and Z dates?" and maybe "add expense..."*.  
  * Interact with the database based on parsed intent.  
  * Return a structured JSON response (e.g., `{ "response_type": "answer", "data": "You spent NPR 1500 on Food" }` or `{ "response_type": "confirmation", "data": "OK. Added NPR 500 for Food at Bhatbhateni on Jan 25th." }`).  
* **\[ \] Chatbot API \- Support:**  
  * `POST /api/chatbot/support`: Accepts a query string.  
  * Implement simple keyword matching or basic intent recognition to return predefined answers for common FAQs.  
* **\[ \] Basic Logging:** Implement logging for requests, errors, and key events.  
* **\[ \] Environment Configuration:** Set up `.env` file support.

**6\. Backlog / Future Considerations:**

* Advanced NLP/AI integration for the query chatbot to handle more complex queries.  
* Budgeting features (setting limits per category).  
* Support for recurring expenses.  
* More sophisticated reporting options (charts within reports, different file formats).  
* Integration with multiple OCR providers or allowing user selection.  
* Unit and Integration tests.  
* Rate limiting for API endpoints.  
* Admin panel (if needed in the future).

FAQ_RESPONSES = {
    "topic_identifier_1": {
        "keywords": ["word1", "word2", "word3"],
        "response": "Answer 1"
    },
    "topic_identifier_2": {
        "keywords": ["word4", "word5"],
        "response": "Answer 2"
    }
}

