# AGENTS.md - Scrooge Budget Tracker

## Project Overview

Scrooge is a personal budget tracking application with FastAPI backend and React TypeScript frontend.

## Architecture

```
scrooge/
├── backend/           # FastAPI + SQLAlchemy + PostgreSQL
│   ├── app/
│   │   ├── core/      # Config, security, database
│   │   ├── models/    # SQLAlchemy models
│   │   ├── schemas/   # Pydantic schemas
│   │   ├── routers/   # API endpoints
│   │   └── services/  # Business logic
│   ├── alembic/       # Database migrations
│   └── tests/         # Test suite
├── frontend/          # React + TypeScript + Vite
│   ├── src/
│   │   ├── api/       # Axios client
│   │   ├── components/# React components
│   │   ├── pages/     # Page components
│   │   ├── stores/    # Zustand stores
│   │   └── i18n/      # Translations
│   └── public/
├── docker-compose.yml
└── nginx.conf
```

## Tech Stack

### Backend
- **Framework**: FastAPI (async)
- **ORM**: SQLAlchemy 2.0 with asyncpg
- **Database**: PostgreSQL 15
- **Migrations**: Alembic
- **Auth**: JWT with bcrypt
- **Testing**: pytest with pytest-asyncio

### Frontend
- **Framework**: React 18
- **Build Tool**: Vite
- **State**: Zustand
- **Styling**: Tailwind CSS
- **Charts**: Recharts
- **i18n**: react-i18next
- **HTTP**: Axios

### DevOps
- **Containerization**: Docker + Docker Compose
- **CI/CD**: GitHub Actions
- **Reverse Proxy**: Nginx
- **Deployment**: Auto-deploy on push to main

## Key Features

- Multi-language (EN/RU)
- Multi-currency (USD/RUB) with CBR rates
- **The Vault** - Financial portfolio management (assets, liabilities, deposits, loans)
- **Bank Statement Import** - CSV/PDF import with auto-categorization
- Soft delete for users
- Admin panel
- CSV/TSV/XLSX export
- Real-time currency conversion

## API Structure

All endpoints prefixed with `/v1/`:

- `/auth/*` - Authentication
- `/categories/*` - Categories
- `/transactions/*` - Transactions
- `/stats/*` - Statistics
- `/currency/*` - Currency conversion
- `/export/*` - Data export (CSV/TSV/XLSX)
- `/import/*` - Bank statement import (CSV/PDF)
- `/vault/*` - Financial portfolio (The Vault)
- `/users/admin/*` - Admin operations

## Database

### Soft Delete Pattern
Users are soft-deleted via `is_active=false` and `deleted_at=timestamp`.
Hard delete removes data permanently.

### Key Tables
- `users` - User accounts with settings
- `categories` - User-defined categories
- `transactions` - Income/expense records
- `transaction_patterns` - User's learned categorization patterns
- `mcc_codes` - Merchant Category Codes reference
- `vault_accounts` - Financial accounts (checking, savings, deposits, loans, brokerage)
- `vault_snapshots` - Historical portfolio snapshots
- `vault_projection_settings` - User settings for vault projections
- `predictions` - Future ML table (placeholder)

## Development Guidelines

### Adding New Features
1. Update backend models if needed
2. Create Alembic migration
3. Add API endpoint in routers
4. Update frontend API client
5. Add component/page
6. Update i18n files (see i18n Guidelines below)
7. Write tests
8. Update documentation

### i18n (Internationalization) Guidelines
**CRITICAL: All user-facing text must support both English and Russian.**

When adding new pages, components, or UI elements:
1. **Always use `useTranslation()` hook** - Never hardcode strings
   ```tsx
   const { t } = useTranslation();
   // ❌ Bad: <h1>Dashboard</h1>
   // ✅ Good: <h1>{t('dashboard.title')}</h1>
   ```

2. **Add keys to both language files:**
   - `frontend/src/i18n/locales/en.json`
   - `frontend/src/i18n/locales/ru.json`

3. **Use descriptive nested keys:**
   ```json
   {
     "pageName": {
       "title": "Page Title",
       "button": "Click Me",
       "tooltip": "This explains something"
     }
   }
   ```

4. **Run i18n tests to verify:**
   ```bash
   cd frontend && npm test -- i18n.test.ts
   ```

5. **Common translation keys:**
   - Actions: `save`, `cancel`, `delete`, `edit`, `create`
   - Navigation: `dashboard`, `history`, `settings`
   - Form labels: Match the field name
   - Errors: Use `errors.` prefix

### Testing
- Unit tests for business logic
- Integration tests for API
- i18n tests for translation completeness
- Run with: `pytest -v` (backend) or `npm test` (frontend)
- CI runs tests automatically

### Testing
- Unit tests for business logic
- Integration tests for API
- Run with: `pytest -v`
- CI runs tests automatically

