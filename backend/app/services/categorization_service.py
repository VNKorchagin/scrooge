"""Hybrid categorization service for bank transactions."""
import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from thefuzz import fuzz

from app.models.transaction_pattern import TransactionPattern
from app.models.mcc_code import MCCCode
from app.models.transaction import Transaction
from app.models.category import Category


@dataclass
class CategorySuggestion:
    """Category suggestion with confidence info."""
    category: str
    score: float
    source: str  # 'pattern', 'mcc', 'fuzzy', 'ml', 'default'


class CategorizationService:
    """Hybrid categorization using rules, ML, and fuzzy matching."""
    
    # Default regex patterns for common merchants
    MERCHANT_PATTERNS = {
        # Groceries / Supermarkets
        r"пят[её]рочка|pyaterochka|pyatyorochka|x5 retail": ("Groceries", "Продукты"),
        r"магнит|magnit": ("Groceries", "Продукты"),
        r"лента|lenta": ("Groceries", "Продукты"),
        r"ашан|auchan|auchan hyper": ("Groceries", "Продукты"),
        r"перекр[её]сток|perekrestok|x5 group": ("Groceries", "Продукты"),
        r"вкусвилл|vkusvill": ("Groceries", "Продукты"),
        r"метро|metro cash": ("Groceries", "Продукты"),
        r"окей|okey": ("Groceries", "Продукты"),
        r" Spar |спар": ("Groceries", "Продукты"),
        r"dixy|дикси": ("Groceries", "Продукты"),
        r" fix price|фикс прайс": ("Groceries", "Продукты"),
        
        # Restaurants / Food Delivery
        r"яндекс.?еда|yandex.?eda|eda\.yandex": ("Restaurants", "Кафе и рестораны"),
        r"delivery club|деливери клаб|доставка еды": ("Restaurants", "Кафе и рестораны"),
        r"sberfood|сберфуд|сбер еда": ("Restaurants", "Кафе и рестораны"),
        r"mcdonalds|макдоналдс|макдак": ("Restaurants", "Кафе и рестораны"),
        r"kfc|кфс": ("Restaurants", "Кафе и рестораны"),
        r"burger king|бургер кинг|bk": ("Restaurants", "Кафе и рестораны"),
        r"starbucks|старбакс": ("Restaurants", "Кафе и рестораны"),
        r"coffee like|кофе лайк": ("Restaurants", "Кафе и рестораны"),
        r"шоколадница|shokoladnitsa": ("Restaurants", "Кафе и рестораны"),
        r"кафе|cafe|restaurant": ("Restaurants", "Кафе и рестораны"),
        
        # Transport / Gas
        r"shell|шелл": ("Transport", "Транспорт"),
        r"газпромнефть|gazpromneft|gpnbest": ("Transport", "Транспорт"),
        r"лукойл|lukoil": ("Transport", "Транспорт"),
        r"татнефть|tatneft": ("Transport", "Транспорт"),
        r"роснефть|rosneft": ("Transport", "Транспорт"),
        r"башнефть|bashneft": ("Transport", "Транспорт"),
        r"bp gas|бп": ("Transport", "Транспорт"),
        r"экто|ekto": ("Transport", "Транспорт"),
        r"uber|убер|yandex\.taxi|яндекс.?такси": ("Transport", "Транспорт"),
        r"citymobil|ситимобил|sitimobil": ("Transport", "Транспорт"),
        r"gett|гетт": ("Transport", "Транспорт"),
        r"метро|subway|underground": ("Transport", "Транспорт"),
        r"аэроэкспресс|aeroexpress": ("Transport", "Транспорт"),
        r"ржд|rzd|ж/д|поезд": ("Transport", "Транспорт"),
        r"авиабилет|airline|aeroflot|победа|s7 airlines": ("Transport", "Транспорт"),
        
        # Entertainment
        r"кино|cinema|kinopoisk|кинопоиск": ("Entertainment", "Развлечения"),
        r"ivi|иви|amediateka|амедиатека": ("Entertainment", "Развлечения"),
        r"okko|окко": ("Entertainment", "Развлечения"),
        r"wink|винк": ("Entertainment", "Развлечения"),
        r"netflix|нетфликс": ("Entertainment", "Развлечения"),
        r"spotify|спотифай": ("Entertainment", "Развлечения"),
        r"youtube|ютуб|ютуп": ("Entertainment", "Развлечения"),
        r"twitch|твич": ("Entertainment", "Развлечения"),
        r"steam|стим": ("Entertainment", "Развлечения"),
        r"origin|ориджин": ("Entertainment", "Развлечения"),
        r"epic games|эпик геймс": ("Entertainment", "Развлечения"),
        r"playstation|плейстейшн|ps store": ("Entertainment", "Развлечения"),
        r"xbox|иксбокс": ("Entertainment", "Развлечения"),
        r" Bowling|боулинг": ("Entertainment", "Развлечения"),
        r"картинг|karting": ("Entertainment", "Развлечения"),
        
        # Health / Pharmacy
        r"аптека|pharmacy|apteka|eapteka|еаптека": ("Health", "Здоровье"),
        r"аптека\.ру|apteka\.ru": ("Health", "Здоровье"),
        r"самсон.?фарма|samson.?pharma": ("Health", "Здоровье"),
        r" Rigla|ригла": ("Health", "Здоровье"),
        r"Асна|asna": ("Health", "Здоровье"),
        r"366|три шесть": ("Health", "Здоровье"),
        r"поликлиника|clinic": ("Health", "Здоровье"),
        r"стоматолог|dentist": ("Health", "Здоровье"),
        
        # Electronics / Tech
        r"dns|днс технопоинт": ("Electronics", "Электроника"),
        r"ситилинк|citilink": ("Electronics", "Электроника"),
        r"м\.видео|m\.video": ("Electronics", "Электроника"),
        r"эльдорадо|eldorado": ("Electronics", "Электроника"),
        r" re:store|ristor|apple": ("Electronics", "Электроника"),
        r"samsung|самсунг": ("Electronics", "Электроника"),
        r"xiaomi|сяоми|ксяоми": ("Electronics", "Электроника"),
        r"ozon|озон|ozon\.ru": ("Electronics", "Электроника"),
        r"wildberries|вайлдберриз|wb": ("Electronics", "Электроника"),
        r"aliexpress|алиэкспресс|alibaba|алибаба": ("Electronics", "Электроника"),
        r"yandex\.market|яндекс.?маркет|беру": ("Electronics", "Электроника"),
        
        # Home / DIY
        r"leroy|леруа|leroy merlin": ("Home", "Дом"),
        r"obi|оби": ("Home", "Дом"),
        r"ikea|икея": ("Home", "Дом"),
        r"hoff|хофф": ("Home", "Дом"),
        r"столплит|stolplit": ("Home", "Дом"),
        r"максидом|maxidom": ("Home", "Дом"),
        r"петрович|petrovich": ("Home", "Дом"),
        r"все инструменты|vseinstrumenti": ("Home", "Дом"),
        
        # Clothing
        r"hm|h&m|h & m": ("Clothing", "Одежда"),
        r"zara|зара": ("Clothing", "Одежда"),
        r"uniqlo|уникло|юникло": ("Clothing", "Одежда"),
        r"reserved|резервед": ("Clothing", "Одежда"),
        r"mango|манго": ("Clothing", "Одежда"),
        r"lamoda|ламода": ("Clothing", "Одежда"),
        r" sportmaster|спортмастер": ("Clothing", "Одежда"),
        r"decathlon|декатлон": ("Clothing", "Одежда"),
        
        # Services / Beauty
        r"салон красоты|beauty salon": ("Services", "Услуги"),
        r"маникюр|nail": ("Services", "Услуги"),
        r"парикмахерская|hair": ("Services", "Услуги"),
        r"химчистка|химчист|dry clean": ("Services", "Услуги"),
        r"прачечная|laundry": ("Services", "Услуги"),
        r"ремонт|repair service": ("Services", "Услуги"),
        
        # Finance / Banking
        r"проценты|percent|interest": ("Income", "Доход", "income"),
        r"зарплата|salary|payroll": ("Income", "Доход", "income"),
        r"премия|bonus": ("Income", "Доход", "income"),
        r"аванс|advance": ("Income", "Доход", "income"),
        r"перевод|transfer|p2p": ("Transfer", "Перевод"),
        r"погашение кредита|loan payment": ("Loans", "Кредиты"),
        
        # Subscriptions / Internet
        r"мтс|mts": ("Utilities", "ЖКХ"),
        r"билайн|beeline|вымпелком": ("Utilities", "ЖКХ"),
        r"мегафон|megafon": ("Utilities", "ЖКХ"),
        r"tele2|теле2": ("Utilities", "ЖКХ"),
        r"rostelecom|ростелеком": ("Utilities", "ЖКХ"),
        r"дом\.ru|домру": ("Utilities", "ЖКХ"),
        r"тинькофф.?мобайл|tinkoff mobile": ("Utilities", "ЖКХ"),
        r"yota|йота": ("Utilities", "ЖКХ"),
        r"comcast|verizon|at&t": ("Utilities", "ЖКХ"),
    }
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for matching."""
        text = text.lower().strip()
        # Remove extra spaces
        text = re.sub(r'\s+', ' ', text)
        # Remove special chars for matching but keep for pattern
        return text
    
    async def _get_user_patterns(self, user_id: int) -> List[TransactionPattern]:
        """Get user's transaction patterns ordered by usage count."""
        result = await self.db.execute(
            select(TransactionPattern)
            .where(TransactionPattern.user_id == user_id)
            .order_by(desc(TransactionPattern.usage_count))
        )
        return result.scalars().all()
    
    async def _get_mcc_mapping(self, mcc_code: str, language: str = "en") -> Optional[str]:
        """Get category from MCC code."""
        if not mcc_code:
            return None
        
        result = await self.db.execute(
            select(MCCCode).where(MCCCode.code == mcc_code)
        )
        mcc = result.scalar_one_or_none()
        
        if mcc:
            if language == "ru":
                return mcc.suggested_category_ru or mcc.suggested_category_en
            return mcc.suggested_category_en or mcc.suggested_category_ru
        return None
    
    async def _match_user_pattern(
        self, 
        raw_description: str, 
        user_id: int
    ) -> Optional[CategorySuggestion]:
        """Match against user's learned patterns."""
        patterns = await self._get_user_patterns(user_id)
        normalized = self._normalize_text(raw_description)
        
        for pattern in patterns:
            # Exact match on normalized pattern
            if pattern.normalized_pattern == normalized:
                return CategorySuggestion(
                    category=pattern.category_name,
                    score=min(0.95 + (pattern.usage_count * 0.01), 0.99),
                    source="pattern"
                )
            
            # Fuzzy match on raw description
            similarity = fuzz.ratio(
                pattern.raw_description.lower(), 
                raw_description.lower()
            )
            if similarity >= 85:
                return CategorySuggestion(
                    category=pattern.category_name,
                    score=similarity / 100,
                    source="fuzzy"
                )
            
            # Partial ratio for substring matching
            partial = fuzz.partial_ratio(
                pattern.normalized_pattern,
                normalized
            )
            if partial >= 90:
                return CategorySuggestion(
                    category=pattern.category_name,
                    score=partial / 100,
                    source="fuzzy"
                )
        
        return None
    
    def _match_regex_patterns(self, raw_description: str, language: str = "en") -> Optional[CategorySuggestion]:
        """Match against predefined regex patterns."""
        normalized = raw_description.lower()
        
        for pattern, categories in self.MERCHANT_PATTERNS.items():
            if re.search(pattern, normalized, re.IGNORECASE):
                # Check if this is an income pattern (has 3 elements)
                if len(categories) == 3:
                    category = categories[0]  # Use English version
                else:
                    category = categories[0] if language == "en" else categories[1]
                
                return CategorySuggestion(
                    category=category,
                    score=0.85,
                    source="regex"
                )
        
        return None
    
    async def _match_transaction_history(
        self, 
        raw_description: str, 
        user_id: int
    ) -> Optional[CategorySuggestion]:
        """Match against user's transaction history."""
        # Get recent transactions with similar descriptions
        result = await self.db.execute(
            select(Transaction)
            .where(Transaction.user_id == user_id)
            .where(Transaction.raw_description.isnot(None))
            .order_by(desc(Transaction.created_at))
            .limit(100)
        )
        transactions = result.scalars().all()
        
        best_match = None
        best_score = 0
        
        for tx in transactions:
            if not tx.raw_description:
                continue
            
            similarity = fuzz.ratio(
                tx.raw_description.lower(),
                raw_description.lower()
            )
            
            if similarity > best_score and similarity >= 80:
                best_score = similarity
                best_match = tx
        
        if best_match:
            return CategorySuggestion(
                category=best_match.category_name,
                score=best_score / 100,
                source="history"
            )
        
        return None
    
    async def categorize(
        self, 
        user_id: int,
        raw_description: str,
        mcc_code: Optional[str] = None,
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Categorize transaction using hybrid approach.
        
        Priority:
        1. User's learned patterns (highest confidence)
        2. MCC code lookup
        3. Regex patterns for known merchants
        4. Fuzzy match on transaction history
        5. Default category (requires manual review)
        """
        if not raw_description or raw_description.strip() == "":
            return {
                "category": "Other" if language == "en" else "Другое",
                "confidence": "low",
                "score": 0.0
            }
        
        # 1. Check user's learned patterns
        suggestion = await self._match_user_pattern(raw_description, user_id)
        if suggestion and suggestion.score >= 0.9:
            return {
                "category": suggestion.category,
                "confidence": "high",
                "score": suggestion.score
            }
        
        # 2. Check MCC code
        if mcc_code:
            mcc_category = await self._get_mcc_mapping(mcc_code, language)
            if mcc_category:
                return {
                    "category": mcc_category,
                    "confidence": "high",
                    "score": 0.85
                }
        
        # 3. Check regex patterns
        regex_match = self._match_regex_patterns(raw_description, language)
        if regex_match:
            return {
                "category": regex_match.category,
                "confidence": "medium",
                "score": regex_match.score
            }
        
        # 4. Check transaction history
        history_match = await self._match_transaction_history(raw_description, user_id)
        if history_match and history_match.score >= 0.8:
            return {
                "category": history_match.category,
                "confidence": "medium",
                "score": history_match.score
            }
        
        # 5. If we had a pattern match earlier with lower confidence
        if suggestion and suggestion.score >= 0.7:
            return {
                "category": suggestion.category,
                "confidence": "medium",
                "score": suggestion.score
            }
        
        # 6. Default - requires manual review
        default_category = "Other" if language == "en" else "Другое"
        return {
            "category": default_category,
            "confidence": "low",
            "score": 0.0
        }
    
    async def learn_pattern(
        self,
        user_id: int,
        raw_description: str,
        category_name: str,
        category_id: Optional[int] = None,
        mcc_code: Optional[str] = None
    ) -> TransactionPattern:
        """Learn a new pattern from user confirmation."""
        normalized = self._normalize_text(raw_description)
        
        # Check if pattern already exists
        result = await self.db.execute(
            select(TransactionPattern)
            .where(TransactionPattern.user_id == user_id)
            .where(TransactionPattern.normalized_pattern == normalized)
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            # Update usage count
            existing.usage_count += 1
            existing.category_name = category_name
            if category_id:
                existing.category_id = category_id
            await self.db.commit()
            await self.db.refresh(existing)
            return existing
        
        # Create new pattern
        pattern = TransactionPattern(
            user_id=user_id,
            raw_description=raw_description,
            normalized_pattern=normalized,
            category_name=category_name,
            category_id=category_id,
            mcc_code=mcc_code,
            type="expense",  # Default, could be inferred
            usage_count=1
        )
        
        self.db.add(pattern)
        await self.db.commit()
        await self.db.refresh(pattern)
        return pattern
