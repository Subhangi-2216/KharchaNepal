# backend/src/dashboard/router.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, extract # Need extract for month/year
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP # For rounding percentages
from typing import List

from database import get_db # Assuming async session for now
from src.auth.dependencies import get_current_active_user
from models import Expense, User, CategoryEnum
from .schemas import DashboardStats, LargestExpenseDetail, DashboardSummary, CategorySummaryItem

router = APIRouter(
    prefix="/api/dashboard",
    tags=["Dashboard"],
    dependencies=[Depends(get_current_active_user)],
    responses={404: {"description": "Not found"}},
)

@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Calculates monthly total and finds the largest expense for the current calendar month."""
    now = datetime.now()
    current_month = now.month
    current_year = now.year

    try:
        # Calculate Monthly Total
        monthly_total_query = (
            select(func.sum(Expense.amount))
            .select_from(Expense)
            .where(Expense.user_id == current_user.id)
            .where(extract('year', Expense.date) == current_year)
            .where(extract('month', Expense.date) == current_month)
        )
        monthly_total = await db.scalar(monthly_total_query) or Decimal('0.00')

        # Find Largest Expense This Month
        largest_expense_query = (
            select(Expense)
            .where(Expense.user_id == current_user.id)
            .where(extract('year', Expense.date) == current_year)
            .where(extract('month', Expense.date) == current_month)
            .order_by(desc(Expense.amount))
            .limit(1)
        )
        result_scalars = await db.scalars(largest_expense_query)
        largest_expense_model = result_scalars.first()

        largest_expense_detail = None
        if largest_expense_model:
            largest_expense_detail = LargestExpenseDetail(
                amount=largest_expense_model.amount,
                # Access enum value if category exists
                category=largest_expense_model.category.value if largest_expense_model.category else None,
                merchant_name=largest_expense_model.merchant_name
            )

        return DashboardStats(
            monthly_total=monthly_total,
            largest_expense=largest_expense_detail
        )
    except Exception as e:
        print(f"Error in /stats: {e}") # Log specific error
        raise HTTPException(status_code=500, detail="Error calculating dashboard stats.")


@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Calculates expense summary by category for the last 30 days."""
    thirty_days_ago = datetime.now() - timedelta(days=30)

    try:
        # Query sum per category for the last 30 days
        summary_query = (
            select(
                Expense.category,
                func.sum(Expense.amount).label("total_amount")
            )
            .select_from(Expense)
            .where(Expense.user_id == current_user.id)
            .where(Expense.date >= thirty_days_ago.date()) # Compare dates
            .group_by(Expense.category)
            .order_by(desc("total_amount"))
        )
        result_proxy = await db.execute(summary_query)
        results = result_proxy.all() # Returns tuples (category_enum, total_amount)

        if not results:
            return DashboardSummary(summary=[], total_last_30_days=Decimal('0.00'))

        summary_list: List[CategorySummaryItem] = []
        total_sum = sum(res.total_amount for res in results if res.total_amount is not None)

        if total_sum == 0: # Avoid division by zero if only 0-amount expenses exist
             return DashboardSummary(summary=[], total_last_30_days=Decimal('0.00'))

        for category_enum, amount_sum in results:
            # Handle potential None for amount_sum if db returns None for sum aggregate
            if amount_sum is None: continue
            category_name = category_enum.value if category_enum else "Uncategorized"
            # Calculate percentage, round to 2 decimal places
            percentage = float(((amount_sum / total_sum) * 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
            summary_list.append(
                CategorySummaryItem(
                    category=category_name,
                    total_amount=amount_sum,
                    percentage=percentage
                )
            )

        return DashboardSummary(summary=summary_list, total_last_30_days=total_sum)
    except Exception as e:
        print(f"Error in /summary: {e}") # Log specific error
        raise HTTPException(status_code=500, detail="Error calculating dashboard summary.")