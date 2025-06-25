# backend/src/expenses/router.py
import io
from datetime import date
from typing import List, Optional
import logging # Import logging

from fastapi import (
    APIRouter, Depends, HTTPException, Query, Path, status,
    UploadFile, File
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from database import get_db
from src.auth.dependencies import get_current_active_user
from models import User, Expense, CategoryEnum
# Assuming schemas are in the same directory or accessible via src.expenses
# Adjust import path if schemas.py is elsewhere (e.g., in src/schemas/expenses.py)
try:
    from .schemas import (
        ExpenseCreate, ExpenseUpdate, ExpenseInDB,
        ExpenseOCRResponse, ExtractedData
    )
except ImportError:
     # Fallback if schemas are directly in src
     from schemas import (
        ExpenseCreate, ExpenseUpdate, ExpenseInDB,
        ExpenseOCRResponse, ExtractedData
    )

# Import OCR service from the new location
try:
    from src.ocr import process_image_with_ocr, parse_ocr_text
except ImportError:
    # Fallback import paths
    try:
        from ocr import process_image_with_ocr, parse_ocr_text
    except ImportError:
        from src.ocr.service import process_image_with_ocr, parse_ocr_text


router = APIRouter(
    prefix="/api/expenses",
    tags=["Expenses"],
    dependencies=[Depends(get_current_active_user)],
    responses={404: {"description": "Not found"}},
)

# --- Configuration for Uploads ---
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024 # 5 MB
ALLOWED_IMAGE_MIMETYPES = {"image/jpeg", "image/png", "image/webp"}

# --- CRUD Endpoints ---

@router.post("/manual", response_model=ExpenseInDB, status_code=status.HTTP_201_CREATED)
async def create_expense_manual(
    expense_in: ExpenseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Creates a new expense via manual input."""
    try:
        expense = Expense(
            **expense_in.model_dump(),
            user_id=current_user.id,
            is_ocr_entry=False # Explicitly set for manual entry
        )
        db.add(expense)
        await db.commit()
        await db.refresh(expense)
        return expense
    except Exception as e:
        await db.rollback()
        print(f"Error creating manual expense: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create expense."
        )

@router.post("/ocr", status_code=status.HTTP_201_CREATED)
async def create_expense_ocr(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Processes an uploaded receipt image using OCR and saves partial expense."""
    # 1. Validate File
    if file.content_type not in ALLOWED_IMAGE_MIMETYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_IMAGE_MIMETYPES)}"
        )

    # Simple size check (more robust check can be done while reading)
    if file.size and file.size > MAX_FILE_SIZE_BYTES:
         raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Max size: {MAX_FILE_SIZE_BYTES // 1024 // 1024}MB"
        )

    # 2. Read File Content
    try:
        image_bytes = await file.read()
        if len(image_bytes) > MAX_FILE_SIZE_BYTES:
             raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large after reading. Max size: {MAX_FILE_SIZE_BYTES // 1024 // 1024}MB"
            )
    except Exception as e:
        logging.error(f"Error reading uploaded file: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not read uploaded file.")
    finally:
         await file.close()

    # 3. Perform OCR and Parsing
    ocr_raw_text = ""
    extracted_dict = {}
    try:
        # Process image with OCR using enhanced preprocessing
        logging.info("Starting OCR processing with preprocessing...")
        ocr_raw_text = process_image_with_ocr(image_bytes)

        if not ocr_raw_text:
            logging.warning("OCR processing returned no text.")
            # We'll proceed but all fields will be missing in the response
        else:
            logging.info(f"OCR text extracted successfully ({len(ocr_raw_text)} characters)")

        # Parse the OCR text to extract structured data
        extracted_dict = parse_ocr_text(ocr_raw_text)
        logging.info(f"Extracted data: {extracted_dict}")

    except Exception as e:
        logging.error(f"Error during OCR/Parsing service call: {e}", exc_info=True)
        # We'll proceed but expect most fields to be missing
        extracted_dict = {}

    # 4. Check if mandatory 'amount' was extracted
    if extracted_dict.get('amount') is None:
        logging.warning("OCR failed to extract the mandatory 'amount' field")

        # Prepare response with extracted data but indicate failure
        missing_fields = ['category']  # Category is always missing initially
        extracted_data_response = ExtractedData(**extracted_dict)

        # Check which fields are missing
        if extracted_data_response.date is None: missing_fields.append('date')
        if extracted_data_response.merchant_name is None: missing_fields.append('merchant_name')
        missing_fields.append('amount')  # Amount is definitely missing

        # Return 400 Bad Request with the extracted data in the error detail
        # This allows the frontend to still use the partial data
        error_response = {
            "detail": "OCR failed to extract the mandatory 'amount' field. Please update manually.",
            "extracted_data": extracted_dict,
            "missing_fields": list(set(missing_fields))
        }

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response
        )

    # 5. Save Expense to DB (only if amount was found)
    try:
        # Prepare expense data
        # Validate the date - if it's unrealistic, use today's date
        extracted_date = extracted_dict.get('date')
        current_year = date.today().year

        # Define valid year range (matching OCR service)
        min_valid_year = current_year - 20  # Allow receipts from up to 20 years ago
        max_valid_year = current_year + 1   # Allow receipts dated slightly in the future

        # Check if date is realistic (using same range as OCR service)
        if extracted_date and (extracted_date.year < min_valid_year or extracted_date.year > max_valid_year):
            logging.warning(f"Unrealistic date detected from OCR: {extracted_date}. Using today's date instead.")
            expense_date = date.today()
            # Remove the invalid date from extracted_dict so it won't be used in the response
            extracted_dict['date'] = None
        elif extracted_date and extracted_date > date.today() and (extracted_date - date.today()).days > 7:
            # If date is more than a week in the future, it's likely an error
            logging.warning(f"Future date detected from OCR: {extracted_date}. Using today's date instead.")
            expense_date = date.today()
            # Remove the invalid date from extracted_dict so it won't be used in the response
            extracted_dict['date'] = None
        else:
            # Use the extracted date if available, otherwise use today's date
            expense_date = extracted_date or date.today()

            # If the date confidence is very low, mark it as missing in the response
            if extracted_dict.get('date_confidence', 0) < 0.2 and extracted_date is not None:
                logging.info(f"Low confidence date detected: {extracted_date} (confidence: {extracted_dict.get('date_confidence')})")
                # Keep the date for the database but mark it as missing in the response
                extracted_dict['date'] = None

        expense_data_for_db = {
            "user_id": current_user.id,
            "date": expense_date,
            "merchant_name": extracted_dict.get('merchant_name'),
            "amount": extracted_dict.get('amount'),  # We know this is not None at this point
            "currency": extracted_dict.get('currency', 'NPR'),  # Default currency
            "category": None,  # Category must be set later
            "is_ocr_entry": True,
            "ocr_raw_text": ocr_raw_text
        }

        # Create the expense but don't commit yet
        expense = Expense(**expense_data_for_db)
        db.add(expense)

        # We'll commit after creating the response, so we can rollback if needed
        # This allows for proper cancellation if the user decides not to proceed
        await db.flush()  # This assigns an ID but doesn't commit

        logging.info(f"Expense created with ID: {expense.id} (not committed yet)")

        # 6. Construct Response
        missing_fields = ['category']  # Category is always missing initially

        # Check which fields might be missing before creating the response object
        if extracted_dict.get('date') is None:
            missing_fields.append('date')
        if extracted_dict.get('merchant_name') is None:
            missing_fields.append('merchant_name')

        # Log the extracted data for debugging
        logging.info(f"Extracted data: {extracted_dict}")
        logging.info(f"Expense saved with ID: {expense.id}, date: {expense.date}, amount: {expense.amount}")

        # Prepare the response with confidence scores
        response_data = {
            "expense_id": expense.id,
            "extracted_data": {
                "merchant_name": expense.merchant_name,
                "merchant_confidence": extracted_dict.get('merchant_confidence', 0.5),  # Default confidence if not provided
                "date": expense.date.isoformat() if expense.date else None,
                "date_confidence": extracted_dict.get('date_confidence', 0.5),  # Default confidence if not provided
                "amount": float(expense.amount) if expense.amount else None,
                "amount_confidence": extracted_dict.get('amount_confidence', 0.5),  # Default confidence if not provided
                "currency": expense.currency,
            },
            "missing_fields": list(set(missing_fields)),  # Ensure unique
            "message": "OCR processing complete. Please verify details and select a category."
        }

        # Now that we have a valid response, commit the transaction
        await db.commit()
        logging.info(f"Expense committed to database with ID: {expense.id}")

        return response_data

    except HTTPException as e:
        await db.rollback()  # Rollback if HTTP exception occurred during process
        raise e  # Re-raise HTTP exceptions

    except Exception as e:
        await db.rollback()
        logging.error(f"Error saving OCR expense: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process OCR request and save expense."
        )


