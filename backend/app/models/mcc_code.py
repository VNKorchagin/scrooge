"""Model for MCC (Merchant Category Codes) reference data."""
from sqlalchemy import Column, Integer, String
from app.core.database import Base


class MCCCode(Base):
    """MCC codes reference table.
    
    MCC (Merchant Category Code) - 4-digit code used to classify
    businesses by the type of goods or services they provide.
    """
    __tablename__ = "mcc_codes"

    id = Column(Integer, primary_key=True, index=True)
    
    # 4-digit MCC code
    code = Column(String(4), unique=True, nullable=False, index=True)
    
    # Category name in English
    name_en = Column(String, nullable=False)
    
    # Category name in Russian
    name_ru = Column(String, nullable=True)
    
    # Suggested expense category for this MCC
    suggested_category_en = Column(String, nullable=True)
    suggested_category_ru = Column(String, nullable=True)
    
    # Transaction type: 'income' or 'expense'
    transaction_type = Column(String, default='expense', nullable=False)


def get_default_mcc_codes() -> list:
    """Return default MCC codes for popular categories."""
    return [
        # Groceries / Supermarkets
        {"code": "5411", "name_en": "Grocery Stores", "name_ru": "Продуктовые магазины", 
         "suggested_category_en": "Groceries", "suggested_category_ru": "Продукты"},
        {"code": "5422", "name_en": "Freezer/Meat Provisioners", "name_ru": "Мясные магазины",
         "suggested_category_en": "Groceries", "suggested_category_ru": "Продукты"},
        {"code": "5441", "name_en": "Candy/Nut/Confection", "name_ru": "Кондитерские",
         "suggested_category_en": "Groceries", "suggested_category_ru": "Продукты"},
        {"code": "5451", "name_en": "Dairy Products", "name_ru": "Молочные продукты",
         "suggested_category_en": "Groceries", "suggested_category_ru": "Продукты"},
        {"code": "5462", "name_en": "Bakeries", "name_ru": "Пекарни",
         "suggested_category_en": "Groceries", "suggested_category_ru": "Продукты"},
        
        # Restaurants / Food
        {"code": "5812", "name_en": "Eating Places", "name_ru": "Рестораны",
         "suggested_category_en": "Restaurants", "suggested_category_ru": "Кафе и рестораны"},
        {"code": "5813", "name_en": "Drinking Places", "name_ru": "Бары",
         "suggested_category_en": "Restaurants", "suggested_category_ru": "Кафе и рестораны"},
        {"code": "5814", "name_en": "Fast Food", "name_ru": "Фастфуд",
         "suggested_category_en": "Restaurants", "suggested_category_ru": "Кафе и рестораны"},
        
        # Transport / Gas
        {"code": "5541", "name_en": "Gas Stations", "name_ru": "АЗС",
         "suggested_category_en": "Transport", "suggested_category_ru": "Транспорт"},
        {"code": "5542", "name_en": "Automated Fuel Dispensers", "name_ru": "Топливные терминалы",
         "suggested_category_en": "Transport", "suggested_category_ru": "Транспорт"},
        {"code": "4111", "name_en": "Local Transport", "name_ru": "Общественный транспорт",
         "suggested_category_en": "Transport", "suggested_category_ru": "Транспорт"},
        {"code": "4112", "name_en": "Passenger Rail", "name_ru": "Ж/д транспорт",
         "suggested_category_en": "Transport", "suggested_category_ru": "Транспорт"},
        {"code": "4119", "name_en": "Ambulance Services", "name_ru": "Скорая помощь",
         "suggested_category_en": "Transport", "suggested_category_ru": "Транспорт"},
        {"code": "4121", "name_en": "Taxicabs", "name_ru": "Такси",
         "suggested_category_en": "Transport", "suggested_category_ru": "Транспорт"},
        
        # Entertainment
        {"code": "7832", "name_en": "Motion Picture Theaters", "name_ru": "Кинотеатры",
         "suggested_category_en": "Entertainment", "suggested_category_ru": "Развлечения"},
        {"code": "7922", "name_en": "Theatrical Producers", "name_ru": "Театры",
         "suggested_category_en": "Entertainment", "suggested_category_ru": "Развлечения"},
        {"code": "7994", "name_en": "Video Game Arcades", "name_ru": "Игровые автоматы",
         "suggested_category_en": "Entertainment", "suggested_category_ru": "Развлечения"},
        {"code": "7996", "name_en": "Amusement Parks", "name_ru": "Парки развлечений",
         "suggested_category_en": "Entertainment", "suggested_category_ru": "Развлечения"},
        
        # Health / Pharmacy
        {"code": "5912", "name_en": "Drug Stores", "name_ru": "Аптеки",
         "suggested_category_en": "Health", "suggested_category_ru": "Здоровье"},
        {"code": "8011", "name_en": "Doctors", "name_ru": "Врачи",
         "suggested_category_en": "Health", "suggested_category_ru": "Здоровье"},
        {"code": "8021", "name_en": "Dentists", "name_ru": "Стоматологи",
         "suggested_category_en": "Health", "suggested_category_ru": "Здоровье"},
        {"code": "8031", "name_en": "Optometrists", "name_ru": "Оптика",
         "suggested_category_en": "Health", "suggested_category_ru": "Здоровье"},
        
        # Shopping / Clothing
        {"code": "5651", "name_en": "Family Clothing", "name_ru": "Одежда",
         "suggested_category_en": "Clothing", "suggested_category_ru": "Одежда"},
        {"code": "5661", "name_en": "Shoe Stores", "name_ru": "Обувь",
         "suggested_category_en": "Clothing", "suggested_category_ru": "Одежда"},
        {"code": "5311", "name_en": "Department Stores", "name_ru": "Универмаги",
         "suggested_category_en": "Shopping", "suggested_category_ru": "Покупки"},
        
        # Utilities / Bills
        {"code": "4900", "name_en": "Utilities", "name_ru": "Коммунальные услуги",
         "suggested_category_en": "Utilities", "suggested_category_ru": "ЖКХ"},
        {"code": "4814", "name_en": "Telecom", "name_ru": "Связь",
         "suggested_category_en": "Utilities", "suggested_category_ru": "ЖКХ"},
        {"code": "4899", "name_en": "Cable/Satellite", "name_ru": "ТВ/Интернет",
         "suggested_category_en": "Utilities", "suggested_category_ru": "ЖКХ"},
        
        # Electronics
        {"code": "5732", "name_en": "Electronics", "name_ru": "Электроника",
         "suggested_category_en": "Electronics", "suggested_category_ru": "Электроника"},
        {"code": "5946", "name_en": "Camera/Photo", "name_ru": "Фото",
         "suggested_category_en": "Electronics", "suggested_category_ru": "Электроника"},
        
        # Home / Construction
        {"code": "5200", "name_en": "Home Supply", "name_ru": "Товары для дома",
         "suggested_category_en": "Home", "suggested_category_ru": "Дом"},
        {"code": "5712", "name_en": "Furniture", "name_ru": "Мебель",
         "suggested_category_en": "Home", "suggested_category_ru": "Дом"},
        
        # Sports / Fitness
        {"code": "5941", "name_en": "Sporting Goods", "name_ru": "Спорттовары",
         "suggested_category_en": "Sports", "suggested_category_ru": "Спорт"},
        {"code": "7997", "name_en": "Golf Courses", "name_ru": "Гольф",
         "suggested_category_en": "Sports", "suggested_category_ru": "Спорт"},
        
        # Education
        {"code": "8299", "name_en": "Schools", "name_ru": "Образование",
         "suggested_category_en": "Education", "suggested_category_ru": "Образование"},
        {"code": "8211", "name_en": "Elementary Schools", "name_ru": "Школы",
         "suggested_category_en": "Education", "suggested_category_ru": "Образование"},
        {"code": "8220", "name_en": "Colleges", "name_ru": "Колледжи",
         "suggested_category_en": "Education", "suggested_category_ru": "Образование"},
        
        # Services
        {"code": "7210", "name_en": "Laundry", "name_ru": "Химчистка",
         "suggested_category_en": "Services", "suggested_category_ru": "Услуги"},
        {"code": "7230", "name_en": "Beauty Shops", "name_ru": "Салоны красоты",
         "suggested_category_en": "Services", "suggested_category_ru": "Услуги"},
        {"code": "7299", "name_en": "Other Services", "name_ru": "Прочие услуги",
         "suggested_category_en": "Services", "suggested_category_ru": "Услуги"},
    ]
