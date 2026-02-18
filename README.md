# Scrooge - Budget Tracker

A personal budget tracking application with FastAPI backend and React TypeScript frontend.

## Features

- 💰 Track income and expenses
- 🏷️ Automatic category creation
- 📊 Dashboard with statistics and charts
- 📈 Transaction history with filters
- 📤 CSV export
- 🔐 JWT authentication
- 🌍 Multi-language support (English/Russian)
- 💱 Multi-currency support (USD/RUB) with exchange rates
- 👤 User account management (soft delete, admin panel)
- 📱 Responsive design
- 🧪 Automated testing

## Architecture

```
scrooge/
├── backend/           # FastAPI + SQLAlchemy + PostgreSQL
├── frontend/          # React + TypeScript + Vite + Tailwind
├── docker-compose.yml # Docker Compose configuration
└── nginx.conf         # Nginx reverse proxy config
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- (Optional) Node.js 18+ for local frontend development
- (Optional) Python 3.11+ for local backend development

### Production Deployment

1. Clone the repository:
```bash
git clone https://github.com/VNKorchagin/scrooge.git
cd scrooge
```

2. Copy and configure environment variables:
```bash
cp .env.example .env
# Edit .env with your secure values
```

3. Build and start services:
```bash
docker-compose up -d --build
```

4. Run database migrations:
```bash
docker-compose exec backend alembic upgrade head
```

5. (Optional) Create admin user:
```bash
docker-compose exec backend python -m app.cli create-admin admin your-password
```

6. (Optional) Create demo user with sample data:
```bash
docker-compose exec backend python -m app.cli create-demo
```

This creates a demo user (`demo` / `demo123`) with pre-populated transactions for testing.

7. Access the application at `http://localhost`

### HTTPS Setup (Production)

For HTTPS with Let's Encrypt:

1. Install Certbot:
```bash
# On Ubuntu/Debian
sudo apt-get install certbot
```

2. Obtain certificates:
```bash
sudo certbot certonly --standalone -d your-domain.com
```

3. Copy certificates to project:
```bash
sudo cp -r /etc/letsencrypt ./certbot-data
```

4. Update `nginx.conf` to enable HTTPS (see commented section in nginx.conf)

## Development

### Local Backend Development

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql+asyncpg://scrooge:password@localhost/scrooge_db"
export SECRET_KEY="dev-secret-key"

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Local Frontend Development

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at `http://localhost:5173`

### CLI Commands

The backend includes CLI commands for administrative tasks:

```bash
# Create admin user
python -m app.cli create-admin <username> <password>

# Create demo user with sample data (default: demo/demo123)
python -m app.cli create-demo [username] [password]

# List all users
python -m app.cli list-users

# Soft delete user
python -m app.cli delete-user <username>

# Hard delete user (permanent)
python -m app.cli delete-user <username> --hard

# Restore soft-deleted user
python -m app.cli restore-user <username>
```

## API Documentation

When running locally, API docs are available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Main Endpoints

#### Authentication
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/auth/register` | POST | Register new user |
| `/v1/auth/login` | POST | Login and get token |
| `/v1/auth/me` | GET | Get current user |
| `/v1/auth/me` | PATCH | Update user settings (language, currency) |
| `/v1/auth/me` | DELETE | Delete own account (soft delete) |

#### Categories
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/categories` | GET | List/search categories |
| `/v1/categories` | POST | Create category |

#### Transactions
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/transactions` | GET | List transactions |
| `/v1/transactions` | POST | Create transaction |
| `/v1/transactions/{id}` | DELETE | Delete transaction |

#### Statistics
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/stats/dashboard` | GET | Get dashboard stats |

#### Currency
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/currency/rate` | GET | Get exchange rate |
| `/v1/currency/convert` | POST | Preview currency conversion |
| `/v1/currency/apply` | POST | Apply currency change |

#### Export
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/export/csv` | GET | Export transactions to CSV |

#### Admin (Admin users only)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/users/admin/users` | GET | List all users |
| `/v1/users/admin/users/{id}` | GET | Get user details |
| `/v1/users/admin/users/{id}/restore` | POST | Restore deleted user |
| `/v1/users/admin/users/{id}` | DELETE | Delete user (soft/hard) |
| `/v1/users/admin/users/{id}/make-admin` | POST | Grant admin privileges |
| `/v1/users/admin/users/{id}/revoke-admin` | POST | Revoke admin privileges |

## Database Schema

### Users
- `id`: Primary key
- `username`: Unique username
- `hashed_password`: Bcrypt hashed password
- `language`: User language ('en' or 'ru')
- `currency`: User currency ('USD' or 'RUB')
- `is_active`: Soft delete flag
- `is_admin`: Admin privileges flag
- `deleted_at`: Deletion timestamp
- `created_at`: Timestamp

