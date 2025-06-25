# Project Structure: Kharcha Nepal Tracker

This document outlines the directory structure for the OCR-Driven Expense Logging and NLP Chatbot project (`Kharcha Nepal Tracker`). The structure is designed to promote modularity, maintainability, and separation of concerns between the backend API and the frontend application.

## Top-Level Structure

ssubhangi-2216-kharchanepal/
├── backend/ # FastAPI Backend Application
├── frontend/ # React Frontend Application
├── .gitignore # Git ignore rules for the whole project
├── README.md # Main project README
├── requirements_project.md # Detailed project requirements & tasks
└── .cursor/ # IDE-specific configuration (can be ignored)


*   **`backend/`**: Contains all code related to the Python FastAPI server, including API logic, database interaction, authentication, OCR processing, and chatbot logic.
*   **`frontend/`**: Contains all code related to the React user interface, including components, pages, styling, state management, and API interactions.
*   **`.gitignore`**: Specifies intentionally untracked files that Git should ignore (e.g., virtual environments, dependency folders, environment files, secrets, logs, uploads).
*   **`README.md`**: Provides an overview of the project, setup instructions, and other relevant information.
*   **`requirements_project.md`**: A detailed breakdown of project features, API endpoints, and tasks (serves as a mini-spec).

## Backend Structure (`backend/`)

The backend follows standard practices for a FastAPI application with SQLAlchemy and Alembic.

backend/
├── alembic.ini # Alembic configuration file
├── config.py # Application configuration (e.g., loading .env)
├── database.py # SQLAlchemy engine, session setup, Base model
├── main.py # FastAPI application instance, middleware, root endpoint, router includes
├── models.py # SQLAlchemy ORM models (User, Expense, etc.)
├── requirements.txt # Python dependencies
├── .env # Environment variables (DB URL, JWT Secret) - DO NOT COMMIT
├── .gitignore # Backend-specific git ignore rules
├── alembic/ # Database migration scripts
│ ├── env.py
│ ├── README
│ ├── script.py.mako
│ └── versions/
│ └── ... migration_files.py ...
├── src/ # Main application source code directory
│ ├── init.py # Makes 'src' a package (optional but good practice)
│ ├── auth/ # Authentication logic
│ │ ├── init.py
│ │ ├── dependencies.py # FastAPI dependencies (e.g., get_current_user)
│ │ ├── router.py # API routes for /auth
│ │ ├── schemas.py # Pydantic schemas for auth requests/responses
│ │ └── service.py # Business logic (password hashing, JWT creation, user lookup)
│ ├── chatbot/ # Chatbot related logic
│ │ ├── init.py
│ │ ├── faqs.py # Data/logic for support chatbot
│ │ ├── nlp_service.py # (Recommended) NLP processing logic (spaCy, intent/entity extraction)
│ │ ├── router.py # API routes for /chatbot
│ │ └── schemas.py # Pydantic schemas for chatbot requests/responses
│ ├── dashboard/ # Dashboard specific logic
│ │ ├── init.py
│ │ ├── router.py # API routes for /dashboard
│ │ └── schemas.py # Pydantic schemas for dashboard data
│ ├── expenses/ # Expense management logic (excluding OCR processing)
│ │ ├── init.py
│ │ ├── router.py # API routes for /expenses (manual add, list, update, delete)
│ │ └── schemas.py # Pydantic schemas for expenses
│ ├── ocr/ # OCR processing logic (NEW - Recommended)
│ │ ├── init.py
│ │ ├── preprocessing.py # (Recommended) OpenCV image preprocessing
│ │ ├── service.py # OCR execution (Pytesseract) and basic text parsing/extraction
│ │ └── schemas.py # Pydantic schemas if needed for OCR results
│ ├── reports/ # Reporting logic
│ │ ├── init.py
│ │ ├── router.py # API routes for /reports
│ │ ├── schemas.py # Pydantic schemas for report data
│ │ └── service.py # Logic for fetching/filtering report data
│ └── user_settings/ # User profile and settings logic
│ ├── init.py
│ ├── router.py # API routes for /user
│ └── schemas.py # Pydantic schemas for user profile/settings
├── uploads/ # Directory for user-uploaded files (e.g., receipts, profile pics) - Should be in .gitignore
│ └── profile_images/
└── .venv/ # Python virtual environment - Should be in .gitignore
└── ...


