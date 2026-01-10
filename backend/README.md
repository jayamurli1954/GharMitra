# GharMitra Backend API

FastAPI backend for GharMitra apartment accounting application with SQLite.

## Tech Stack

- **FastAPI**: Modern, fast web framework for building APIs
- **SQLite**: Lightweight, embedded SQL database
- **SQLAlchemy**: SQL toolkit and async ORM for Python
- **PyJWT**: JSON Web Token authentication
- **Pydantic**: Data validation using Python type annotations
- **Uvicorn**: ASGI server for running FastAPI
- **Python 3.11+**: Latest Python features

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py               # Configuration and environment variables
│   ├── database.py             # SQLite connection with SQLAlchemy
│   ├── dependencies.py         # Common dependencies (auth, etc.)
│   │
│   ├── models/                 # Pydantic models (request/response)
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── transaction.py
│   │   ├── flat.py
│   │   ├── maintenance.py
│   │   ├── account_code.py
│   │   └── report.py
│   │
│   ├── models_db.py            # SQLAlchemy database models (tables)
│   │
│   ├── routes/                 # API endpoints
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── transactions.py
│   │   ├── flats.py
│   │   ├── maintenance.py
│   │   ├── accounting.py
│   │   ├── reports.py
│   │   ├── messages.py
│   │   └── members.py
│   │
│   ├── services/               # Business logic
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── billing_service.py
│   │   ├── accounting_service.py
│   │   ├── report_service.py
│   │   └── calculation_service.py
│   │
│   └── utils/                  # Utility functions
│       ├── __init__.py
│       ├── security.py         # Password hashing, JWT
│       ├── calculations.py     # Maintenance calculations
│       ├── validators.py       # Data validators
│       └── pdf_generator.py    # PDF report generation
│
├── tests/                      # Unit and integration tests
│   ├── __init__.py
│   ├── test_auth.py
│   ├── test_billing.py
│   └── test_reports.py
│
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
├── .gitignore
├── README.md
└── run.py                     # Development server runner
```

## Installation

### Prerequisites

- Python 3.11 or higher
- No external database needed (SQLite is embedded)
- pip and virtualenv

### Setup

1. **Clone the repository**
   ```bash
   cd backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run the application**
   ```bash
   python run.py
   ```

   Or with uvicorn directly:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## Environment Variables

```env
# Database
DATABASE_URL=sqlite+aiosqlite:///./gharmitra.db

# Security
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application
DEBUG=True
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:19006

# Optional
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - User login
- `POST /api/auth/refresh` - Refresh access token
- `GET /api/auth/me` - Get current user

### Users
- `GET /api/users` - List all users (admin)
- `GET /api/users/{id}` - Get user by ID
- `PUT /api/users/{id}` - Update user
- `DELETE /api/users/{id}` - Delete user (admin)

### Transactions
- `GET /api/transactions` - List transactions
- `POST /api/transactions` - Create transaction
- `GET /api/transactions/{id}` - Get transaction
- `PUT /api/transactions/{id}` - Update transaction
- `DELETE /api/transactions/{id}` - Delete transaction

### Flats
- `GET /api/flats` - List all flats
- `POST /api/flats` - Create flat
- `GET /api/flats/{id}` - Get flat details
- `PUT /api/flats/{id}` - Update flat
- `DELETE /api/flats/{id}` - Delete flat

### Maintenance Billing
- `GET /api/maintenance/settings` - Get apartment settings
- `PUT /api/maintenance/settings` - Update settings
- `POST /api/maintenance/water-expense` - Add water expense
- `GET /api/maintenance/water-expense/{month}` - Get water expense
- `POST /api/maintenance/generate-bills` - Generate bills for month
- `GET /api/maintenance/bills` - List bills
- `GET /api/maintenance/bills/{id}` - Get bill details
- `PUT /api/maintenance/bills/{id}/pay` - Mark bill as paid

### Accounting
- `GET /api/accounting/accounts` - Chart of accounts
- `POST /api/accounting/accounts` - Create account
- `PUT /api/accounting/accounts/{code}` - Update account
- `GET /api/accounting/balance` - Get account balances

### Financial Reports
- `POST /api/reports/receipts-payments` - Generate Receipts & Payments
- `POST /api/reports/income-expenditure` - Generate Income & Expenditure
- `POST /api/reports/balance-sheet` - Generate Balance Sheet
- `POST /api/reports/member-dues` - Generate Member Dues Report
- `POST /api/reports/member-ledger/{flatNumber}` - Member Ledger
- `GET /api/reports/export/{reportId}` - Export report as PDF

### Messages
- `GET /api/messages/rooms` - List chat rooms
- `POST /api/messages/rooms` - Create chat room
- `GET /api/messages/rooms/{id}/messages` - Get messages
- `POST /api/messages/rooms/{id}/messages` - Send message

## Database Schema

### Tables (SQLite + SQLAlchemy)

```sql
-- users
CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  name VARCHAR(255) NOT NULL,
  apartment_number VARCHAR(50),
  role VARCHAR(20) NOT NULL,  -- 'admin' or 'member'
  phone_number VARCHAR(20),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- flats
