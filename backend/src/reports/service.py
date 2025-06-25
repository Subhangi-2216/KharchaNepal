# backend/src/reports/service.py
import io
import pandas as pd
from datetime import date, datetime
from typing import List, Optional, Dict, Any # Import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from models import Expense, CategoryEnum, User # Import User if needed for user_id filtering
from .schemas import ExpenseReportItem # Import the schema

# For PDF Generation with ReportLab
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch


async def fetch_report_data(
    db: AsyncSession,
    user_id: int,
    start_date: date,
    end_date: date,
    categories: Optional[List[CategoryEnum]] = None
) -> List[ExpenseReportItem]:
    """Fetches filtered expense data and returns it as Pydantic models."""
    stmt = select(
        # Select specific columns needed
        Expense.date,
        Expense.merchant_name,
        Expense.amount,
        Expense.currency,
        Expense.category 
    ).where(
        Expense.user_id == user_id,
        Expense.date >= start_date,
        Expense.date <= end_date
    ).order_by(Expense.date.asc())

    if categories:
        stmt = stmt.where(Expense.category.in_(categories))

    result = await db.execute(stmt)
    # Fetch results as mappings (like dicts)
    # Use .mappings().all() instead of .scalars().all()
    expenses_raw = result.mappings().all() 
    
    # Validate/convert raw data into Pydantic models
    report_items = [ExpenseReportItem.model_validate(exp_data) for exp_data in expenses_raw]
    
    return report_items # Return list of Pydantic models


def create_csv_report(data: List[ExpenseReportItem]) -> io.StringIO:
    """Generates a CSV report from ExpenseReportItem data using Pandas."""
    if not data:
        return io.StringIO()

    # Convert list of Pydantic models to list of dicts for DataFrame
    # Be more explicit with potential None values
    data_dicts = []
    for item in data:
        try:
            category_value = item.category.value if item.category else 'N/A'
            amount_float = float(item.amount) # Convert Decimal to float
            merchant_name = item.merchant_name or 'N/A'
            
            data_dicts.append({
                "Date": item.date.isoformat(),
                "Merchant Name": merchant_name,
                "Category": category_value, 
                "Amount": amount_float, 
                "Currency": item.currency or 'N/A' # Handle currency potentially being None too
            })
        except Exception as e:
            # Log the item causing issues and the error
            print(f"Error processing item for CSV: {item}. Error: {e}")
            # Depending on requirements, you might skip the item or raise the error
            # For now, let's raise to signal a problem during conversion
            raise ValueError(f"Failed to process report item: {item}") from e

    if not data_dicts:
        # This case might happen if all items failed processing
        return io.StringIO()

    try:
        df = pd.DataFrame(data_dicts)
        # Reorder columns - ensure these names match the keys created above
        df = df[["Date", "Merchant Name", "Category", "Amount", "Currency"]]
    except Exception as e:
        print(f"Error creating/reordering DataFrame for CSV: {e}")
        raise ValueError("Failed to create DataFrame from report data.") from e

    output = io.StringIO()
    try:
        df.to_csv(output, index=False, encoding='utf-8')
    except Exception as e:
        print(f"Error writing DataFrame to CSV buffer: {e}")
        raise ValueError("Failed to write report data to CSV format.") from e
        
    output.seek(0)
    return output


def create_pdf_report(data: List[ExpenseReportItem], start_date: date, end_date: date, categories: Optional[List[str]]) -> io.BytesIO:
    """Generates a PDF report from ExpenseReportItem data using ReportLab."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()
    story = []

    # Title
    title_str = f"Expense Report ({start_date.isoformat()} to {end_date.isoformat()})"
    if categories:
         cat_str = ", ".join(categories)
         title_str += f" - Categories: {cat_str}"
    story.append(Paragraph(title_str, styles['h1']))
    story.append(Spacer(1, 0.2*inch))

    if not data:
        story.append(Paragraph("No expenses found matching the criteria.", styles['Normal']))
        doc.build(story)
        buffer.seek(0)
        return buffer

    # Prepare table data from list of ExpenseReportItem models
    table_data = [["Date", "Merchant Name", "Category", "Amount", "Currency"]]
    total_amount = 0.0
    # Iterate through the list of ExpenseReportItem models
    for item in data:
        amount_float = float(item.amount) 
        total_amount += amount_float
        table_data.append([
            item.date.isoformat(),
            item.merchant_name or 'N/A',
            item.category.value if item.category else 'N/A',
            f"{amount_float:.2f}", 
            item.currency
        ])

    # Create Table Style
    # Adjusted widths for landscape
    col_widths = [1.5*inch, 3.5*inch, 2.0*inch, 1.5*inch, 1.0*inch]
    table = Table(table_data, colWidths=col_widths)
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (3, 1), (3, -1), 'RIGHT'),
        ('RIGHTPADDING', (3, 1), (3, -1), 6),
    ])
    table.setStyle(style)
    story.append(table)

    story.append(Spacer(1, 0.2*inch))
    summary_str = f"Total Expenses: {total_amount:.2f} {data[0].currency if data else 'NPR'}" 
    story.append(Paragraph(summary_str, styles['h3']))

    doc.build(story)
    buffer.seek(0)
    return buffer 