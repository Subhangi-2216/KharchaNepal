# Kharcha Nepal Tracker - Backend Development Guide

**Version:** 1.0
**Date:** 2024-07-27

## 1. Introduction

This document outlines the next steps for developing the backend of the Kharcha Nepal Tracker application. The project currently has a solid foundation with FastAPI, SQLAlchemy, Alembic migrations, JWT authentication, and a modular structure within the `src/` directory.

The immediate focus is on implementing and refining the **OCR processing pipeline** for expense receipts and building the core logic for the **NLP-driven chatbots**.

## 2. Prerequisites & Setup

Ensure you have the following installed:

*   Python (~3.13 recommended, based on `.venv`)
*   `pip` (Python package installer)
*   PostgreSQL Server (Running locally or accessible)
*   **(System Dependency)** Tesseract OCR engine:
    *   macOS (Brew): `brew install tesseract`
    *   Debian/Ubuntu: `sudo apt-get update && sudo apt-get install tesseract-ocr`
    *   Other OS: Follow official Tesseract installation guides.
*   **(System Dependency - Optional but Recommended for Step 1)** OpenCV libraries:
    *   macOS (Brew): `brew install opencv`
    *   Debian/Ubuntu: `sudo apt-get update && sudo apt-get install libopencv-dev python3-opencv` (or build from source if needed)

**Setup Steps:**

1.  **Clone the repository** (if not already done).
2.  **Navigate to the `backend` directory:**
    ```bash
    cd path/to/subhangi-2216-kharchanepal/backend
    ```
3.  **Create/Activate Virtual Environment:**
    ```bash
    # If .venv doesn't exist or needs recreation
    python3 -m venv .venv

    # Activate the environment (adjust path if necessary)
    # Linux/macOS:
    source .venv/bin/activate
    # Windows (Git Bash/WSL):
    # source .venv/Scripts/activate
    # Windows (CMD):
    # .venv\Scripts\activate.bat
    # Windows (PowerShell):
    # .venv\Scripts\Activate.ps1
    ```
4.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
5.  **Configure Environment Variables:**
    *   Copy `.env.example` to `.env` (if an example file exists) or create `.env`.
    *   Ensure `DATABASE_URL` points to your running PostgreSQL database (e.g., `postgresql+asyncpg://user:password@host:port/dbname`).
    *   Ensure `JWT_SECRET_KEY` is set to a secure random string.
6.  **Setup Database:**
    *   Ensure your PostgreSQL database exists.
    *   Apply database migrations:
        ```bash
        alembic upgrade head
        ```

## 3. Core Next Steps Roadmap

1.  **Integrate OCR Preprocessing (OpenCV):** Enhance image quality before sending to Tesseract.
2.  **Refine Expense OCR Endpoint (`/api/expenses/ocr`):** Solidify the workflow, handle errors, and manage partial saves correctly.
3.  **Enhance OCR Parsing (spaCy NER):** Replace basic regex/keyword parsing with more robust NLP for extracting date, amount, and merchant.
4.  **Implement Expense Chatbot Core Logic (`/api/chatbot/query`):** Build the NLP service to parse queries/commands and implement the router logic to interact with the database.
5.  **Implement Unit & Integration Tests (pytest):** Add tests for OCR, chatbot NLP, and API endpoints.
6.  **(Optional) Refine Support Chatbot (`/api/chatbot/support`):** Improve FAQ matching beyond basic keywords if needed.

## 4. Detailed Instructions & Commands

### Step 1: Integrate OCR Preprocessing (OpenCV)

*   **Goal:** Improve raw OCR text quality.
*   **Dependencies:** Add OpenCV.
    ```bash
    # Ensure virtual env is active
    pip install opencv-python-headless
    # Add 'opencv-python-headless' to requirements.txt
    pip freeze > requirements.txt
    ```
    *(Note: System libraries might also be needed - see Prerequisites)*
*   **Code Location:** `src/ocr/service.py` (modify `process_image_with_ocr`) and `src/ocr/preprocessing.py`.
*   **Action:**
    1.  In `src/ocr/service.py::process_image_with_ocr`:
        *   Import necessary modules: `import cv2`, `import numpy as np`, `from . import preprocessing`.
        *   Replace `img = Image.open(io.BytesIO(image_bytes))` with OpenCV loading:
            ```python
            nparr = np.frombuffer(image_bytes, np.uint8)
            img_cv = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img_cv is None:
                print("Error: Failed to decode image with OpenCV")
                return "" # Or raise error
            ```
        *   Apply preprocessing steps *before* Pytesseract (start simple):
            ```python
            processed_img = preprocessing.grayscale(img_cv)
            # Optionally add more steps - test incrementally
            # processed_img = preprocessing.threshold(processed_img)
            # processed_img = preprocessing.deskew(processed_img) # Deskew usually benefits binary images
            # processed_img = preprocessing.denoise(processed_img) # Denoise typically before thresholding
            ```
        *   Pass the *preprocessed OpenCV image* (NumPy array) to Pytesseract:
            ```python
            text = pytesseract.image_to_string(processed_img) # Pass the NumPy array directly
            ```
