# Welcome to Kharcha Nepal Tracker

This project is a personal expense tracker application.

## Project Overview

<!-- Add a brief description of your project -->

**Tech Stack**: React, TypeScript, FastAPI, Python

<!-- Optional: Add link to your live deployment -->
<!-- **URL**: [Link to your deployed app] -->

## Getting Started

### Prerequisites

- Node.js (v18 or later recommended)
- Python (v3.9 or later recommended)
- pip (Python package installer)
- An IDE (like VS Code)

### Use the Application

Follow the setup instructions below to run the application locally.

<!-- Removed section about using Lovable directly -->

### Local Development Setup

If you want to work locally using your own IDE, clone this repo and follow the setup steps.

#### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

This will start the React development server, usually at `http://localhost:5173`.

#### Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
pip install -r requirements.txt

# Optional: Create a .env file for environment variables (see .env.example)
# cp .env.example .env
# Fill in your DATABASE_URL and other settings in .env

uvicorn main:app --reload --port 8000
```

This will start the FastAPI backend server, usually at `http://localhost:8000`.

Make sure both the frontend and backend servers are running simultaneously.

## Project Structure

- `frontend/`: Contains the React frontend code.
- `backend/`: Contains the FastAPI backend code.
- `README.md`: This file.

## Deployment

<!-- Instructions on how to deploy the application -->

<!-- Removed section about publishing via Lovable -->

## Frequently Asked Questions (FAQ)

### How do I add a new dependency?

- **Frontend**: `cd frontend && npm install <package-name>`
- **Backend**: Activate your virtual environment (`source backend/.venv/bin/activate`), then `pip install <package-name>`, and finally update `requirements.txt` using `pip freeze > requirements.txt`.

### Can I connect a custom domain to my project deployment?

Connecting a custom domain depends on your hosting provider. Please refer to your provider's documentation for instructions.

<!-- Removed link to Lovable custom domain docs -->

### Where can I find database migrations?

This project currently does not use a formal migration tool like Alembic. Database schema changes are managed directly through SQLAlchemy models. For significant changes or production environments, integrating Alembic is recommended.
