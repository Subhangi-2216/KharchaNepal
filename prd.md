# Product Requirements Document: Kharcha Nepal Tracker

**Version:** 1.0
**Date:** 2024-07-27
**Authors:** Aasara Bade Shrestha, Subhangi Lamichhane

## 1. Introduction

Kharcha Nepal Tracker is a web-based personal expense management application designed to simplify financial tracking for users, primarily focusing on the Nepalese context (NPR currency). It leverages Optical Character Recognition (OCR) to automate the logging of expenses from printed receipts and incorporates an NLP-driven chatbot to provide users with interactive insights and data entry capabilities. The goal is to reduce manual data entry effort, minimize errors, and offer a seamless, user-friendly experience for tracking and understanding personal spending habits.

## 2. Goals

*   **Automate Expense Entry:** Significantly reduce manual data entry by accurately extracting key information (Merchant, Date, Amount) from uploaded receipt images using OCR.
*   **Simplify Expense Management:** Provide a centralized platform for users to log, view, categorize, filter, and manage their expenses efficiently.
*   **Enhance Financial Awareness:** Offer quick insights into spending patterns through a dashboard summary and an interactive query chatbot.
*   **Improve Accuracy:** Minimize errors associated with manual expense tracking through OCR assistance and user confirmation.
*   **Provide Convenience:** Offer a responsive web application accessible on both desktop and mobile devices, with features like direct bill upload.

## 3. Target Audience

*   Individuals residing in Nepal managing their personal budgets and expenses.
*   Tech-savvy users comfortable with web applications and looking for an automated expense tracking solution.
*   (Secondary) Freelancers or small business owners in Nepal needing a simple tool for tracking business-related expenses.

## 4. Key Use Cases

*   **User Registration & Login:** A user creates an account and logs in securely.
*   **OCR Expense Logging:** A user uploads a photo of a receipt; the system extracts data; the user verifies/corrects the data and selects a category before saving.
*   **Manual Expense Logging:** A user manually enters expense details (Merchant, Date, Amount, Category) through a form.
*   **Expense Review:** A user views a list of their logged expenses, filtering by date range or category.
*   **Dashboard Overview:** A user views a summary of their recent spending categorized visually on the dashboard.
*   **Report Generation:** A user generates a filtered list of expenses and downloads it as an Excel file.
*   **Chatbot Query:** A user asks the chatbot questions like "How much did I spend on food last week?" or "Show my travel expenses in January."
*   **Chatbot Logging:** A user instructs the chatbot to log an expense, e.g., "Add 500 NPR for lunch at Cafe XYZ today."
*   **Support Query:** A user asks the support chatbot basic questions about how to use the application.
*   **Profile Management:** A user updates their name, email, password, or profile picture.

## 5. Functional Requirements

### 5.1 User Authentication & Profile Management

*   **FR-AUTH-01:** Users shall be able to register for a new account using Name, Email, and Password. Email uniqueness must be enforced. Passwords must be securely hashed.
*   **FR-AUTH-02:** Registered users shall be able to log in using their Email and Password.
*   **FR-AUTH-03:** Upon successful login, the system shall issue a secure session token (JWT) to the user.
*   **FR-AUTH-04:** All subsequent requests requiring user authentication must include a valid JWT. The system must verify the token.
*   **FR-USER-01:** Logged-in users shall be able to view their profile details (Name, Email, Profile Image URL).
*   **FR-USER-02:** Logged-in users shall be able to update their Name and Email.
*   **FR-USER-03:** Logged-in users shall be able to change their password securely (requiring current password).
*   **FR-USER-04:** Logged-in users shall be able to upload/update their profile picture.

### 5.2 Expense Logging - OCR

*   **FR-OCR-01:** Users shall be able to upload an image file (e.g., JPG, PNG) containing a receipt through the web interface. Mobile users should ideally be able to use their device camera directly for capture and upload.
*   **FR-OCR-02:** The backend shall receive the uploaded image and perform pre-processing (e.g., grayscale, binarization, deskewing) to improve OCR quality.
*   **FR-OCR-03:** The backend shall use an OCR engine (e.g., Tesseract via `pytesseract`) to extract raw text from the pre-processed image.
*   **FR-OCR-04:** The backend shall attempt to parse the raw OCR text to identify and extract:
    *   Merchant/Organization Name
    *   Date of Expense
    *   Total Amount (assuming NPR currency)
