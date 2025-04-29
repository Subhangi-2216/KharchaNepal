from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select # Import select
from sqlalchemy import func # Added func

from database import get_db
from models import Expense as ExpenseModel # DB model
from models import User as UserModel # DB model
from auth.dependencies import get_current_active_user
from . import schemas as expense_schemas # Local schemas

router = APIRouter(
    prefix="/api/expenses",
    tags=["Expenses"],
    dependencies=[Depends(get_current_active_user)], # Apply auth to all routes in this router
    responses={404: {"description": "Not found"}}
)

@router.post("/manual", response_model=expense_schemas.Expense, status_code=status.HTTP_201_CREATED)
async def create_manual_expense(
    expense_in: expense_schemas.ExpenseCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_active_user)]
):
    """Handles manual expense entry for the authenticated user."""
    # Create the expense instance
    db_expense = ExpenseModel(
        user_id=current_user.id,
        merchant_name=expense_in.merchant_name,
        date=expense_in.date,
        amount=expense_in.amount,
        category=expense_in.category,
        currency='NPR', # As per requirements
        is_ocr_entry=False # Manual entry
        # ocr_raw_text is nullable, defaults to None
        # created_at/updated_at have defaults in the model
    )

    # Add expense to the database session and commit
    db.add(db_expense)
    await db.commit()
    await db.refresh(db_expense)

    return db_expense

@router.get("/has_any", response_model=bool)
async def check_has_any_expenses(
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """Checks if the current user has recorded at least one expense."""
    try:
        print(f"--- Checking expenses for user_id: {current_user.id} ---") # DEBUG PRINT
        query = (
            select(func.count(ExpenseModel.id))
            .select_from(ExpenseModel)
            .where(ExpenseModel.user_id == current_user.id)
        )
        count = await db.scalar(query)
        print(f"--- Found count: {count} for user_id: {current_user.id} ---") # DEBUG PRINT
        return count > 0
    except Exception as e:
        print(f"Error checking for expenses: {e}")
        raise HTTPException(status_code=500, detail="Error checking for expenses.")

@router.get("", response_model=List[expense_schemas.Expense])
async def read_expenses(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_active_user)],
    skip: int = 0, # Optional: for pagination
    limit: int = 100 # Optional: for pagination
):
    """Retrieves a list of expenses for the current user."""
    # Query expenses for the current user, ordered by date descending
    result = await db.execute(
        select(ExpenseModel)
        .where(ExpenseModel.user_id == current_user.id)
        .order_by(ExpenseModel.date.desc(), ExpenseModel.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    expenses = result.scalars().all()
    return expenses

# --- Add other expense endpoints below --- 
# e.g., PUT /api/expenses/{id}, DELETE /api/expenses/{id} 