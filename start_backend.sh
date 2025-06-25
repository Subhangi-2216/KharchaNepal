#!/bin/bash

# KharchaNepal Backend Startup Script
echo "🚀 Starting KharchaNepal Backend Server..."
echo "=" * 50

# Navigate to backend directory
cd backend

# Activate conda environment
echo "📦 Activating conda environment..."
source ~/miniconda3/etc/profile.d/conda.sh
conda activate kharchanepal

# Check if environment is activated
if [[ $CONDA_DEFAULT_ENV != "kharchanepal" ]]; then
    echo "❌ Failed to activate kharchanepal environment"
    echo "Please run: conda activate kharchanepal"
    exit 1
fi

echo "✅ Environment activated: $CONDA_DEFAULT_ENV"

# Run database migrations
echo "🗄️  Running database migrations..."
alembic upgrade head

if [ $? -ne 0 ]; then
    echo "❌ Database migration failed"
    echo "Please check your database connection and alembic configuration"
    exit 1
fi

echo "✅ Database migrations completed"

# Start the server
echo "🌐 Starting FastAPI server..."
echo "📍 Server will be available at: http://localhost:8000"
echo "📚 API Documentation: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

uvicorn main:app --reload --host 0.0.0.0 --port 8000
