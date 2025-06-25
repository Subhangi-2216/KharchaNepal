# Project Status: OCR-Driven Expense Logging and NLP Chatbot

**Last Updated:** <Your Current Date>

This document tracks the progress of the Kharcha Nepal Tracker project against the requirements outlined in `requirements_project.md`.

**Legend:**
* ✅: Done
* ⏳: In Progress
* ❌: Not Started

## 1. Core Backend Setup & Foundation

*   [✅] Project Structure Initialized (FastAPI)
*   [✅] Virtual Environment & Core Dependencies Setup
*   [✅] Database Setup (PostgreSQL, SQLAlchemy)
*   [✅] Alembic Migrations Setup & Initial Migration
*   [✅] Environment Variable Configuration (`.env`)
*   [✅] Basic Logging Setup (Assumed via FastAPI defaults/Uvicorn)
*   [✅] CORS Middleware Configured
*   [✅] Root Endpoint (`/`) for Health Check

## 2. Database Schema / Models

*   [✅] `User` Model Defined (`models.py`)
*   [✅] `Expense` Model Defined (`models.py`, including `CategoryEnum`)
*   [✅] Relationships Defined (User <-> Expense)

## 3. Authentication Module (`auth/`)

*   [✅] User Registration Endpoint (`/api/auth/register`)
*   [✅] User Login Endpoint (`/api/auth/login` - returns JWT)
*   [✅] JWT Verification Middleware/Dependency (`auth/dependencies.py`)
*   [✅] Password Hashing (`auth/service.py`)
*   [✅] Get Current User Endpoint (`/api/auth/users/me`)

## 4. User Settings API (`src/user_settings/`)

*   [✅] Router & Schemas Defined
*   [✅] `GET /api/user/profile`: Fetch current user's details
*   [✅] `PUT /api/user/profile`: Update user's name, email
*   [✅] `PUT /api/user/password`: Update user's password
*   [✅] `PUT /api/user/profile/image`: Upload profile image (Assumed implementation detail)

## 5. Expense CRUD API & OCR (`src/expenses/` & `src/ocr/`)

*   [✅] Router & Schemas Defined (`src/expenses/`)
*   [✅] `POST /api/expenses/manual`: Create manual expense
*   [⏳] `POST /api/expenses/ocr`: Handles file upload.
    *   [✅] File Upload Endpoint Exists
    *   [⏳] OCR Service Integration (`pytesseract` - basic implementation likely done)
    *   [❌] Image Preprocessing (OpenCV - crucial enhancement)
    *   [⏳] Extraction Logic (Regex/NER - basic parsing likely done, needs spaCy enhancement)
    *   [✅] Saves partial expense (requires category update)
*   [✅] `PUT /api/expenses/{id}`: Update expense (used for adding category after OCR, corrections)
*   [✅] `GET /api/expenses`: List expenses (with filtering & pagination)
*   [✅] `DELETE /api/expenses/{id}`: Delete expense

## 6. Dashboard API (`src/dashboard/`)

*   [✅] Router & Schemas Defined
*   [✅] `GET /api/dashboard/summary`: Calculate and return expense summary (last 30 days by category)

## 7. Reporting API (`src/reports/`)

*   [✅] Router & Schemas Defined
*   [✅] `GET /api/reports/data`: Returns filtered expense data (JSON)
    *   [✅] Filtering Logic Implemented (`reports/service.py`)
*   [⏳] Excel Download (Frontend responsibility using fetched JSON data, or backend generation if preferred)

## 8. Chatbot API - Expense Query (`src/chatbot/`)

*   [✅] Router & Schemas Defined
*   [⏳] `POST /api/chatbot/query`: Endpoint exists.
    *   [❌] Basic NLP/Parsing Logic (Intent recognition, Entity extraction - Regex/spaCy pending)
    *   [❌] Database Interaction Logic (Querying/Inserting based on NLP result pending)
    *   [❌] Structured JSON Response Logic

## 9. Chatbot API - Support (`src/chatbot/`)

*   [✅] Router & Schemas Defined (`faqs.py` likely holds data)
*   [⏳] `POST /api/chatbot/support`: Endpoint exists.
    *   [⏳] Simple Keyword Matching / Predefined Answers (Basic implementation likely based on `faqs.py`)
    *   [❌] Advanced Matching (TF-IDF/RAG - Future enhancement)

## 10. Frontend

*   [✅] Project Setup (React, Vite, TypeScript)
*   [✅] Core Dependencies Setup
*   [✅] Styling Setup (TailwindCSS, shadcn/ui)
*   [✅] Basic Layout (`AppLayout`, `Sidebar`)
*   [✅] Routing Setup (Likely using `react-router-dom`)
*   [✅] UI Component Library (`components/ui/`)
*   [✅] Authentication Context/Pages (`AuthContext`, `LoginPage`, `RegisterPage`, `ProtectedRoute`)
*   [⏳] Expense Pages (Display, Manual Add, OCR Upload flow)
*   [⏳] Dashboard Page (Displaying summary)
*   [⏳] Reports Page (Displaying data, filtering, triggering download)
*   [⏳] Settings Page (User profile, password update)
*   [❌] Chatbot UI Integration

## Summary

The project has a very strong backend and frontend foundation. Authentication, core database models, migrations, and basic API structures for most features are in place. Expense CRUD (manual) and basic dashboard/reporting data fetching seem functional.

**Current Focus Areas:**
1.  Implementing and refining the OCR processing pipeline (preprocessing, robust extraction).
2.  Implementing the NLP logic for both chatbots.
3.  Completing the frontend UI flows for OCR upload, reporting interactions, and chatbot interfaces.
4.  Addressing the `backend/node_modules` structural issue.