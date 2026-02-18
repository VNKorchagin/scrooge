"""Service for importing bank statements (CSV, PDF)."""
import re
import io
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

import pandas as pd
from thefuzz import fuzz
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transaction import TransactionType
from app.services.category_service import CategoryService
from app.services.categorization_service import CategorizationService


@dataclass
class ParsedTransaction:
    """Represents a transaction parsed from bank statement."""
    raw_description: str
    amount: Decimal
    transaction_date: Optional[datetime]
    mcc_code: Optional[str] = None
    type: Optional[TransactionType] = None
    # Suggested values from categorization
    suggested_category: Optional[str] = None
    confidence: str = "low"  # 'high', 'medium', 'low'
    confidence_score: float = 0.0
    # Duplicate detection
    is_duplicate: bool = False
    duplicate_count: int = 0


class BaseBankAdapter:
    """Base class for bank adapters."""
    
    # Column name mappings - override in subclasses
    COLUMN_MAPPINGS = {}
    ENCODING = "utf-8"
    
    @classmethod
    def detect(cls, df: pd.DataFrame) -> bool:
        """Detect if this adapter can handle the given dataframe."""
        columns = set(df.columns.str.lower())
        required = set(cls.COLUMN_MAPPINGS.keys())
        return required.issubset(columns)
    
    @classmethod
    def parse(cls, df: pd.DataFrame) -> List[ParsedTransaction]:
        """Parse dataframe into list of transactions."""
        raise NotImplementedError
    
    @classmethod
    def _normalize_amount(cls, value: Any) -> Decimal:
        """Normalize amount to Decimal."""
        if pd.isna(value):
            return Decimal("0")
        if isinstance(value, (int, float)):
            return Decimal(str(value))
        # Remove spaces, replace comma with dot
        cleaned = str(value).replace(" ", "").replace(",", ".").replace("\xa0", "")
        try:
            return Decimal(cleaned)
        except InvalidOperation:
            return Decimal("0")
    
    @classmethod
    def _parse_date(cls, value: Any, formats: List[str] = None) -> Optional[datetime]:
        """Parse date from various formats."""
        if pd.isna(value):
            return None
        
        formats = formats or ["%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"]
        date_str = str(value).strip()
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        # Try pandas parser as fallback
        try:
            return pd.to_datetime(value, dayfirst=True).to_pydatetime()
        except:
            return None


class TinkoffAdapter(BaseBankAdapter):
    """Adapter for Tinkoff Bank CSV exports."""
    
    COLUMN_MAPPINGS = {
        "дата операции": "date",
        "дата платежа": "payment_date",
        "номер карты": "card_number",
        "статус": "status",
        "сумма операции": "amount",
        "валюта операции": "currency",
        "сумма платежа": "payment_amount",
        "валюта платежа": "payment_currency",
        "кэшбэк": "cashback",
        "категория": "category",
        "mcc": "mcc",
        "описание": "description",
        "бонусы (включая кэшбэк)": "bonuses",
        "округление на облучение": "rounding",
        "сумма операции с округлением": "rounded_amount",
    }
    ENCODING = "utf-8"
    
    @classmethod
    def detect(cls, df: pd.DataFrame) -> bool:
        columns = set(df.columns.str.lower())
        # Tinkoff-specific columns
        tinkoff_cols = {"дата операции", "описание", "сумма операции", "категория"}
        return tinkoff_cols.issubset(columns)
    
    @classmethod
    def parse(cls, df: pd.DataFrame) -> List[ParsedTransaction]:
        transactions = []
        
        for idx, row in df.iterrows():
            # Skip non-completed transactions
            status = str(row.get("статус", "")).lower()
            if status in ("failed", "отменен", "declined"):
                continue
            
            # Determine amount and type
            raw_amount = row.get("сумма операции")
            amount = cls._normalize_amount(raw_amount)
            if amount == 0:
                amount = cls._normalize_amount(row.get("сумма платежа"))
            
            # Income if amount > 0, expense if < 0
            if amount > 0:
                tx_type = TransactionType.INCOME
            else:
                tx_type = TransactionType.EXPENSE
                amount = abs(amount)
            
            # Parse date (with time from "Дата операции")
            date = cls._parse_date(row.get("дата операции"), formats=["%d.%m.%Y %H:%M:%S", "%d.%m.%Y"])
            
            # Get description
            description = str(row.get("описание", "")).strip()
            
            # Get MCC (clean up - remove .0 suffix from numeric values, limit to 4 chars)
            mcc_raw = row.get("mcc")
            if pd.notna(mcc_raw):
                mcc = str(int(float(mcc_raw))).strip()[:4]
            else:
                mcc = None
            
            # Get category from CSV (bank's own categorization)
            csv_category = str(row.get("категория", "")).strip() if pd.notna(row.get("категория")) else None
            
            transactions.append(ParsedTransaction(
                raw_description=description,
                amount=amount,
                transaction_date=date,
                mcc_code=mcc,
                type=tx_type,
                suggested_category=csv_category  # Use bank's category as initial suggestion
            ))
        
        return transactions