*   **Testing:** Use tools like Postman or `curl` to send receipt images to the `/api/expenses/ocr` endpoint. Check the backend logs for the raw `text` output. Compare results with and without preprocessing steps enabled.

### Step 2: Refine Expense OCR Endpoint (`/api/expenses/ocr`)

*   **Goal:** Robustly handle OCR results, errors, and partial saves.
*   **Code Location:** `src/expenses/router.py` (`create_expense_ocr`).
*   **Action:**
    1.  **After calling `parse_ocr_text`:** Check if the mandatory `amount` was successfully extracted (`extracted_dict.get('amount') is not None`).
    2.  **If Amount is Missing:**
        *   Log the failure.
        *   Raise `HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OCR failed to extract the mandatory 'amount' field. Please update manually.")`.
        *   *(Consider: Should you still return partial data in the error response?)*
    3.  **If Amount is Present:**
        *   Proceed to create the `Expense` object in the database with `category=None`, `is_ocr_entry=True`, and populate other fields from `extracted_dict` (using defaults like `date.today()` if necessary).
        *   Ensure the `user_id` is set correctly from `current_user`.
        *   Save the `ocr_raw_text` to the database record.
        *   Commit the transaction (`await db.commit()`). Handle potential database errors with rollback (`await db.rollback()`).
        *   Construct and return the `ExpenseOCRResponse` containing the `expense_id` of the newly created record, the `extracted_data`, and a list of `missing_fields` (always including "category").
*   **Testing:** Test with images where:
    *   All fields are likely found.
    *   Amount is clearly missing or unparseable.
    *   Date or merchant might be missing.
    *   Check the database state and API responses in each case. Verify error handling and rollbacks.

### Step 3: Enhance OCR Parsing (spaCy NER)

*   **Goal:** Improve extraction accuracy for date, amount, and merchant.
*   **Dependencies:** Add spaCy and a model.
    ```bash
    # Ensure virtual env is active
    pip install spacy dateparser # dateparser is highly recommended for flexible date parsing
    python -m spacy download en_core_web_sm
    # Add 'spacy', 'dateparser' to requirements.txt
    pip freeze > requirements.txt
    ```
*   **Code Location:** `src/ocr/service.py` (modify `parse_ocr_text`, `parse_date`, `parse_amount`, `parse_merchant` or create new spaCy-based versions).
*   **Action:**
    1.  **Load Model:** Load the spaCy model once (can be done globally in the module or within the function). `nlp = spacy.load("en_core_web_sm")`.
    2.  **Process Text:** `doc = nlp(ocr_raw_text)`.
    3.  **Extract Entities:**
        *   **Date:** Find `ent.label_ == "DATE"`. Use `dateparser.parse(ent.text)` for robust parsing. Handle multiple date entities (e.g., pick the first valid one or based on context).
        *   **Amount:** Find `ent.label_ == "MONEY"` or (`ent.label_ == "CARDINAL"` and looks like currency). Clean the text (`ent.text.replace('Rs.', '').replace(',', '').strip()`). Convert to `Decimal`. Apply heuristics (largest value, near keywords) to find the total.
        *   **Merchant:** Find `ent.label_ == "ORG"`. Apply heuristics (e.g., first ORG near the top, not matching common non-merchant orgs). Consider simple string matching against known local merchants as a fallback/boost.
    4.  Update the `parse_ocr_text` function to use these spaCy-based extractions.
*   **Testing:** Create a simple script or use an interactive Python session (`python -i`) to test the modified parsing functions with various raw OCR text examples saved from previous steps. Compare results with the old regex method.

### Step 4: Implement Expense Chatbot Core Logic (`/api/chatbot/query`)