### Code Style
- Backend: PEP 8, type hints
- Frontend: ESLint, Prettier
- Use meaningful variable names
- Comment complex logic

## Deployment

### GitHub Actions Workflow
1. **Test Job**: Runs on every push/PR
   - Installs dependencies
   - Runs pytest
2. **Deploy Job**: Runs on push to main
   - SSH to server
   - Pulls latest code
   - Rebuilds containers
   - Applies migrations

### Manual Deployment (if needed)
```bash
cd /opt/scrooge
git pull
docker-compose up -d --build
docker-compose exec backend alembic upgrade head
```

## Environment Variables

Required in `.env`:
```
SECRET_KEY=<jwt-secret-key>
DB_PASSWORD=<postgres-password>
DATABASE_URL=postgresql+asyncpg://scrooge:${DB_PASSWORD}@db/scrooge_db
```

## CLI Commands

Available in backend container:
```bash
python -m app.cli create-admin <user> <pass>
python -m app.cli create-demo [username] [password]  # Creates demo user with sample data
python -m app.cli list-users
python -m app.cli delete-user <user> [--hard]
python -m app.cli restore-user <user>
```

### Demo User
The `create-demo` command creates a test user pre-populated with realistic data:
- **Default credentials**: `demo` / `demo123`
- **Categories**: 5 income + 10 expense categories
- **Transactions**: 
  - 6+ months of monthly salary ($5000)
  - Occasional freelance income
  - ~80 expense transactions across all categories
- **Use case**: Perfect for testing UI, charts, filters, and reports without manual data entry

## Bank Statement Import Feature

### Overview
Users can import bank statements from CSV or PDF files. The system automatically categorizes transactions using a hybrid approach.

### Supported Formats
- **CSV**: Tinkoff Bank, SberBank, Alfa-Bank, and generic CSV
- **PDF**: Text-based PDF statements from major Russian banks

### Categorization Algorithm
The system uses a 4-tier hybrid approach:

1. **User Patterns (Highest Priority)**
   - Stores user's previous categorization decisions in `transaction_patterns` table
   - Exact match: 99% confidence
   - Fuzzy match (80%+ similarity): variable confidence

2. **MCC Code Lookup**
   - Merchant Category Codes from `mcc_codes` table
   - 85% confidence for known MCCs
   - Pre-loaded with 40+ common MCC codes

3. **Regex Pattern Matching**
   - Predefined patterns for popular merchants (Pyatyorochka, Gazpromneft, Yandex, etc.)
   - 85% confidence
   - Patterns stored in `CategorizationService.MERCHANT_PATTERNS`

4. **Transaction History Fuzzy Match**
   - Matches against user's previous transactions
   - 80%+ similarity threshold
   - Variable confidence based on match quality

### Confidence Levels
- **High (Green)**: User pattern or MCC match - auto-accepted
- **Medium (Yellow)**: Regex or history match - suggested
- **Low (Red)**: Unknown - requires manual category selection

### API Endpoints
- `POST /v1/import/preview` - Upload and preview transactions
- `POST /v1/import/confirm` - Confirm and save transactions
- `POST /v1/import/suggest-category` - Get category suggestion
- `POST /v1/import/learn-pattern` - Teach system a new pattern

### Dependencies
```
# Backend
pdfplumber==0.11.4      # PDF parsing
pymupdf==1.25.1         # PDF fallback
thefuzz==0.22.1         # Fuzzy string matching
python-levenshtein==0.26.1  # Speed up fuzzy matching
scikit-learn==1.6.0     # Future ML categorization
```

### Adding New Bank Support
1. Create new adapter in `app/services/import_service.py`
2. Inherit from `BaseBankAdapter`
3. Implement `detect()` and `parse()` methods
4. Add to `ADAPTERS` registry

### Adding New Merchant Patterns
Edit `CategorizationService.MERCHANT_PATTERNS` in `app/services/categorization_service.py`:
```python
r"pattern|alias|synonym": ("EnglishCategory", "RussianCategory"),
```

## Common Issues

See SUMMARY.md for detailed troubleshooting.

### Quick Fixes
- Migration issues: `alembic stamp head`
- Missing columns: Manual ALTER TABLE
- Container conflicts: `docker-compose down && docker container prune -f`

## Notes for AI Assistants

- Always check existing code patterns before adding new features
- Backend uses async/await throughout
- Frontend uses functional components with hooks
- i18n keys should be added to both EN and RU files
- Tests should cover both success and error cases
- Docker builds must include all necessary files (check Dockerfile)
- GitHub Actions deploys automatically - no manual server updates needed

## Resources

- API Docs: `/docs` (Swagger UI)
- Repository: https://github.com/VNKorchagin/scrooge
- Summary: See SUMMARY.md