*   **Configuration (`config.py`, `.env`)**: Centralized configuration loading.
*   **Database (`database.py`, `models.py`, `alembic/`)**: Clear separation of database connection, ORM models, and migrations.
*   **Entry Point (`main.py`)**: Initializes the FastAPI app and includes modular routers.
*   **Source Code (`src/`)**: Contains the core application logic, organized by feature (auth, chatbot, expenses, ocr, reports, etc.).
    *   Each feature module typically contains:
        *   `router.py`: Defines API endpoints using FastAPI's `APIRouter`.
        *   `schemas.py`: Defines Pydantic models for request/response validation and serialization.
        *   `service.py` (Optional but Recommended): Contains business logic separated from the router handlers.
        *   `dependencies.py` (Optional): Defines reusable FastAPI dependencies for the module.
*   **Uploads (`uploads/`)**: A designated, potentially ignored-by-git, location for storing uploaded files.
*   **Virtual Environment (`.venv/`)**: Isolates project dependencies.

## Frontend Structure (`frontend/`)

The frontend follows standard practices for a React application using Vite, TypeScript, and TailwindCSS, likely incorporating shadcn/ui conventions.

frontend/
├── components.json # shadcn/ui configuration
├── eslint.config.js # ESLint configuration
├── index.html # Main HTML entry point
├── package-lock.json # Exact dependency versions
├── package.json # Project metadata and dependencies
├── postcss.config.js # PostCSS configuration (used by Tailwind)
├── tailwind.config.ts # TailwindCSS configuration
├── tsconfig.app.json # TypeScript configuration for the app
├── tsconfig.json # Base TypeScript configuration
├── tsconfig.node.json # TypeScript configuration for Node scripts (like Vite config)
├── vite.config.ts # Vite build tool configuration
├── .env # Frontend environment variables - DO NOT COMMIT
├── .gitignore # Frontend-specific git ignore rules
├── public/ # Static assets directly served
│ └── robots.txt
└── src/ # Main application source code
├── App.tsx # Root application component, routing setup
├── index.css # Global CSS styles (Tailwind base/imports)
├── main.tsx # Application entry point (renders App)
├── vite-env.d.ts # Vite TypeScript environment types
├── assets/ # (Recommended) Static assets like images, icons used in components
├── components/ # Reusable React components
│ ├── auth/ # Components specific to authentication (e.g., ProtectedRoute)
│ ├── expenses/ # Components specific to expense features (e.g., AddExpenseForm, ExpenseList)
│ ├── layout/ # Layout components (e.g., Sidebar, AppLayout)
│ └── ui/ # Base UI components (likely shadcn/ui - Button, Card, Input etc.)
├── contexts/ # React Context API providers (e.g., AuthContext)
├── hooks/ # Custom React hooks (e.g., useAuth, useApi)
├── lib/ # Utility functions, constants, API clients, validators
│ ├── api.ts # (Recommended) Axios or fetch wrapper for backend calls
│ ├── utils.ts # General utility functions
│ └── validators/ # Frontend validation schemas (e.g., Zod, Yup) matching backend schemas
└── pages/ # Page-level components corresponding to routes
├── Expenses.tsx
├── Home.tsx
├── LoginPage.tsx
├── NotFound.tsx
├── RegisterPage.tsx
├── ReportsPage.tsx
└── Settings.tsx


*   **Configuration**: Standard config files for Vite, TypeScript, Tailwind, ESLint.
*   **Entry Point (`index.html`, `src/main.tsx`, `src/App.tsx`)**: Standard setup for Vite + React.
*   **Styling (`src/index.css`, `tailwind.config.ts`)**: Centralized global styles and Tailwind configuration.
*   **Components (`src/components/`)**: Organized by feature (`auth/`, `expenses/`) or layout (`layout/`), with a separate directory (`ui/`) for base, reusable UI primitives (excellent practice).
*   **State/Context (`src/contexts/`)**: Manages global or shared state.
*   **Hooks (`src/hooks/`)**: Encapsulates reusable logic, often interacting with context or APIs.
*   **Library/Utilities (`src/lib/`)**: Contains shared code like API interaction logic (`api.ts`), general utilities (`utils.ts`), and potentially frontend validation schemas (`validators/`) that mirror backend expectations.
*   **Pages (`src/pages/`)**: Top-level components rendered by the router for different application views.

This structure provides a clear and scalable organization for developing the Kharcha Nepal Tracker application.