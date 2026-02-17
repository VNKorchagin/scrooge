# Scrooge - Budget Tracker

A personal budget tracking application with FastAPI backend and React TypeScript frontend.

## Features

- Track income and expenses
- Automatic category creation
- Dashboard with statistics and charts
- Transaction history with filters
- CSV export
- JWT authentication
- Responsive design

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
git clone <repo-url>
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

5. Access the application at `http://localhost`

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

## API Documentation

When running locally, API docs are available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Main Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/auth/register` | POST | Register new user |
| `/api/v1/auth/login` | POST | Login and get token |
| `/api/v1/auth/me` | GET | Get current user |
| `/api/v1/categories` | GET | List/search categories |
| `/api/v1/categories` | POST | Create category |
| `/api/v1/transactions` | GET | List transactions |
| `/api/v1/transactions` | POST | Create transaction |
| `/api/v1/transactions/{id}` | DELETE | Delete transaction |
| `/api/v1/stats/dashboard` | GET | Get dashboard stats |
| `/api/v1/export/csv` | GET | Export transactions to CSV |

## Database Schema

### Users
- `id`: Primary key
- `username`: Unique username
- `hashed_password`: Bcrypt hashed password
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

## Future Features

- [ ] Bank statement import (PDF/CSV)
- [ ] AI-powered auto-categorization
- [ ] Telegram bot integration
- [ ] Spending predictions
- [ ] Budget goals
- [ ] Recurring transactions

## Security

- Passwords hashed with bcrypt
- JWT tokens for authentication
- CORS configured for production domain
- SQL injection prevention via SQLAlchemy ORM
- Ownership verification for all resources

## License

MIT