CREATE TABLE flats (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  flat_number VARCHAR(50) UNIQUE NOT NULL,
  area FLOAT NOT NULL,
  number_of_occupants INTEGER DEFAULT 1,
  owner_name VARCHAR(255) NOT NULL,
  owner_email VARCHAR(255),
  owner_phone VARCHAR(20),
  user_id INTEGER,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id)
);

-- transactions
CREATE TABLE transactions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  type VARCHAR(20) NOT NULL,  -- 'income' or 'expense'
  category VARCHAR(100) NOT NULL,
  account_code VARCHAR(50) NOT NULL,
  amount FLOAT NOT NULL,
  description TEXT,
  date TIMESTAMP NOT NULL,
  added_by INTEGER,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (added_by) REFERENCES users(id)
);

-- maintenance_bills
CREATE TABLE maintenance_bills (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  month VARCHAR(20) NOT NULL,
  year INTEGER NOT NULL,
  flat_id INTEGER NOT NULL,
  flat_number VARCHAR(50) NOT NULL,
  calculation_method VARCHAR(20) NOT NULL,  -- 'sqft_rate' or 'variable'
  area FLOAT,
  sqft_rate FLOAT,
  sqft_charges FLOAT,
  water_charges FLOAT,
  fixed_expenses FLOAT,
  sinking_fund FLOAT,
  total_amount FLOAT NOT NULL,
  status VARCHAR(20) DEFAULT 'generated',  -- 'generated', 'paid', 'overdue'
  generated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  paid_date TIMESTAMP,
  breakdown JSON,
  FOREIGN KEY (flat_id) REFERENCES flats(id)
);

-- account_codes
CREATE TABLE account_codes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  code VARCHAR(50) UNIQUE NOT NULL,
  name VARCHAR(255) NOT NULL,
  type VARCHAR(50) NOT NULL,  -- 'asset', 'liability', 'capital', 'income', 'expense'
  sub_type VARCHAR(100),
  description TEXT,
  is_active BOOLEAN DEFAULT TRUE,
  opening_balance FLOAT DEFAULT 0.0,
  current_balance FLOAT DEFAULT 0.0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Additional tables: apartment_settings, water_expenses, messages, chat_rooms
```

## Development

### Running Tests
```bash
pytest
```

### Code Formatting
```bash
black app/
```

### Linting
```bash
flake8 app/
```

## Deployment

See [DEPLOYMENT.md](./DEPLOYMENT.md) for deployment instructions for:
- Railway (Free tier)
- Render (Free tier)
- Fly.io (Free tier)
- DigitalOcean (Paid but affordable)

## Free Tier Hosting Options

1. **SQLite Database**
   - Embedded in the application
   - No separate database hosting needed
   - Perfect for small-medium associations

2. **Railway** (Backend hosting)
   - Free: $5 credit/month
   - Easy deployment

3. **Render** (Alternative)
   - Free tier available
   - Auto-deploy from Git

4. **Fly.io** (Alternative)
   - Free tier with limitations
   - Global deployment

## Documentation

- API Documentation: http://localhost:8000/docs (Swagger UI)
- Alternative docs: http://localhost:8000/redoc

## Security

- Password hashing with bcrypt
- JWT token authentication
- CORS protection
- Input validation with Pydantic
- SQL injection protection via SQLAlchemy ORM
- Rate limiting (coming soon)

## Contributing

1. Fork the repository
2. Create feature branch
3. Write tests
4. Submit pull request

## License

MIT License

## Support

For issues and questions, please open an issue on GitHub.
