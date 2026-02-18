"""PDF parser for bank statements."""
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import List, Optional, Dict, Any
from io import BytesIO

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

from app.services.import_service import ParsedTransaction, TransactionType


class PDFParser:
    """Parser for bank statement PDFs."""
    
    # Common date patterns in PDFs
    DATE_PATTERNS = [
        r"(\d{2})\.(\d{2})\.(\d{4})",  # DD.MM.YYYY
        r"(\d{2})/(\d{2})/(\d{4})",    # MM/DD/YYYY or DD/MM/YYYY
        r"(\d{4})-(\d{2})-(\d{2})",    # YYYY-MM-DD
        r"(\d{2})-(\d{2})-(\d{4})",    # DD-MM-YYYY
    ]
    
    # Amount patterns
    AMOUNT_PATTERNS = [
        r"([+-]?\d+[\s\xa0]?\d*,\d{2})",  # European format with comma
        r"([+-]?\d+[\s\xa0]?\d*\.\d{2})",  # US format with dot
    ]
    
    @staticmethod
    def extract_text(content: bytes) -> str:
        """Extract text from PDF content."""
        if not PDFPLUMBER_AVAILABLE and not PYMUPDF_AVAILABLE:
            raise ImportError("No PDF parser available. Install pdfplumber or pymupdf.")
        
        text = ""
        
        # Try pdfplumber first
        if PDFPLUMBER_AVAILABLE:
            try:
                with pdfplumber.open(BytesIO(content)) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
            except Exception as e:
                if not PYMUPDF_AVAILABLE:
                    raise e
        
        # Fallback to PyMuPDF
        if not text and PYMUPDF_AVAILABLE:
            try:
                doc = fitz.open(stream=content, filetype="pdf")
                for page in doc:
                    text += page.get_text() + "\n"
                doc.close()
            except Exception as e:
                raise e
        
        return text
    
    @staticmethod
    def extract_tables(content: bytes) -> List[List[List[str]]]:
        """Extract tables from PDF content."""
        if not PDFPLUMBER_AVAILABLE:
            raise ImportError("pdfplumber required for table extraction")
        
        tables = []
        with pdfplumber.open(BytesIO(content)) as pdf:
            for page in pdf.pages:
                page_tables = page.extract_tables()
                tables.extend(page_tables)
        return tables
    
    @staticmethod
    def _parse_amount(amount_str: str) -> Optional[Decimal]:
        """Parse amount from string."""
        if not amount_str:
            return None
        
        # Clean the string
        cleaned = amount_str.strip()
        cleaned = re.sub(r'\s+', '', cleaned)  # Remove spaces
        cleaned = cleaned.replace('\xa0', '')  # Remove non-breaking spaces
        cleaned = cleaned.replace(',', '.')     # Normalize decimal separator
        
        # Remove currency symbols
        cleaned = re.sub(r'[₽$€£]', '', cleaned)
        
        try:
            # Check if negative
            is_negative = cleaned.startswith('-') or 'дб' in cleaned.lower()
            cleaned = cleaned.lstrip('+-')
            
            amount = Decimal(cleaned)
            if is_negative:
                amount = -amount
            
            return amount
        except (InvalidOperation, ValueError):
            return None
    
    @staticmethod
    def _parse_date(date_str: str) -> Optional[datetime]:
        """Parse date from string."""
        if not date_str:
            return None
        
        date_str = date_str.strip()
        formats = [
            "%d.%m.%Y",
            "%d.%m.%y",
            "%d/%m/%Y",
            "%d/%m/%y",
            "%Y-%m-%d",
            "%d-%m-%Y",
            "%m/%d/%Y",
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        return None
    
    @classmethod
    def parse_tinkoff_pdf(cls, content: bytes) -> List[ParsedTransaction]:
        """Parse Tinkoff Bank PDF statement."""
        transactions = []
        tables = cls.extract_tables(content)
        
        for table in tables:
            for row in table:
                if len(row) < 4:
                    continue
                
                # Tinkoff PDF structure: Date | Description | Amount | Balance
                date_str = str(row[0]) if row[0] else ""
                description = str(row[1]) if row[1] else ""
                amount_str = str(row[2]) if row[2] else ""
                
                if not description or not amount_str:
                    continue
                
                amount = cls._parse_amount(amount_str)
                if not amount:
                    continue
                
                date = cls._parse_date(date_str)
                
                # Determine type
                if amount < 0:
                    tx_type = TransactionType.EXPENSE
                    amount = abs(amount)
                else:
                    tx_type = TransactionType.INCOME
                
                transactions.append(ParsedTransaction(
                    raw_description=description.strip(),
                    amount=amount,
                    transaction_date=date,
                    type=tx_type
                ))
        
        return transactions
    
    @classmethod
    def parse_sber_pdf(cls, content: bytes) -> List[ParsedTransaction]:
        """Parse SberBank PDF statement."""
        transactions = []
        text = cls.extract_text(content)
        
        # Sber statements often have a specific format
        # Try to find transaction lines
        lines = text.split('\n')
        
        for line in lines:
            # Pattern: Date Description Amount
            # e.g., "01.01.2024 PYATYOROCHKA -500.00"
            match = re.search(
                r'(\d{2}\.\d{2}\.\d{4})\s+(.+?)\s+(-?\d+[\s\xa0]?\d*[,.]\d{2})',
                line
            )
            
            if match:
                date_str = match.group(1)
                description = match.group(2).strip()
                amount_str = match.group(3)
                
                amount = cls._parse_amount(amount_str)
                if not amount:
                    continue
                
                date = cls._parse_date(date_str)
                
                if amount < 0:
                    tx_type = TransactionType.EXPENSE
                    amount = abs(amount)
                else:
                    tx_type = TransactionType.INCOME
                
                transactions.append(ParsedTransaction(
                    raw_description=description,
                    amount=amount,
                    transaction_date=date,
                    type=tx_type
                ))
        
        return transactions
    
    @classmethod
    def parse_generic_pdf(cls, content: bytes) -> List[ParsedTransaction]:
        """Generic PDF parser using heuristics."""
        transactions = []
        text = cls.extract_text(content)
        lines = text.split('\n')
        
        for line in lines:
            # Look for patterns that look like transactions
            # Date + Description + Amount
            
            # Try to find date
            date = None
            for pattern in cls.DATE_PATTERNS:
                match = re.search(pattern, line)
                if match:
                    date_str = match.group(0)
                    date = cls._parse_date(date_str)
                    if date:
                        break
            
            # Try to find amount
            amount = None
            for pattern in cls.AMOUNT_PATTERNS:
                matches = re.findall(pattern, line)
                for match in matches:
                    amt = cls._parse_amount(match)
                    if amt and abs(amt) > 0:
                        amount = amt
                        break
                if amount:
                    break
            
            if date and amount:
                # Extract description (everything between date and amount)
                line_clean = re.sub(cls.DATE_PATTERNS[0], '', line, count=1)
                for pattern in cls.AMOUNT_PATTERNS:
                    line_clean = re.sub(pattern, '', line_clean)
                
                description = line_clean.strip()
                
                # Clean up description
                description = re.sub(r'\s+', ' ', description)
                description = description.strip(' |:-')
                
                if description and len(description) > 2:
                    if amount < 0:
                        tx_type = TransactionType.EXPENSE
                        amount = abs(amount)
                    else:
                        tx_type = TransactionType.INCOME
                    
                    transactions.append(ParsedTransaction(
                        raw_description=description,
                        amount=amount,
                        transaction_date=date,
                        type=tx_type
                    ))
        
        return transactions
    
    @classmethod
    def parse(cls, content: bytes, bank_hint: Optional[str] = None) -> List[ParsedTransaction]:
        """
        Parse PDF content into transactions.
        
        Args:
            content: PDF file content
            bank_hint: Optional hint about bank type ('tinkoff', 'sber', etc.)
        """
        # Try specific parsers first if hint provided
        if bank_hint:
            bank_hint = bank_hint.lower()
            if 'tinkoff' in bank_hint or 'тинькофф' in bank_hint:
                return cls.parse_tinkoff_pdf(content)
            elif 'sber' in bank_hint or 'сбер' in bank_hint:
                return cls.parse_sber_pdf(content)
        
        # Try to detect by content
        try:
            return cls.parse_tinkoff_pdf(content)
        except Exception:
            pass
        
        try:
            return cls.parse_sber_pdf(content)
        except Exception:
            pass
        
        # Fallback to generic parser
        return cls.parse_generic_pdf(content)
