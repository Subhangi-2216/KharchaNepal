from datetime import date
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_

from models import Expense, User, CategoryEnum

async def get_filtered_expenses(
    db: AsyncSession,
    user: User,
    start_date: date,
    end_date: date,
    categories: Optional[List[CategoryEnum]] = None
) -> List[Expense]:
    """Fetches expenses filtered by user, date range, and optional categories."""
    
    query = (
        select(Expense)
        .where(
            and_(
                Expense.user_id == user.id,
                Expense.date >= start_date,
                Expense.date <= end_date
            )
        )
    )

    if categories:
        query = query.where(Expense.category.in_(categories))

    # Sort by date ascending as requested for reports
    query = query.order_by(Expense.date.asc())

    result = await db.execute(query)
    expenses = result.scalars().all()
    return expenses 