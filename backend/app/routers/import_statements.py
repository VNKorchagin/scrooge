"""Router for importing bank statements."""
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.transaction import TransactionSource
from app.services.import_service import ImportService, ParsedTransaction
from app.services.pdf_parser import PDFParser
from app.services.categorization_service import CategorizationService
from app.services.transaction_service import TransactionService
from app.services.category_service import CategoryService
from app.schemas.import_schema import (
    ImportPreviewResponse,
    ImportConfirmRequest,
    ImportConfirmResponse,
    ImportTransaction,
    CategorySuggestionRequest,
    CategorySuggestionResponse
)


router = APIRouter()


def _map_parsed_to_schema(tx: ParsedTransaction) -> ImportTransaction:
    """Convert ParsedTransaction to schema."""
    return ImportTransaction(
        raw_description=tx.raw_description,
        amount=float(tx.amount),
        transaction_date=tx.transaction_date,
        mcc_code=tx.mcc_code,
        type=tx.type.value if tx.type else "expense",
        suggested_category=tx.suggested_category,
        confidence=tx.confidence,
        confidence_score=tx.confidence_score,
        is_duplicate=tx.is_duplicate,
        duplicate_count=tx.duplicate_count
    )


@router.post("/preview", response_model=ImportPreviewResponse)
async def preview_import(
    file: UploadFile = File(...),
    bank_type: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    Preview transactions from uploaded file before import.
    
    Parses CSV or PDF file and returns transactions with suggested categories.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    content = await file.read()
    
    try:
        # Determine file type and parse
        filename_lower = file.filename.lower()
        
        if filename_lower.endswith('.csv'):
            transactions, detected_bank = ImportService.parse_csv(content, file.filename)
            source = TransactionSource.IMPORT_CSV
        elif filename_lower.endswith('.pdf'):
            transactions = PDFParser.parse(content, bank_type)
            detected_bank = bank_type or "unknown"
            source = TransactionSource.IMPORT_PDF
        else:
            raise HTTPException(
                status_code=400, 
                detail="Unsupported file format. Only CSV and PDF are supported."
            )
        
        # Get user language from DB
        from app.services.user_service import UserService
        user = await UserService.get_by_id(db, current_user_id)
        language = user.language if user else "en"
        
        # Categorize transactions
        transactions = await ImportService.categorize_transactions(
            transactions,
            current_user_id,
            db,
            language
        )
        
        # Check for duplicates
        transactions = await ImportService.check_duplicates(
            transactions,
            current_user_id,
            db
        )
        
        # Count by confidence
        high_count = sum(1 for t in transactions if t.confidence == "high")
        medium_count = sum(1 for t in transactions if t.confidence == "medium")
        low_count = sum(1 for t in transactions if t.confidence == "low")
        duplicate_count = sum(1 for t in transactions if t.is_duplicate)
        
        response = ImportPreviewResponse(
            transactions=[_map_parsed_to_schema(t) for t in transactions],
            total_count=len(transactions),
            high_confidence_count=high_count,
            medium_confidence_count=medium_count,
            low_confidence_count=low_count,
            duplicate_count=duplicate_count,
            detected_bank=detected_bank
        )
        print(f"DEBUG: Returning response with {len(response.transactions)} transactions")
        return response
        
    except Exception as e:
        import traceback
        print(f"ERROR in preview_import: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=400,
            detail=f"Failed to parse file: {str(e)}"
        )


@router.post("/confirm", response_model=ImportConfirmResponse)
async def confirm_import(
    request: ImportConfirmRequest,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    Confirm and save imported transactions.
    
    Accepts the list of transactions (potentially modified by user)
    and saves them to the database.
    """
    categorization_service = CategorizationService(db)
    imported_count = 0
    saved_patterns = 0
    
    for tx_data in request.transactions:
        try:
            # Get or create category
            category = await CategoryService.get_or_create(
                db, 
                tx_data.suggested_category or "Other", 
                current_user_id
            )
            
            # Determine source based on file type (assume CSV for now)
            source = TransactionSource.IMPORT_CSV
            
            # Create transaction
            from app.models.transaction import Transaction, TransactionType
            
            transaction = Transaction(
                user_id=current_user_id,
                type=TransactionType(tx_data.type),
                amount=tx_data.amount,
                category_id=category.id,
                category_name=category.name,
                description=tx_data.raw_description[:100] if tx_data.raw_description else None,
                raw_description=tx_data.raw_description,
                transaction_date=tx_data.transaction_date or datetime.utcnow(),
                source=source
            )
            
            db.add(transaction)
            imported_count += 1
            
            # Learn pattern if user confirmed (but don't fail the whole import if this fails)
            if request.save_patterns and tx_data.confidence in ("high", "medium"):
                try:
                    # Clean MCC code - limit to 4 chars
                    clean_mcc = tx_data.mcc_code[:4] if tx_data.mcc_code else None
                    await categorization_service.learn_pattern(
                        user_id=current_user_id,
                        raw_description=tx_data.raw_description,
                        category_name=category.name,
                        category_id=category.id,
                        mcc_code=clean_mcc
                    )
                    saved_patterns += 1
                except Exception as e:
                    print(f"Failed to save pattern: {e}")
                    # Continue without saving pattern
                
        except Exception as e:
            # Log error but continue with other transactions
            print(f"Failed to import transaction: {e}")
            await db.rollback()
            continue
    
    await db.commit()
    
    return ImportConfirmResponse(
        imported_count=imported_count,
        saved_patterns=saved_patterns
    )


@router.post("/suggest-category", response_model=CategorySuggestionResponse)
async def suggest_category(
    request: CategorySuggestionRequest,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    Get category suggestion for a raw transaction description.
    
    Useful for real-time suggestions as user edits transactions.
    """
    from app.services.user_service import UserService
    user = await UserService.get_by_id(db, current_user_id)
    language = user.language if user else "en"
    
    categorization_service = CategorizationService(db)
    
    result = await categorization_service.categorize(
        user_id=current_user_id,
        raw_description=request.raw_description,
        mcc_code=request.mcc_code,
        language=language
    )
    
    return CategorySuggestionResponse(
        category=result["category"],
        confidence=result["confidence"],
        score=result["score"]
    )


@router.post("/learn-pattern")
async def learn_pattern(
    raw_description: str,
    category_name: str,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    Explicitly learn a pattern from user input.
    
    Call this when user manually corrects a category.
    """
    categorization_service = CategorizationService(db)
    
    # Get category ID if exists
    category = await CategoryService.get_by_name(db, category_name, current_user_id)
    category_id = category.id if category else None
    
    pattern = await categorization_service.learn_pattern(
        user_id=current_user_id,
        raw_description=raw_description,
        category_name=category_name,
        category_id=category_id
    )
    
    return {
        "success": True,
        "pattern_id": pattern.id,
        "usage_count": pattern.usage_count
    }
