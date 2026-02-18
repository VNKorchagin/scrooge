"""Add import tables for transaction patterns and MCC codes

Revision ID: 005
Revises: 004
Create Date: 2024-02-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '005'
down_revision: Union[str, None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create MCC codes table
    op.create_table(
        'mcc_codes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=4), nullable=False),
        sa.Column('name_en', sa.String(), nullable=False),
        sa.Column('name_ru', sa.String(), nullable=True),
        sa.Column('suggested_category_en', sa.String(), nullable=True),
        sa.Column('suggested_category_ru', sa.String(), nullable=True),
        sa.Column('transaction_type', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    op.create_index(op.f('ix_mcc_codes_code'), 'mcc_codes', ['code'], unique=True)
    op.create_index(op.f('ix_mcc_codes_id'), 'mcc_codes', ['id'], unique=False)
    
    # Create transaction patterns table
    op.create_table(
        'transaction_patterns',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('raw_description', sa.String(), nullable=False),
        sa.Column('normalized_pattern', sa.String(), nullable=False),
        sa.Column('category_name', sa.String(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=True),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('mcc_code', sa.String(length=4), nullable=True),
        sa.Column('usage_count', sa.Integer(), nullable=False, server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_transaction_patterns_id'), 'transaction_patterns', ['id'], unique=False)
    op.create_index(op.f('ix_transaction_patterns_normalized_pattern'), 'transaction_patterns', ['normalized_pattern'], unique=False)
    op.create_index(op.f('ix_transaction_patterns_user_id'), 'transaction_patterns', ['user_id'], unique=False)
    op.create_index('ix_patterns_user_normalized', 'transaction_patterns', ['user_id', 'normalized_pattern'], unique=False)
    
    # Insert default MCC codes
    mcc_codes = [
        # Groceries
        ("5411", "Grocery Stores", "Продуктовые магазины", "Groceries", "Продукты"),
        ("5422", "Freezer/Meat Provisioners", "Мясные магазины", "Groceries", "Продукты"),
        ("5441", "Candy/Nut/Confection", "Кондитерские", "Groceries", "Продукты"),
        ("5451", "Dairy Products", "Молочные продукты", "Groceries", "Продукты"),
        ("5462", "Bakeries", "Пекарни", "Groceries", "Продукты"),
        # Restaurants
        ("5812", "Eating Places", "Рестораны", "Restaurants", "Кафе и рестораны"),
        ("5813", "Drinking Places", "Бары", "Restaurants", "Кафе и рестораны"),
        ("5814", "Fast Food", "Фастфуд", "Restaurants", "Кафе и рестораны"),
        # Transport/Gas
        ("5541", "Gas Stations", "АЗС", "Transport", "Транспорт"),
        ("5542", "Automated Fuel Dispensers", "Топливные терминалы", "Transport", "Транспорт"),
        ("4111", "Local Transport", "Общественный транспорт", "Transport", "Транспорт"),
        ("4112", "Passenger Rail", "Ж/д транспорт", "Transport", "Транспорт"),
        ("4121", "Taxicabs", "Такси", "Transport", "Транспорт"),
        # Entertainment
        ("7832", "Motion Picture Theaters", "Кинотеатры", "Entertainment", "Развлечения"),
        ("7922", "Theatrical Producers", "Театры", "Entertainment", "Развлечения"),
        ("7996", "Amusement Parks", "Парки развлечений", "Entertainment", "Развлечения"),
        # Health
        ("5912", "Drug Stores", "Аптеки", "Health", "Здоровье"),
        ("8011", "Doctors", "Врачи", "Health", "Здоровье"),
        ("8021", "Dentists", "Стоматологи", "Health", "Здоровье"),
        ("8031", "Optometrists", "Оптика", "Health", "Здоровье"),
        # Shopping
        ("5651", "Family Clothing", "Одежда", "Clothing", "Одежда"),
        ("5661", "Shoe Stores", "Обувь", "Clothing", "Одежда"),
        ("5311", "Department Stores", "Универмаги", "Shopping", "Покупки"),
        # Utilities
        ("4900", "Utilities", "Коммунальные услуги", "Utilities", "ЖКХ"),
        ("4814", "Telecom", "Связь", "Utilities", "ЖКХ"),
        ("4899", "Cable/Satellite", "ТВ/Интернет", "Utilities", "ЖКХ"),
        # Electronics
        ("5732", "Electronics", "Электроника", "Electronics", "Электроника"),
        # Home
        ("5200", "Home Supply", "Товары для дома", "Home", "Дом"),
        ("5712", "Furniture", "Мебель", "Home", "Дом"),
        # Sports
        ("5941", "Sporting Goods", "Спорттовары", "Sports", "Спорт"),
        # Education
        ("8299", "Schools", "Образование", "Education", "Образование"),
        # Services
        ("7210", "Laundry", "Химчистка", "Services", "Услуги"),
        ("7230", "Beauty Shops", "Салоны красоты", "Services", "Услуги"),
    ]
    
    # Insert MCC codes data
    for code, name_en, name_ru, cat_en, cat_ru in mcc_codes:
        op.execute(
            f"INSERT INTO mcc_codes (code, name_en, name_ru, suggested_category_en, suggested_category_ru, transaction_type) "
            f"VALUES ('{code}', '{name_en}', '{name_ru}', '{cat_en}', '{cat_ru}', 'expense')"
        )


def downgrade() -> None:
    op.drop_index('ix_patterns_user_normalized', table_name='transaction_patterns')
    op.drop_index(op.f('ix_transaction_patterns_user_id'), table_name='transaction_patterns')
    op.drop_index(op.f('ix_transaction_patterns_normalized_pattern'), table_name='transaction_patterns')
    op.drop_index(op.f('ix_transaction_patterns_id'), table_name='transaction_patterns')
    op.drop_table('transaction_patterns')
    
    op.drop_index(op.f('ix_mcc_codes_id'), table_name='mcc_codes')
    op.drop_index(op.f('ix_mcc_codes_code'), table_name='mcc_codes')
    op.drop_table('mcc_codes')
