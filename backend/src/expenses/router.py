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
from auth.dependencies import get_current_active_user
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

@router.post("/ocr", response_model=ExpenseOCRResponse, status_code=status.HTTP_201_CREATED)
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
        print(f"Error reading uploaded file: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not read uploaded file.")
    finally:
         await file.close()
         
    # 3. Perform OCR and Parsing
    ocr_raw_text = ""
    extracted_dict = {}
    try:
        ocr_raw_text = process_image_with_ocr(image_bytes)
        if not ocr_raw_text:
            # Handle case where OCR itself failed or returned empty
            print("OCR processing returned no text.")
            # We might still proceed to save an entry with only raw text, or raise error
            # Let's proceed and indicate all fields are missing in response
            
        extracted_dict = parse_ocr_text(ocr_raw_text)
    except Exception as e:
        # Catch errors from OCR service itself
        print(f"Error during OCR/Parsing service call: {e}")
        # Proceed but expect most fields to be missing
        pass # extracted_dict remains empty or partially filled

    # 4. Save Partial Expense to DB
    try:
        # Prepare partial expense data
        # Use extracted values if present, otherwise default to None or a sensible default
        # Important: Ensure date is present, maybe default to today if not found?
        expense_date = extracted_dict.get('date') or date.today() # Default to today if OCR fails
        
        expense_data_for_db = {
            "user_id": current_user.id,
            "date": expense_date,
            "merchant_name": extracted_dict.get('merchant_name'),
            "amount": extracted_dict.get('amount'), 
            "currency": extracted_dict.get('currency', 'NPR'), # Default currency
            "category": None, # Category must be set later
            "is_ocr_entry": True,
            "ocr_raw_text": ocr_raw_text
        }
        
        # Amount is required by model, handle if not found by OCR
        if expense_data_for_db['amount'] is None:
            # Option 1: Raise error - force user to provide amount
             # raise HTTPException(status_code=400, detail="Could not extract amount from receipt. Please enter manually.")
             # Option 2: Save with a placeholder (e.g., 0) - might be confusing
             # expense_data_for_db['amount'] = Decimal('0.00')
             # For now, let's allow saving without amount, relying on PUT to fix.
             # **Correction**: The model likely requires amount. Let's raise error if not found.
             # Reverting to raising error as it's safer. User MUST provide amount later via PUT.
             print("OCR could not extract amount.") # Log it
             # We will indicate amount is missing in the response, but won't save yet.
             # Instead of saving partially, let's just return the extracted data
             # and let frontend decide how to handle missing mandatory fields (like amount) before PUT.
             
             # --- REVISED LOGIC: Don't save yet, return extracted data --- 
             missing_fields = ['category'] # Category is always missing initially
             extracted_data_response = ExtractedData(**extracted_dict)
             if extracted_data_response.date is None: missing_fields.append('date')
             if extracted_data_response.merchant_name is None: missing_fields.append('merchant_name')
             if extracted_data_response.amount is None: missing_fields.append('amount')
             
             # Cannot create expense if mandatory fields like amount are missing. Return failure.
             # Let's modify the response to indicate failure but still provide data
             # Maybe use 200 OK but with an error message and no expense_id?
             # Or stick to the plan: Save partially *if* mandatory fields are present?
             # Let's stick to PRD plan: Save partially, return ID, require PUT
             # BUT amount is required by DB model. We MUST have an amount.
             # If OCR fails amount, we cannot proceed with saving.
             raise HTTPException(
                 status_code=status.HTTP_400_BAD_REQUEST, 
                 detail="OCR failed to extract the mandatory 'amount' field. Cannot create expense entry automatically."
             )
             # --- End of revised logic attempt --- 

        # Original Logic: Save partially (assuming amount was found)
        expense = Expense(**expense_data_for_db)
        db.add(expense)
        await db.commit()
        await db.refresh(expense)

        # 5. Construct Response
        missing_fields = ['category'] # Always missing initially
        extracted_data_for_resp = ExtractedData(**extracted_dict)
        # Check other fields that might be missing from parsing
        if extracted_data_for_resp.date is None: missing_fields.append('date') # Should have default though
        if extracted_data_for_resp.merchant_name is None: missing_fields.append('merchant_name')
        # Amount check already happened

        return ExpenseOCRResponse(
            expense_id=expense.id,
            extracted_data=extracted_data_for_resp,
            missing_fields=list(set(missing_fields)), # Ensure unique
            message="OCR processing complete. Please verify details and select a category."
        )

    except HTTPException as e:
         await db.rollback() # Rollback if HTTP exception occurred during process
         raise e # Re-raise HTTP exceptions (like validation, amount not found)
    except Exception as e:
        await db.rollback()
        print(f"Error saving OCR expense: {e}")
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