*   **FR-OCR-05:** The system shall present the extracted Merchant, Date, and Amount to the user for confirmation/correction via the frontend.
*   **FR-OCR-06:** The user *must* select an expense category from a predefined list: `Food`, `Travel`, `Entertainment`, `Household Bill`, `Other`.
*   **FR-OCR-07:** Upon user confirmation (and potential correction), the system shall save the expense details (User ID, Confirmed Merchant, Confirmed Date, Confirmed Amount, Currency='NPR', Selected Category, `is_ocr_entry=True`, optionally `ocr_raw_text`, optionally `bill_image_path`) to the database.

### 5.3 Expense Logging - Manual

*   **FR-MAN-01:** Users shall be able to access a dedicated form for manual expense entry.
*   **FR-MAN-02:** The form shall include fields for: Merchant Name (text), Date (date picker), Amount (numeric, NPR assumed), Category (dropdown/select from predefined list).
*   **FR-MAN-03:** Upon submission, the system shall validate the input and save the expense details (User ID, Merchant, Date, Amount, Currency='NPR', Category, `is_ocr_entry=False`) to the database.

### 5.4 Expense Viewing & Management

*   **FR-VIEW-01:** Users shall be able to view a list of all their logged expenses, sorted by date (most recent first by default).
*   **FR-VIEW-02:** The expense list shall display key details: Date, Merchant Name, Category, Amount.
*   **FR-VIEW-03:** Users shall be able to filter the expense list by:
    *   Date Range (Start Date, End Date)
    *   Category (Single or multiple selections)
*   **FR-VIEW-04:** The expense list shall implement pagination to handle a large number of records efficiently.
*   **FR-EDIT-01:** Users shall be able to edit the details (Merchant, Date, Amount, Category) of any existing expense entry.
*   **FR-DEL-01:** Users shall be able to delete expense entries. A confirmation step is recommended.

### 5.5 Dashboard

*   **FR-DASH-01:** The dashboard shall display a summary of the user's total expenses grouped by category for a default period (e.g., the last 30 days).
*   **FR-DASH-02:** The dashboard shall include a visual representation (e.g., Pie Chart, Bar Chart) of the expense summary by category.

### 5.6 Reporting

*   **FR-REP-01:** Users shall be able to access a reporting section.
*   **FR-REP-02:** Users shall be able to filter the data for the report by:
    *   Date Range (Start Date, End Date)
    *   Category (Optional, single or multiple selections)
*   **FR-REP-03:** The system shall display the filtered expense data in a tabular format on the page.
*   **FR-REP-04:** Users shall be able to download the filtered expense data as an Excel (.xlsx) file.
*   **FR-REP-05:** The downloaded Excel file shall contain columns for at least: Date, Merchant Name, Category, Amount (NPR).

### 5.7 Chatbot - Expense Query & Add Assistant

*   **FR-CB-EXP-01:** An interactive chat interface shall be available within the application (e.g., accessible from the Expenses page).
*   **FR-CB-EXP-02:** The chatbot shall understand natural language queries related to viewing expense data. Examples:
    *   "How much did I spend on Food last week?"
    *   "Show my expenses from Jan 1st to Jan 15th"
    *   "What was my total spending in March?"
    *   "List travel expenses"
*   **FR-CB-EXP-03:** The chatbot shall understand natural language commands related to adding new expenses. Example:
    *   "Add Rs. 500 for Food at Bhatbhateni yesterday"
    *   "Log transport expense 150 NPR on March 5th"
*   **FR-CB-EXP-04:** The backend shall parse the user's input to identify the **intent** (e.g., query sum, query list, add expense) and extract **entities** (Amount, Currency, Category, Merchant/Place, Date/Date Range). (Initial implementation may use regex/keywords/spaCy; LLM NLU is a future enhancement).
*   **FR-CB-EXP-05:** Based on parsed intent and entities, the backend shall securely interact with the user's expense data in the database (perform reads or writes).
*   **FR-CB-EXP-06:** The chatbot shall provide clear, concise, and accurate responses to the user (e.g., calculated sums, lists of expenses, confirmation of added expenses). Error handling for misunderstood queries is required.

