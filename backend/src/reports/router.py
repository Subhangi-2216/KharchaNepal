import io
from datetime import date, datetime
from typing import List, Optional

from fastapi import (
    APIRouter, Depends, HTTPException, Query, Path, status
)
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from src.auth.dependencies import get_current_active_user
from models import User, CategoryEnum
from .schemas import ExpenseReportItem # Assuming this schema exists
from . import service

router = APIRouter(
    prefix="/api/reports",
    tags=["Reports"],
    dependencies=[Depends(get_current_active_user)],
    responses={404: {"description": "Not found"}},
)

def parse_categories(category_str: Optional[str]) -> Optional[List[CategoryEnum]]:
    """Parses comma-separated category string into list of CategoryEnum."""
    if not category_str:
        return None

    categories = []
    raw_categories = [c.strip() for c in category_str.split(',') if c.strip()]
    valid_category_values = {cat.value for cat in CategoryEnum}

    for cat_str in raw_categories:
        # Simple case-insensitive match against enum values
        matched = False
        for enum_member in CategoryEnum:
            if enum_member.value.lower() == cat_str.lower():
                categories.append(enum_member)
                matched = True
                break
        if not matched:
            # Handle invalid category string - raise error or ignore?
            # Raising error is safer to indicate bad input.
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid category provided: '{cat_str}'. Allowed values: {list(valid_category_values)}"
            )

    return categories if categories else None


@router.get("/data", response_model=List[ExpenseReportItem])
async def get_report_data(
    start_date: date = Query(...),
    end_date: date = Query(...),
    category: Optional[str] = Query(None, description="Comma-separated categories (e.g., Food,Travel)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Fetches filtered expense data for report preview."""
    if start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start date cannot be later than end date."
        )

    try:
        parsed_cats = parse_categories(category)
    except HTTPException as e:
        raise e

    try:
        # Service function now returns the correct Pydantic model list
        report_items = await service.fetch_report_data(
            db=db,
            user_id=current_user.id,
            start_date=start_date,
            end_date=end_date,
            categories=parsed_cats
        )
        # No need to validate here anymore
        return report_items
    except Exception as e:
        print(f"Error fetching report data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch report data."
        )


@router.get("/download/{format}")
async def download_report(
    format: str = Path(..., description="Report format: 'csv' or 'pdf'"),
    start_date: date = Query(...),
    end_date: date = Query(...),
    category: Optional[str] = Query(None, description="Comma-separated categories (e.g., Food,Travel)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Generates and downloads an expense report in the specified format (CSV or PDF)."""
    if format.lower() not in ['csv', 'pdf']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid format specified. Use 'csv' or 'pdf'."
        )

    if start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start date cannot be later than end date."
        )

    category_names_for_title: Optional[List[str]] = None
    filename_category_suffix = ""
    parsed_cats: Optional[List[CategoryEnum]] = None

    try:
        parsed_cats = parse_categories(category)
        if parsed_cats:
             category_names_for_title = [cat.value for cat in parsed_cats]
             if len(parsed_cats) == 1:
                  safe_category_name = parsed_cats[0].value.replace(" ", "_")
                  filename_category_suffix = f"_{safe_category_name}"

    except HTTPException as e:
        raise e

    try:
        # Fetch the data as Pydantic models
        expenses_report_items = await service.fetch_report_data(
            db=db,
            user_id=current_user.id,
            start_date=start_date,
            end_date=end_date,
            categories=parsed_cats
        )

        # Generate filename
        start_str = start_date.strftime('%Y%m%d')
        end_str = end_date.strftime('%Y%m%d')
        filename_base = f"expense_report{filename_category_suffix}_{start_str}_to_{end_str}"

        if format.lower() == 'csv':
            try:
                csv_buffer = service.create_csv_report(expenses_report_items)
                filename = f"{filename_base}.csv"
                headers = {'Content-Disposition': f'attachment; filename="{filename}"'}

                if not csv_buffer.getvalue():
                     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No expenses found for the selected criteria.")

                return StreamingResponse(csv_buffer, media_type="text/csv", headers=headers)
            except HTTPException as e:
                 raise e
            except Exception as e:
                print(f"Error creating CSV report: {e}")
                raise HTTPException(status_code=500, detail="Failed to generate CSV report.")

        elif format.lower() == 'pdf':
            try:
                # Pass the Pydantic model list
                pdf_buffer = service.create_pdf_report(expenses_report_items, start_date, end_date, category_names_for_title)
                filename = f"{filename_base}.pdf"
                headers = {'Content-Disposition': f'attachment; filename="{filename}"'}
                # PDF generation handles the 'no data' case internally by design
                return StreamingResponse(pdf_buffer, media_type="application/pdf", headers=headers)
            except Exception as e:
                print(f"Error creating PDF report: {e}")
                raise HTTPException(status_code=500, detail="Failed to generate PDF report.")

    # This exception should now be less likely for DB session issues
    except Exception as e:
        print(f"Error preparing report download: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to prepare report for download."
        )