### Categories
- `id`: Primary key
- `user_id`: FK to users
- `name`: Category name (unique per user)
- `created_at`: Timestamp

### Transactions
- `id`: Primary key
- `user_id`: FK to users
- `type`: 'income' or 'expense'
- `amount`: Decimal amount
- `category_id`: FK to categories (nullable)
- `category_name`: Denormalized category name
- `description`: Optional description
- `raw_description`: For future AI import
- `transaction_date`: When transaction occurred
- `source`: 'manual', 'import_csv', 'import_pdf', 'telegram'
- `created_at`: Timestamp

### Predictions (Future)
- `id`: Primary key
- `user_id`: FK to users
- `predicted_date`: Predicted date
- `predicted_amount`: Predicted amount
- `confidence`: Prediction confidence
- `created_at`: Timestamp

## Multi-language Support

The application supports:
- 🇺🇸 English (en)
- 🇷🇺 Russian (ru)

Language can be changed in the settings modal (gear icon in the header).

## Multi-currency Support

The application supports:
- 💵 US Dollar (USD)
- 🇷🇺 Russian Ruble (RUB)

Features:
- Real-time exchange rates from Central Bank of Russia
- Currency conversion preview before applying
- All transactions recalculated when changing currency

## User Management

### Soft Delete
Users can delete their own accounts through the settings modal. This performs a soft delete:
- Account is marked as inactive
- User cannot log in anymore
- Data is preserved and can be restored by admin

### Admin Panel
Admin users can:
- View all users and their statistics
- Restore deleted users
- Permanently delete users (hard delete)
- Grant/revoke admin privileges

To create an admin user:
```bash
docker-compose exec backend python -m app.cli create-admin admin password123
```

## Testing

Run tests locally:
```bash
cd backend
source venv/bin/activate
pytest -v
```

### Test Coverage (43 tests)

#### Unit Tests
- **test_security.py** (8 tests): Password hashing, JWT tokens
- **test_currency_service.py** (11 tests): Currency conversion, validation

#### API Integration Tests
- **test_api_integration.py** (24 tests):
  - Authentication (register, login, settings)
  - Transactions (create, list, filters)
  - Categories (create, search)
  - Currency (rates, conversion)
  - Statistics (dashboard)
  - Validation errors

Tests are automatically run in GitHub Actions on every push.

## CI/CD

The project includes GitHub Actions workflows:
- **Tests**: Run on every push and PR
- **Deploy**: Automatic deployment to server on push to main branch

Configure GitHub Secrets:
- `SSH_PRIVATE_KEY`: SSH key for server access
- `SERVER_HOST`: Server IP or domain
- `SERVER_USER`: SSH username
- `DEPLOY_PATH`: Path to project on server
- `DB_PASSWORD`: Database password
- `SECRET_KEY`: JWT secret key

## Troubleshooting

### Database Migration Issues

**Problem:** `DuplicateTableError: relation "users" already exists`

Solution: Mark migrations as applied without running them:
```bash
docker-compose exec backend alembic stamp head
```

**Problem:** `UndefinedColumnError: column users.language does not exist`

Solution: Add missing columns manually:
```bash
docker-compose exec db psql -U scrooge -d scrooge_db -c "
ALTER TABLE users ADD COLUMN IF NOT EXISTS language VARCHAR(10) DEFAULT 'en';
ALTER TABLE users ADD COLUMN IF NOT EXISTS currency VARCHAR(10) DEFAULT 'USD';
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT true;
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT false;
ALTER TABLE users ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP;
"
```

### Container Conflicts

**Problem:** `Cannot create container for service db: Conflict. The container name "/scrooge_db_1" is already in use`

Solution: Remove old containers and rebuild:
```bash
docker-compose down
docker container prune -f
docker-compose up -d --build
```

### Alembic Configuration Not Found

**Problem:** `No config file 'alembic.ini' found`

Solution: Ensure Dockerfile copies alembic files:
```dockerfile
COPY alembic.ini .
COPY alembic/ ./alembic/
```

Then rebuild:
```bash
docker-compose up -d --build
```

## Future Features

- [ ] Bank statement import (PDF/CSV)
- [ ] AI-powered auto-categorization
- [ ] Telegram bot integration
- [ ] Spending predictions
- [ ] Budget goals
- [ ] Recurring transactions

## Security

- Passwords hashed with bcrypt (72-byte limit handling)
- JWT tokens for authentication
- CORS configured for production domain
- SQL injection prevention via SQLAlchemy ORM
- Ownership verification for all resources
- Soft delete for data protection
- Admin privileges for sensitive operations

## License

MIT
