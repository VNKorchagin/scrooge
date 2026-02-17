"""Service for currency exchange rates and conversion."""
from decimal import Decimal
from datetime import datetime
from typing import Optional
import httpx

from app.models.transaction import Transaction


class CurrencyService:
    """Service for currency operations."""
    
    CBR_API_URL = "https://www.cbr-xml-daily.ru/daily_json.js"
    
    @staticmethod
    async def get_usd_to_rub_rate() -> Optional[float]:
        """Get current USD to RUB exchange rate from Central Bank of Russia."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(CurrencyService.CBR_API_URL, timeout=10.0)
                response.raise_for_status()
                data = response.json()
                
                # Get USD rate
                usd_data = data.get("Valute", {}).get("USD", {})
                rate = usd_data.get("Value")
                
                if rate:
                    return float(rate)
                return None
        except Exception as e:
            print(f"Error fetching currency rate: {e}")
            return None
    
    @staticmethod
    async def get_exchange_rate(from_currency: str, to_currency: str) -> Optional[float]:
        """Get exchange rate between two currencies."""
        if from_currency == to_currency:
            return 1.0
        
        if from_currency == "USD" and to_currency == "RUB":
            return await CurrencyService.get_usd_to_rub_rate()
        elif from_currency == "RUB" and to_currency == "USD":
            rate = await CurrencyService.get_usd_to_rub_rate()
            return 1.0 / rate if rate else None
        
        return None
    
    @staticmethod
    def convert_amount(amount: Decimal, from_currency: str, to_currency: str, rate: float) -> Decimal:
        """Convert amount from one currency to another."""
        if from_currency == to_currency:
            return amount
        
        if from_currency == "USD" and to_currency == "RUB":
            return amount * Decimal(str(rate))
        elif from_currency == "RUB" and to_currency == "USD":
            return amount / Decimal(str(rate))
        
        return amount
    
    @staticmethod
    async def convert_all_transactions(
        transactions: list[Transaction], 
        from_currency: str, 
        to_currency: str
    ) -> tuple[list[Transaction], float]:
        """Convert all transaction amounts to new currency."""
        rate = await CurrencyService.get_exchange_rate(from_currency, to_currency)
        if not rate:
            raise ValueError(f"Could not get exchange rate for {from_currency} to {to_currency}")
        
        # Create new transactions with converted amounts
        converted_transactions = []
        for tx in transactions:
            new_tx = Transaction(
                id=tx.id,
                user_id=tx.user_id,
                type=tx.type,
                amount=CurrencyService.convert_amount(tx.amount, from_currency, to_currency, rate),
                category_id=tx.category_id,
                category_name=tx.category_name,
                description=tx.description,
                raw_description=tx.raw_description,
                transaction_date=tx.transaction_date,
                source=tx.source,
                created_at=tx.created_at
            )
            converted_transactions.append(new_tx)
        
        return converted_transactions, rate