### 5.8 Chatbot - Support Assistant

*   **FR-CB-SUP-01:** A simple chat interface shall be available (e.g., on the Home page or a dedicated Help section).
*   **FR-CB-SUP-02:** The chatbot shall answer predefined frequently asked questions (FAQs) about using the Kharcha Nepal Tracker application.
*   **FR-CB-SUP-03:** The backend shall use a simple matching mechanism (e.g., keyword lookup, TF-IDF similarity, basic RAG) to map user queries to the most relevant predefined FAQ answer.
*   **FR-CB-SUP-04:** The chatbot shall respond with the predefined answer corresponding to the matched FAQ. If no relevant FAQ is found, it should indicate it cannot answer the question.

## 6. Non-Functional Requirements

*   **NFR-USA-01 (Usability):** The web application must have an intuitive and user-friendly interface, easy to navigate for non-technical users.
*   **NFR-USA-02 (Responsiveness):** The application UI must be responsive and function correctly on common desktop and mobile screen sizes.
*   **NFR-PERF-01 (OCR Speed):** OCR processing time should be reasonable (e.g., typically under 10-15 seconds per receipt, depending on complexity and server load). Provide user feedback during processing.
*   **NFR-PERF-02 (Chatbot Response):** Chatbot responses should be generated quickly (ideally under 2-3 seconds for non-LLM bots).
*   **NFR-PERF-03 (Query Speed):** Database queries for expense lists, dashboard, and reports should be optimized for fast loading times.
*   **NFR-ACC-01 (OCR Accuracy):** While 100% accuracy isn't guaranteed, OCR extraction should aim for high accuracy on clear receipt images. The user confirmation step mitigates inaccuracies.
*   **NFR-ACC-02 (Data Integrity):** Expense data saved must accurately reflect user input/confirmation. Chatbot queries must return factually correct results based on the stored data.
*   **NFR-SEC-01 (Authentication):** User authentication must be secure using JWTs with appropriate expiry and secure handling. Passwords must be securely hashed.
*   **NFR-SEC-02 (Authorization):** Users must only be able to access and modify their own expense data.
*   **NFR-SEC-03 (Input Validation):** All API endpoints must validate incoming data to prevent injection attacks and ensure data integrity. Use of an ORM like SQLAlchemy helps prevent basic SQL injection.
*   **NFR-SEC-04 (File Uploads):** Uploaded files should be handled securely (e.g., validation of file types, size limits, storing securely).
*   **NFR-REL-01 (Reliability):** The application should be stable and handle common errors gracefully (e.g., network issues, invalid input, OCR failures) without crashing.
*   **NFR-MAINT-01 (Maintainability):** Codebase (both backend and frontend) should be well-structured, modular, follow language-specific conventions, and include reasonable comments.
*   **NFR-CMP-01 (Compatibility):** The web application should be compatible with the latest versions of major web browsers (Chrome, Firefox, Safari, Edge).

## 7. Design Considerations

*   **UI/UX:** Clean, simple, and intuitive design focused on ease of expense logging and data visualization. Use the shadcn/ui component library built on TailwindCSS for a consistent look and feel.
*   **Feedback:** Provide clear visual feedback to users for actions like uploading receipts (processing state), saving data (success/failure), and chatbot interactions.
*   **Mobile First:** While responsive, prioritize a smooth experience on mobile devices, especially for receipt capture and quick logging.
*   **Currency:** Clearly indicate that amounts are in NPR throughout the interface.

## 8. Future Considerations / Out of Scope (Version 1.0)

*   Advanced automated expense categorization (ML-based suggestions).
*   Budgeting features (setting spending limits per category).
*   Support for recurring expenses.
*   Multi-currency support and automatic conversion.
*   Advanced reporting features (custom charts, PDF exports).
*   More sophisticated NLP for chatbots (e.g., handling complex conversational context, full LLM integration beyond basic NLU/RAG).
*   Integration with bank accounts or other financial services.
*   User sharing/group expense features.
*   Extensive unit and integration testing suites (focus on manual and core feature testing for V1).
*   Offline functionality.
*   Admin panel for application management.