*   **Goal:** Process user commands to query or add expenses.
*   **Code Location:** Create `src/chatbot/nlp_service.py` and implement logic in `src/chatbot/router.py` (`POST /api/chatbot/query`).
*   **Action (`nlp_service.py`):**
    1.  Define `parse_expense_query(query: str) -> Dict`:
        *   Use spaCy for NER (like Step 3) to extract `DATE`, `MONEY`, `ORG`, potentially numbers (`CARDINAL`).
        *   Use keyword matching (e.g., check for presence of category enum values like "food", "travel").
        *   Use rule-based logic for intent:
            *   If "add", "log", "record" -> `intent = "add_expense"`
            *   If "how much", "total", "sum" -> `intent = "query_sum"`
            *   If "show", "list", "what were" -> `intent = "query_list"`
        *   Return a dict: `{"intent": "...", "entities": {"amount": ..., "date": ..., "category": ..., "merchant": ...}}`
*   **Action (`router.py`):**
    1.  Implement the `POST /api/chatbot/query` endpoint.
    2.  Call `parse_expense_query` from the `nlp_service`.
    3.  Based on the returned `intent`:
        *   **`query_sum` / `query_list`:** Build a SQLAlchemy `select` statement using `entities` to filter by `user_id`, date range, category, etc. Use `func.sum` for totals. Execute the query (`await db.execute(...)`). Format the results into a user-friendly string.
        *   **`add_expense`:** Validate that required `entities` (amount, date, category) were extracted. Create a new `Expense` object and save it to the database (`db.add(...)`, `await db.commit()`). Format a confirmation message.
    4.  Handle cases where parsing fails or required entities are missing.
    5.  Return the formatted message in the `ChatbotResponse`.
*   **Testing:** Use API tools (Postman, curl) to send various queries ("add 100 for food", "how much food last month", "list travel expenses"). Verify intents, extracted entities, database interactions (check DB directly), and response messages.

### Step 5: Implement Unit & Integration Tests

*   **Goal:** Ensure code reliability and catch regressions.
*   **Dependencies:**
    ```bash
    # Ensure virtual env is active
    pip install pytest pytest-asyncio httpx
    # Add to requirements-dev.txt or requirements.txt
    pip freeze > requirements.txt # Or requirements-dev.txt
    ```
*   **Action:**
    1.  Create `backend/tests/` directory.
    2.  Create `tests/unit/` and `tests/integration/`.
    3.  **Unit Tests:** Write `pytest` tests for functions in `src/ocr/service.py` (parsing functions), `src/chatbot/nlp_service.py` (query parsing), `src/reports/service.py` (data fetching/formatting). Use sample inputs and assert expected outputs.
    4.  **Integration Tests:** Write `pytest` tests using `httpx.AsyncClient` against FastAPI's `TestClient`. Test API endpoints:
        *   Auth: Register, Login, Get Me.
        *   Expenses: Manual Create, OCR Upload (mock OCR/parsing if needed or test end-to-end), Update, List, Delete.
        *   Reports: Get Data, Download (check response status/headers).
        *   Chatbot: Test query/add intents.
*   **Running Tests:**
    ```bash
    # Ensure virtual env is active
    pytest tests/
    ```

### Step 6: (Optional) Refine Support Chatbot

*   **Goal:** Improve FAQ matching robustness.
*   **Action (TF-IDF):**
    *   Add `scikit-learn` to `requirements.txt`.
    *   In `chatbot/router.py` (`handle_support_query`):
        *   Fit a `TfidfVectorizer` on the `keywords` or combined text of your FAQs.
        *   Transform the user query using the same vectorizer.
        *   Calculate `cosine_similarity` between the user query vector and all FAQ vectors.
        *   Return the response corresponding to the highest similarity score above a certain threshold.
*   **Action (RAG):**
    *   More involved: requires `sentence-transformers` and a vector DB (`chromadb`, `faiss-cpu`). Involves embedding FAQs, embedding user query, performing vector search, and providing context to an LLM (if used) or just returning the best match. Likely out of scope unless specifically desired.

## 5. General Development Notes

*   **Git:** Use feature branches for development (`git checkout -b feature/ocr-preprocessing`). Make small, atomic commits with clear messages (`git commit -m "feat: Add OpenCV grayscale preprocessing"`). Create Pull Requests for review if working in a team.
*   **Linting/Formatting:** Use linters/formatters (like `ruff`, `black`, `flake8`, `mypy`) to maintain code quality. Configure your IDE or run them manually.
*   **Logging:** Add informative logging (`import logging`) within your endpoints and services, especially around complex logic (OCR, parsing, chatbot) and error handling.
*   **Dependencies:** Keep `requirements.txt` updated (`pip freeze > requirements.txt`) after installing new packages.
*   **Secrets:** **Never** commit `.env` files or API keys directly into the code or Git history.

## 6. Running the Application

```bash
# Ensure virtual env is active
# Navigate to the backend directory
uvicorn main:app --reload --port 8000