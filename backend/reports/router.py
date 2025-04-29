import io
import pandas as pd
from datetime import date
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

# PDF Generation imports (assuming reportlab is installed)
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

from database import get_db
from models import User as UserModel, CategoryEnum
from auth.dependencies import get_current_active_user
from . import schemas as report_schemas
from . import service as report_service

router = APIRouter(
    prefix="/api/reports",
    tags=["Reports"],
    dependencies=[Depends(get_current_active_user)]
)

# Helper function to parse and validate categories
def parse_categories(category: Optional[str] = Query(None)) -> Optional[List[CategoryEnum]]:
    if not category:
        return None
    
    valid_categories = []
    invalid_categories = []
    input_categories = [c.strip() for c in category.split(',')]
    
    for cat_str in input_categories:
        try:
            # Attempt to convert string to CategoryEnum member
            enum_member = CategoryEnum(cat_str)
            valid_categories.append(enum_member)
        except ValueError:
            invalid_categories.append(cat_str)
            
    if invalid_categories:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid categories provided: {', '.join(invalid_categories)}. Allowed categories are: {', '.join([e.value for e in CategoryEnum])}"
        )
        
    return valid_categories if valid_categories else None

# Common dependency for fetching filtered data
# Reordered parameters: Non-default first (db, current_user)
async def get_report_data(
    db: Annotated[AsyncSession, Depends(get_db)], 
    current_user: Annotated[UserModel, Depends(get_current_active_user)],
    start_date: date = Query(...),
    end_date: date = Query(...),
    categories: Optional[List[CategoryEnum]] = Depends(parse_categories)
) -> List[report_schemas.ReportExpenseItem]:
    
    if start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start date cannot be after end date."
        )
        
    expenses = await report_service.get_filtered_expenses(
        db=db, user=current_user, start_date=start_date, end_date=end_date, categories=categories
    )
    
    # Convert DB models to Pydantic schemas for consistent output structure
    report_items = [report_schemas.ReportExpenseItem.model_validate(exp) for exp in expenses]
    return report_items

@router.get("/data", response_model=List[report_schemas.ReportExpenseItem])
async def get_report_data_endpoint(
    report_data: List[report_schemas.ReportExpenseItem] = Depends(get_report_data)
):
    """Provides filtered expense data as JSON for report previews."""
    return report_data

@router.get("/download/csv")
async def download_report_csv(
    report_data: List[report_schemas.ReportExpenseItem] = Depends(get_report_data)
):
    """Generates and streams a CSV report of filtered expenses."""
    if not report_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No expenses found for the selected criteria.")

    # Convert Pydantic models list to list of dicts for pandas
    data_dicts = [item.model_dump() for item in report_data]
    df = pd.DataFrame(data_dicts)
    
    # Format date column if needed
    df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
    
    # Select and reorder columns for the report
    df_report = df[['date', 'merchant_name', 'category', 'currency', 'amount']]

    stream = io.StringIO()
    df_report.to_csv(stream, index=False)
    
    response = StreamingResponse(iter([stream.getvalue()]), media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=expense_report.csv"
    return response

@router.get("/download/pdf")
async def download_report_pdf(
    report_data: List[report_schemas.ReportExpenseItem] = Depends(get_report_data)
):
    """Generates and streams a PDF report of filtered expenses."""
    if not report_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No expenses found for the selected criteria.")

    buffer = io.BytesIO()
    # Use landscape for potentially wide table
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
    styles = getSampleStyleSheet()
    story = []

    # Title
    title = "Expense Report"
    story.append(Paragraph(title, styles['h1']))
    story.append(Spacer(1, 12))

    # Convert data for ReportLab Table
    # Header row
    table_data = [['Date', 'Merchant', 'Category', 'Currency', 'Amount']]
    # Data rows
    for item in report_data:
        table_data.append([
            item.date.strftime('%Y-%m-%d'),
            item.merchant_name,
            item.category.value, # Get the string value from Enum
            item.currency,
            f"{item.amount:.2f}" # Format amount as string
        ])

    # Create Table style
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey), # Header background
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke), # Header text
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), # Header font
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12), # Header padding
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige), # Body background
        ('GRID', (0, 0), (-1, -1), 1, colors.black) # Grid lines
    ])

    # Create Table object
    report_table = Table(table_data)
    report_table.setStyle(style)

    story.append(report_table)
    
    # TODO: Add summary statistics if needed

    doc.build(story)

    buffer.seek(0)
    response = StreamingResponse(buffer, media_type="application/pdf")
    response.headers["Content-Disposition"] = "attachment; filename=expense_report.pdf"
    return response 