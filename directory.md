# Project Structure: Kharcha Nepal Tracker

This document outlines the directory structure for the OCR-Driven Expense Logging and NLP Chatbot project (`Kharcha Nepal Tracker`).

subhangi-2216-kharchanepal/
├── backend/ # FastAPI Backend Application
│ ├── alembic.ini # Alembic configuration file
│ ├── config.py # Application configuration (e.g., loading .env)
│ ├── database.py # SQLAlchemy engine, session setup, Base model
│ ├── main.py # FastAPI application instance, middleware, root endpoint, router includes
│ ├── models.py # SQLAlchemy ORM models (User, Expense, etc.)
│ ├── requirements.txt # Python dependencies
│ ├── .env # Environment variables (DB URL, JWT Secret) - DO NOT COMMIT
│ └── .gitignore # Backend-specific git ignore rules
│ ├── alembic/ # Database migration scripts
│ │ ├── env.py
│ │ ├── README
│ │ ├── script.py.mako
│ │ └── versions/
│ │ └── ... migration_files.py ...
│ ├── src/ # Main application source code directory
│ │ ├── init.py
│ │ ├── auth/ # Authentication logic
│ │ │ ├── init.py
│ │ │ ├── dependencies.py
│ │ │ ├── router.py
│ │ │ ├── schemas.py
│ │ │ └── service.py
│ │ ├── chatbot/ # Chatbot related logic
│ │ │ ├── init.py
│ │ │ ├── faqs.py
│ │ │ ├── nlp_service.py # (Recommended) NLP processing logic
│ │ │ ├── router.py
│ │ │ └── schemas.py
│ │ ├── dashboard/ # Dashboard specific logic
│ │ │ ├── init.py
│ │ │ ├── router.py
│ │ │ └── schemas.py
│ │ ├── expenses/ # Expense management logic (excluding OCR processing)
│ │ │ ├── init.py
│ │ │ ├── router.py
│ │ │ └── schemas.py
│ │ ├── ocr/ # OCR processing logic (NEW - Recommended)
│ │ │ ├── init.py
│ │ │ ├── preprocessing.py # (Recommended) OpenCV image preprocessing
│ │ │ ├── service.py # OCR execution and parsing/extraction
│ │ │ └── schemas.py # Pydantic schemas if needed for OCR results
│ │ ├── reports/ # Reporting logic
│ │ │ ├── init.py
│ │ │ ├── router.py
│ │ │ ├── schemas.py
│ │ │ └── service.py
│ │ └── user_settings/ # User profile and settings logic
│ │ ├── init.py
│ │ ├── router.py
│ │ └── schemas.py
│ ├── uploads/ # Directory for user-uploaded files - Should be in .gitignore
│ │ └── profile_images/
│ └── .venv/ # Python virtual environment - Should be in .gitignore
│ └── ...
├── frontend/ # React Frontend Application
│ ├── components.json # shadcn/ui configuration
│ ├── eslint.config.js # ESLint configuration
│ ├── index.html # Main HTML entry point
│ ├── package-lock.json # Exact dependency versions
│ ├── package.json # Project metadata and dependencies
│ ├── postcss.config.js # PostCSS configuration (used by Tailwind)
│ ├── tailwind.config.ts # TailwindCSS configuration
│ ├── tsconfig.app.json # TypeScript configuration for the app
│ ├── tsconfig.json # Base TypeScript configuration
│ ├── tsconfig.node.json # TypeScript configuration for Node scripts (like Vite config)
│ ├── vite.config.ts # Vite build tool configuration
│ ├── .env # Frontend environment variables - DO NOT COMMIT
│ ├── .gitignore # Frontend-specific git ignore rules
│ ├── public/ # Static assets directly served
│ │ └── robots.txt
│ └── src/ # Main application source code
│ ├── App.tsx # Root application component, routing setup
│ ├── index.css # Global CSS styles (Tailwind base/imports)
│ ├── main.tsx # Application entry point (renders App)
│ ├── vite-env.d.ts # Vite TypeScript environment types
│ ├── assets/ # (Recommended) Static assets like images, icons
│ ├── components/ # Reusable React components
│ │ ├── auth/ # Components specific to authentication
│ │ ├── expenses/ # Components specific to expense features
│ │ ├── layout/ # Layout components (Sidebar, AppLayout)
│ │ └── ui/ # Base UI components (shadcn/ui)
│ ├── contexts/ # React Context API providers
│ ├── hooks/ # Custom React hooks
│ ├── lib/ # Utility functions, API clients, validators
│ │ ├── api.ts # (Recommended) API interaction wrapper
│ │ ├── utils.ts
│ │ └── validators/
│ └── pages/ # Page-level components
│ ├── Expenses.tsx
│ ├── Home.tsx
│ ├── LoginPage.tsx
│ ├── NotFound.tsx
│ ├── RegisterPage.tsx
│ ├── ReportsPage.tsx
│ └── Settings.tsx
├── .gitignore # Git ignore rules for the whole project
├── README.md # Main project README
└── requirements_project.md # Detailed project requirements & tasks