@router.put("/{expense_id}", response_model=ExpenseInDB)
async def update_expense(
    expense_id: int,
    expense_in: ExpenseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Updates an existing expense (e.g., add category after OCR)."""

    # --- Added Logging ---
    logging.info(f"--- update_expense (ID: {expense_id}) --- Received validated data:")
    logging.info(expense_in.model_dump())
    # --- End Added Logging ---

    # Fetch the existing expense
    stmt = select(Expense).where(Expense.id == expense_id, Expense.user_id == current_user.id)
    result = await db.execute(stmt)
    db_expense = result.scalar_one_or_none()

    if db_expense is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")

    # Get update data, excluding unset fields to prevent accidentally nullifying fields
    update_data = expense_in.model_dump(exclude_unset=True)

    if not update_data:
            # Although Pydantic model allows all fields Optional,
            # we probably shouldn't allow an empty update.
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No update data provided."
            )

    # Update fields
    logging.info(f"Applying update data: {update_data}") # Log fields being applied
    for key, value in update_data.items():
        setattr(db_expense, key, value)

    try:
        await db.commit()
        await db.refresh(db_expense)
        logging.info(f"Expense {expense_id} updated successfully.") # Log success
        return db_expense
    except Exception as e:
        await db.rollback()
        # --- Modified Logging ---
        logging.error(f"Error updating expense {expense_id}: {e}", exc_info=True) # Log full exception
        # --- End Modified Logging ---
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, # Changed to 500 for unexpected errors
            detail=f"Could not update expense: {e}" # Include error in detail
        )

# Basic GET endpoint (add filtering/pagination later)
@router.get("", response_model=List[ExpenseInDB])
async def read_expenses(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    # Add filters later: start_date, end_date, category
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieves a list of expenses for the current user."""
    stmt = select(Expense).where(Expense.user_id == current_user.id)\
            .order_by(Expense.date.desc(), Expense.created_at.desc())\
            .offset(skip).limit(limit)

    result = await db.execute(stmt)
    expenses = result.scalars().all()
    return list(expenses)

# Basic DELETE endpoint
@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense(
    expense_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Deletes an expense for the current user."""
    stmt = delete(Expense).where(Expense.id == expense_id, Expense.user_id == current_user.id)
    result = await db.execute(stmt)

    if result.rowcount == 0:
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")

    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        print(f"Error deleting expense {expense_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not delete expense."
        )

    return # Return None for 204

@router.get("/has_any", response_model=bool)
async def has_any_expenses(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Checks if the user has any expenses."""
    stmt = select(Expense).where(Expense.user_id == current_user.id).limit(1)
    result = await db.execute(stmt)
    has_expenses = result.scalar_one_or_none() is not None
    return has_expenses