class SberAdapter(BaseBankAdapter):
    """Adapter for SberBank CSV exports."""
    
    COLUMN_MAPPINGS = {
        "дата операции": "date",
        "дата": "date",
        "время": "time",
        "дата/время": "datetime",
        "номер карты": "card",
        "тип": "type",
        "категория": "category",
        "описание": "description",
        "сумма": "amount",
    }
    ENCODING = "cp1251"  # Sber uses Windows-1251
    
    @classmethod
    def detect(cls, df: pd.DataFrame) -> bool:
        columns = set(df.columns.str.lower())
        # Sber-specific columns
        sber_cols = {"дата", "сумма", "описание"}
        return sber_cols.issubset(columns) and "дата операции" not in columns
    
    @classmethod
    def parse(cls, df: pd.DataFrame) -> List[ParsedTransaction]:
        transactions = []
        
        for _, row in df.iterrows():
            # Parse amount - Sber uses +/- format
            amount_str = str(row.get("сумма", "0"))
            # Remove spaces and normalize
            amount_str = amount_str.replace(" ", "").replace("\xa0", "").replace(",", ".")
            
            # Determine type based on sign or column
            if amount_str.startswith("-"):
                tx_type = TransactionType.EXPENSE
                amount = cls._normalize_amount(amount_str[1:])
            elif amount_str.startswith("+"):
                tx_type = TransactionType.INCOME
                amount = cls._normalize_amount(amount_str[1:])
            else:
                # Try to determine from separate column
                amount = cls._normalize_amount(amount_str)
                tx_type_col = str(row.get("тип", "")).lower()
                if any(x in tx_type_col for x in ("доход", "приход", "зачисление", "income")):
                    tx_type = TransactionType.INCOME
                else:
                    tx_type = TransactionType.EXPENSE
            
            # Parse date
            date = cls._parse_date(row.get("дата"))
            if date is None:
                date = cls._parse_date(row.get("дата операции"))
            
            # Get description
            description = str(row.get("описание", "")).strip()
            
            transactions.append(ParsedTransaction(
                raw_description=description,
                amount=amount,
                transaction_date=date,
                mcc_code=None,
                type=tx_type
            ))
        
        return transactions


class AlfaAdapter(BaseBankAdapter):
    """Adapter for Alfa-Bank CSV exports."""
    
    COLUMN_MAPPINGS = {
        "дата": "date",
        "приход": "income",
        "расход": "expense",
        "назначение платежа": "description",
        "описание": "description",
        "контрагент": "counterparty",
        "счет": "account",
    }
    ENCODING = "utf-8"
    
    @classmethod
    def detect(cls, df: pd.DataFrame) -> bool:
        columns = set(df.columns.str.lower())
        # Alfa-specific: separate income/expense columns
        alfa_cols = {"приход", "расход"}  # Income and expense columns
        return alfa_cols.issubset(columns)
    
    @classmethod
    def parse(cls, df: pd.DataFrame) -> List[ParsedTransaction]:
        transactions = []
        
        for _, row in df.iterrows():
            income = cls._normalize_amount(row.get("приход", 0))
            expense = cls._normalize_amount(row.get("расход", 0))
            
            if income > 0:
                tx_type = TransactionType.INCOME
                amount = income
            elif expense > 0:
                tx_type = TransactionType.EXPENSE
                amount = expense
            else:
                continue  # Skip zero transactions
            
            # Parse date
            date = cls._parse_date(row.get("дата"))
            
            # Get description
            description = str(row.get("назначение платежа", row.get("описание", ""))).strip()
            
            transactions.append(ParsedTransaction(
                raw_description=description,
                amount=amount,
                transaction_date=date,
                mcc_code=None,
                type=tx_type
            ))
        
        return transactions


class GenericAdapter(BaseBankAdapter):
    """Generic adapter that tries to auto-detect columns."""
    
    # Common column name patterns
    DATE_PATTERNS = ["date", "дата", "transaction date", "дата операции", "дата транзакции"]
    AMOUNT_PATTERNS = ["amount", "сумма", "sum", "сумма операции", "сумма платежа"]
    DESC_PATTERNS = ["description", "описание", "назначение", "details", "назначение платежа"]
    
    @classmethod
    def detect(cls, df: pd.DataFrame) -> bool:
        # Always falls back to generic
        return True
    
    @classmethod
    def _find_column(cls, columns: List[str], patterns: List[str]) -> Optional[str]:
        """Find column matching any of the patterns."""
        columns_lower = {c.lower(): c for c in columns}
        for pattern in patterns:
            if pattern in columns_lower:
                return columns_lower[pattern]
            # Fuzzy match
            for col_lower, col_orig in columns_lower.items():
                if fuzz.ratio(pattern, col_lower) > 80:
                    return col_orig
        return None
    
    @classmethod
    def parse(cls, df: pd.DataFrame) -> List[ParsedTransaction]:
        columns = list(df.columns)
        
        # Find relevant columns
        date_col = cls._find_column(columns, cls.DATE_PATTERNS)
        amount_col = cls._find_column(columns, cls.AMOUNT_PATTERNS)
        desc_col = cls._find_column(columns, cls.DESC_PATTERNS)
        
        if not amount_col or not desc_col:
            raise ValueError("Could not identify required columns (amount, description)")
        
        transactions = []
        
        for _, row in df.iterrows():
            amount = cls._normalize_amount(row.get(amount_col))
            
            # Try to determine type from sign or separate column
            if amount < 0:
                tx_type = TransactionType.EXPENSE
                amount = abs(amount)
            else:
                # Check if there's a type column
                tx_type = TransactionType.EXPENSE  # Default to expense
                for col in columns:
                    if any(x in col.lower() for x in ["тип", "type"]):
                        type_val = str(row.get(col, "")).lower()
                        if any(x in type_val for x in ["доход", "приход", "income"]):
                            tx_type = TransactionType.INCOME
                        break
            
            date = cls._parse_date(row.get(date_col)) if date_col else None
            description = str(row.get(desc_col, "")).strip()
            
            transactions.append(ParsedTransaction(
                raw_description=description,
                amount=amount,
                transaction_date=date,
                type=tx_type
            ))
        
        return transactions


# Registry of adapters in order of preference
ADAPTERS = [TinkoffAdapter, SberAdapter, AlfaAdapter, GenericAdapter]


class ImportService:
    """Service for importing bank statements."""
    
    @staticmethod
    def detect_adapter(df: pd.DataFrame) -> type:
        """Detect the appropriate adapter for the dataframe."""
        for adapter in ADAPTERS:
            if adapter.detect(df):
                return adapter
        return GenericAdapter
    
    @staticmethod
    def parse_csv(content: bytes, filename: str = "") -> Tuple[List[ParsedTransaction], str]:
        """Parse CSV file content."""
        # Try different encodings
        encodings = ["utf-8", "cp1251", "cp1252", "iso-8859-1"]
        
        df = None
        used_encoding = "utf-8"
        
        for encoding in encodings:
            try:
                # Try with different separators
                for sep in [',', '\t', ';']:
                    try:
                        df = pd.read_csv(io.BytesIO(content), encoding=encoding, sep=sep)
                        if len(df.columns) > 1:  # Valid CSV/TSV should have multiple columns
                            used_encoding = encoding
                            break
                    except:
                        continue
                if df is not None and len(df.columns) > 1:
                    break
            except UnicodeDecodeError:
                continue
        
        if df is None:
            raise ValueError("Could not decode CSV file with any known encoding")
        
        # Clean column names - strip whitespace and convert to lowercase
        df.columns = df.columns.str.strip().str.lower()
        
        # Debug logging
        print(f"DEBUG: Detected columns: {list(df.columns)}")
        print(f"DEBUG: First row: {df.iloc[0].to_dict() if len(df) > 0 else 'empty'}")
        
        # Detect adapter
        adapter = ImportService.detect_adapter(df)
        print(f"DEBUG: Selected adapter: {adapter.__name__}")
        
        # Parse transactions
        transactions = adapter.parse(df)
        
        return transactions, adapter.__name__
    
    @staticmethod
    async def check_duplicates(
        transactions: List[ParsedTransaction],
        user_id: int,
        db: AsyncSession
    ) -> List[ParsedTransaction]:
        """Check each transaction for potential duplicates in database."""
        from app.services.transaction_service import TransactionService
        
        for tx in transactions:
            duplicates = await TransactionService.find_duplicates(
                db,
                user_id,
                tx.raw_description,
                tx.amount,
                tx.transaction_date
            )
            if duplicates:
                tx.is_duplicate = True
                tx.duplicate_count = len(duplicates)
        
        return transactions
    
    @staticmethod
    async def categorize_transactions(
        transactions: List[ParsedTransaction],
        user_id: int,
        db: AsyncSession,
        language: str = "en"
    ) -> List[ParsedTransaction]:
        """Categorize parsed transactions using hybrid approach."""
        categorization_service = CategorizationService(db)
        
        for tx in transactions:
            # Check user's learned patterns first (highest priority)
            result = await categorization_service.categorize(
                user_id=user_id,
                raw_description=tx.raw_description,
                mcc_code=tx.mcc_code,
                language=language
            )
            
            # If user has a pattern - use it
            if result["confidence"] == "high":
                tx.suggested_category = result["category"]
                tx.confidence = result["confidence"]
                tx.confidence_score = result["score"]
            # If CSV has a category and no high-confidence match - use CSV category
            elif tx.suggested_category and tx.suggested_category.strip():
                # Keep CSV category with medium confidence
                tx.confidence = "medium"
                tx.confidence_score = 0.75
            else:
                # Use algorithm result
                tx.suggested_category = result["category"]
                tx.confidence = result["confidence"]
                tx.confidence_score = result["score"]
        
        return transactions
