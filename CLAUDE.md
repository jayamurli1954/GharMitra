# CLAUDE.md - AI Assistant Guide for GharKhata

This document provides a comprehensive guide for AI assistants working with the GharKhata codebase. It covers architecture, conventions, patterns, and workflows to follow when making changes.

## Table of Contents
1. [Repository Overview](#repository-overview)
2. [Architecture & Tech Stack](#architecture--tech-stack)
3. [Project Structure](#project-structure)
4. [Development Setup](#development-setup)
5. [Code Conventions](#code-conventions)
6. [Backend Patterns](#backend-patterns)
7. [Frontend Patterns](#frontend-patterns)
8. [Authentication & Security](#authentication--security)
9. [Database Patterns](#database-patterns)
10. [Testing](#testing)
11. [Common Development Tasks](#common-development-tasks)
12. [Key Files Reference](#key-files-reference)
13. [Important Gotchas](#important-gotchas)

---

## Repository Overview

**GharKhata** is a comprehensive mobile application for apartment associations to manage:
- Accounting & financial transactions
- Monthly maintenance billing (two calculation methods)
- Professional accounting system with chart of accounts
- Financial reports (Balance Sheet, Income & Expenditure, etc.)
- Member management
- Messaging & announcements
- Complaints and move-in/out requests

### Key Characteristics
- **Multi-tenant**: Each society is isolated via `society_id`
- **Mobile-first**: React Native app (iOS & Android)
- **REST API**: FastAPI backend with SQLite database
- **Zero-config DB**: SQLite file-based, no server required
- **JWT Auth**: Token-based authentication with AsyncStorage
- **TypeScript**: Frontend is fully typed
- **Async/Await**: Both frontend and backend use async patterns

---

## Architecture & Tech Stack

### Frontend (Mobile App)
```
Technology Stack:
├── React Native 0.73.2      # Mobile framework
├── TypeScript 5.3.3         # Type safety
├── React Navigation 6.1.9   # Bottom tabs + stack navigation
├── Axios 1.13.2             # HTTP client with interceptors
├── Formik 2.4.5 + Yup       # Forms & validation
├── AsyncStorage             # Local persistence (tokens, user data)
├── Vector Icons             # Material & Ionicons
└── React Native Chart Kit   # Data visualization
```

### Backend (API Server)
```
Technology Stack:
├── FastAPI 0.109.0          # Web framework
├── Python 3.11+             # Language
├── SQLAlchemy 2.0.25        # Async ORM
├── SQLite + aiosqlite       # Database (file-based)
├── Pydantic 2.5.3           # Request/response validation
├── Python-jose              # JWT tokens
├── Passlib + Bcrypt         # Password hashing
├── Pytest + httpx           # Testing
├── ReportLab + WeasyPrint   # PDF generation
└── OpenPyXL                 # Excel export
```

### Architecture Diagram
```
┌─────────────────────────────────┐
│  React Native App (TypeScript)  │
│  - Screens (UI components)      │
│  - Services (API clients)       │
│  - Navigation (tabs + stacks)   │
│  - AsyncStorage (persistence)   │
└─────────────────────────────────┘
         ↕ HTTP/HTTPS (REST API)
┌─────────────────────────────────┐
│  FastAPI Backend (Python)       │
│  - Routes (API endpoints)       │
│  - Models (Pydantic schemas)    │
│  - Dependencies (auth, DB)      │
│  - Business logic               │
└─────────────────────────────────┘
         ↕ SQLAlchemy (async ORM)
┌─────────────────────────────────┐
│  SQLite Database                │
│  - File: gharkhata.db           │
│  - 9+ tables with relationships │
│  - Multi-tenant via society_id  │
└─────────────────────────────────┘
```

---

## Project Structure

### Frontend Structure
```
src/
├── screens/                    # UI screens organized by feature
│   ├── auth/                   # Login, Register, RegisterSociety
│   ├── dashboard/              # Main dashboard with overview
│   ├── accounting/             # Transaction screens, chart of accounts
│   ├── maintenance/            # Bills, flats, water expenses, fixed expenses
│   ├── messages/               # Chat rooms, messaging
│   ├── members/                # Member directory
│   ├── reports/                # Financial reports (P&L, Balance Sheet, etc.)
│   ├── resources/              # Resource center
│   ├── payments/               # Payment screens
│   ├── complaints/             # Complaint management
│   ├── move_in_out/            # Move in/out requests
│   ├── profile/                # User profile
│   └── settings/               # App settings
│
├── navigation/                 # Navigation configuration
│   ├── MainTabNavigator.tsx    # Bottom tabs (5 tabs)
│   ├── AccountingNavigator.tsx # Accounting stack
│   ├── MaintenanceNavigator.tsx# Maintenance billing stack
│   ├── MessagesNavigator.tsx   # Messaging stack
│   └── ReportsNavigator.tsx    # Reports stack
│
├── services/                   # API service layer (Axios clients)
│   ├── api.ts                  # Base Axios instance with interceptors
│   ├── authService.ts          # Login, register, logout
│   ├── transactionsService.ts  # Transaction CRUD
│   ├── accountingService.ts    # Chart of accounts
│   ├── maintenanceService.ts   # Billing & maintenance
│   ├── messagesService.ts      # Chat & messaging
│   ├── societyService.ts       # Society settings
│   └── [other services]
│
├── types/                      # TypeScript type definitions
│   ├── models.ts               # Business entity interfaces
│   └── navigation.ts           # Navigation param types
│
├── config/                     # Configuration
│   └── env.ts                  # API URL configuration (auto IP detection)
│
├── utils/                      # Utility functions
│   ├── financialReports.ts     # Report generation logic
│   ├── maintenanceCalculations.ts  # Billing calculations
│   ├── networkUtils.ts         # Network helpers
│   └── chartOfAccounts.ts      # Account code utilities
│
├── components/                 # Reusable components
│   └── UnderDevelopment.tsx    # Placeholder component
│
└── constants/                  # App constants
    └── featureIcons.ts         # Icon mappings for features
```

### Backend Structure
```
backend/
├── app/
│   ├── main.py                 # FastAPI app setup, CORS, router registration
│   ├── config.py               # Settings (Pydantic BaseSettings)
│   ├── database.py             # SQLAlchemy engine, session, lifespan events
│   ├── dependencies.py         # FastAPI dependencies (auth, DB)
│   ├── models_db.py            # SQLAlchemy ORM models (all tables)
│   │
│   ├── models/                 # Pydantic request/response schemas
│   │   ├── user.py             # User, UserCreate, UserResponse
│   │   ├── transaction.py      # Transaction schemas
│   │   ├── flat.py             # Flat schemas
│   │   ├── society.py          # Society schemas
│   │   ├── maintenance.py      # Billing schemas
│   │   └── [other models]
│   │
│   ├── routes/                 # API endpoints (one file per resource)
│   │   ├── auth.py             # POST /login, /register
│   │   ├── transactions.py     # CRUD for transactions
│   │   ├── flats.py            # CRUD for flats
│   │   ├── accounting.py       # Chart of accounts
│   │   ├── maintenance.py      # Billing, water expenses, fixed expenses
│   │   ├── reports.py          # Financial reports (P&L, Balance Sheet, etc.)
│   │   ├── messages.py         # Chat rooms & messages
│   │   ├── society.py          # Society settings
│   │   ├── users.py            # User management
│   │   ├── resources.py        # Resource center
│   │   └── journal.py          # Journal entries
│   │
│   └── utils/
│       └── security.py         # JWT encode/decode, password hashing
│
├── tests/                      # Pytest tests
│   ├── test_fixes_simple.py
│   ├── test_transactions_fixes.py
│   ├── test_water_vacancy_calculation.py
│   └── test_messages_fixes.py
│
├── requirements.txt            # Python dependencies
├── run.py                      # Development server launcher
├── .env.example                # Environment variables template
└── gharkhata.db                # SQLite database (created on first run)
```

### Other Important Directories
```
gharkhata/
├── scripts/                    # Automation scripts
│   ├── auto-configure-ip.js    # Auto-detect and configure IP for dev
│   ├── run-android-phone-only.js # Run on physical Android device only
│   ├── configure-phone-ip.js   # Configure IP for phone development
│   ├── get-ip.js               # Get local IP address
│   └── update-ip.js            # Update IP in env.ts
│
├── android/                    # Android native code
├── ios/                        # iOS native code
├── App.tsx                     # React Native root component
├── index.js                    # Entry point
├── package.json                # Frontend dependencies & scripts
├── tsconfig.json               # TypeScript config with path aliases
├── babel.config.js             # Babel config with module resolver
└── metro.config.js             # Metro bundler config
```

---

## Development Setup

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env and set SECRET_KEY
python run.py  # Starts on http://localhost:8000
```

### Frontend Setup
```bash
npm install
# For physical Android device development:
npm run android:phone
# For Android emulator:
npm run android:emulator
# For iOS:
npm run ios
```

### Starting Development
1. **Terminal 1 (Backend)**: `cd backend && python run.py`
2. **Terminal 2 (Frontend)**: `npm run android:phone` or `npm run ios`
3. **API Docs**: http://localhost:8000/docs (Swagger UI)

### Scripts & Commands
```json
// Frontend (package.json scripts)
"start": "react-native start"                          // Start Metro bundler
"start:network": "react-native start --host <IP>"      // Start with specific IP
"android:phone": "node scripts/run-android-phone-only.js"  // Physical device
"android:emulator": "react-native run-android"         // Emulator
"ios": "react-native run-ios"                          // iOS
"test": "jest"                                         // Run tests
"lint": "eslint ."                                     // Lint code
```

```bash
# Backend commands
python run.py              # Start development server (auto-reload)
pytest                     # Run all tests
pytest -v tests/test_transactions_fixes.py  # Run specific test
black .                    # Format code
flake8 .                   # Lint code
```

---

## Code Conventions

### Naming Conventions

#### Frontend (TypeScript)
| Item | Convention | Example |
|------|------------|---------|
| Files (Components) | PascalCase | `LoginScreen.tsx`, `DashboardScreen.tsx` |
| Files (Services) | camelCase + Service suffix | `authService.ts`, `transactionsService.ts` |
| Files (Utils) | camelCase | `financialReports.ts`, `networkUtils.ts` |
| Interfaces/Types | PascalCase | `User`, `Transaction`, `MaintenanceBill` |
| Functions | camelCase | `handleLogin`, `fetchTransactions` |
| Constants | UPPER_SNAKE_CASE | `API_URL`, `TOKEN_KEY` |
| React Components | PascalCase | `<LoginScreen />`, `<DashboardScreen />` |

#### Backend (Python)
| Item | Convention | Example |
|------|------------|---------|
| Files | snake_case | `models_db.py`, `security.py` |
| Classes | PascalCase | `User`, `Transaction`, `UserCreate` |
| Functions | snake_case | `get_current_user`, `create_transaction` |
| Variables | snake_case | `user_id`, `transaction_data` |
| Constants | UPPER_SNAKE_CASE | `SECRET_KEY`, `ALGORITHM` |
| API Routes | lowercase with hyphens | `/maintenance-bills`, `/chart-of-accounts` |

### Import Patterns

#### Frontend (TypeScript)
```typescript
// Use path aliases (defined in tsconfig.json)
import { authService } from '@services/authService';
import { Transaction, User } from '@types/models';
import { RootStackParamList } from '@types/navigation';
import { calculateMonthlyBill } from '@utils/maintenanceCalculations';

// React imports
import React, { useState, useEffect } from 'react';
import { View, Text, TouchableOpacity, Alert } from 'react-native';

// Third-party imports
import axios from 'axios';
import { Formik } from 'formik';
import * as Yup from 'yup';
```

#### Backend (Python)
```python
# Standard library
from datetime import datetime
from typing import List, Optional

# Third-party
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Local imports
from app.database import get_db
from app.dependencies import get_current_user, get_current_admin_user
from app.models_db import Transaction, User
from app.models.transaction import TransactionCreate, TransactionResponse
from app.utils.security import verify_password, create_access_token
```

### File Organization

#### Frontend Screen Component Template
```typescript
// src/screens/example/ExampleScreen.tsx
import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { exampleService } from '@services/exampleService';
import { ExampleData } from '@types/models';

const ExampleScreen = ({ navigation, route }: any) => {
  // State
  const [data, setData] = useState<ExampleData[]>([]);
  const [loading, setLoading] = useState(false);

  // Load data on mount
  useEffect(() => {
    loadData();
  }, []);

  // Handlers
  const loadData = async () => {
    setLoading(true);
    try {
      const response = await exampleService.getAll();
      setData(response.data);
    } catch (error: any) {
      Alert.alert('Error', error.message || 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const handleItemPress = (item: ExampleData) => {
    navigation.navigate('ExampleDetail', { id: item.id });
  };

  // Loading state
  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
      </View>
    );
  }

  // Main render
  return (
    <View style={styles.container}>
      {/* UI content */}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F5',
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
});

export default ExampleScreen;
```

#### Backend Route File Template
```python
# app/routes/example.py
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from app.dependencies import get_current_user, get_current_admin_user
from app.models_db import Example
from app.models.example import ExampleCreate, ExampleUpdate, ExampleResponse
from app.models.user import UserResponse

router = APIRouter()

@router.get("/", response_model=List[ExampleResponse])
async def list_examples(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all examples for current user's society"""
    query = select(Example).where(Example.society_id == current_user.society_id)
    result = await db.execute(query)
    examples = result.scalars().all()
    return [ExampleResponse.model_validate(ex) for ex in examples]

@router.post("/", response_model=ExampleResponse, status_code=status.HTTP_201_CREATED)
async def create_example(
    example_data: ExampleCreate,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Create new example (admin only)"""
    # Validation
    existing = await db.execute(
        select(Example).where(
            Example.name == example_data.name,
            Example.society_id == current_user.society_id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Example with this name already exists"
        )

    # Create
    new_example = Example(
        **example_data.model_dump(),
        society_id=current_user.society_id
    )
    db.add(new_example)
    await db.commit()
    await db.refresh(new_example)
    return ExampleResponse.model_validate(new_example)

@router.get("/{example_id}", response_model=ExampleResponse)
async def get_example(
    example_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get example by ID"""
    try:
        example_id_int = int(example_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid example ID format"
        )

    result = await db.execute(
        select(Example).where(
            Example.id == example_id_int,
            Example.society_id == current_user.society_id
        )
    )
    example = result.scalar_one_or_none()
    if not example:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Example not found"
        )
    return ExampleResponse.model_validate(example)

@router.put("/{example_id}", response_model=ExampleResponse)
async def update_example(
    example_id: str,
    example_data: ExampleUpdate,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Update example (admin only)"""
    # Get existing
    try:
        example_id_int = int(example_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid example ID format"
        )

    result = await db.execute(
        select(Example).where(
            Example.id == example_id_int,
            Example.society_id == current_user.society_id
        )
    )
    example = result.scalar_one_or_none()
    if not example:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Example not found"
        )

    # Update
    update_data = example_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(example, field, value)

    await db.commit()
    await db.refresh(example)
    return ExampleResponse.model_validate(example)

@router.delete("/{example_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_example(
    example_id: str,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete example (admin only)"""
    try:
        example_id_int = int(example_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid example ID format"
        )

    result = await db.execute(
        select(Example).where(
            Example.id == example_id_int,
            Example.society_id == current_user.society_id
        )
    )
    example = result.scalar_one_or_none()
    if not example:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Example not found"
        )

    await db.delete(example)
    await db.commit()
    return None
```

---

## Backend Patterns

### FastAPI Route Registration
```python
# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import (
    auth, transactions, flats, accounting,
    maintenance, reports, messages, society, users
)

app = FastAPI(title="GharKhata API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(transactions.router, prefix="/api/transactions", tags=["Transactions"])
app.include_router(flats.router, prefix="/api/flats", tags=["Flats"])
# ... more routers
```

### Dependency Injection Pattern
```python
# app/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models_db import User
from app.models.user import UserResponse
from app.utils.security import decode_access_token

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """Get current authenticated user from JWT token"""
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

    user_id = int(payload.get("sub"))
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    return UserResponse.model_validate(user)

async def get_current_admin_user(
    current_user: UserResponse = Depends(get_current_user)
) -> UserResponse:
    """Require admin or super_admin role"""
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user
```

### Pydantic Model Validation
```python
# app/models/transaction.py
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, Literal
from datetime import datetime

class TransactionCreate(BaseModel):
    type: Literal["income", "expense"]
    category: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=500)
    account_code: Optional[str] = Field(None, max_length=10)
    amount: Optional[float] = Field(None, gt=0)
    quantity: Optional[float] = Field(None, gt=0)
    unit_price: Optional[float] = Field(None, gt=0)
    date: datetime

    @field_validator('category')
    @classmethod
    def validate_category(cls, v):
        """Validate category is not empty"""
        if not v or not v.strip():
            raise ValueError('Category cannot be empty')
        return v.strip()

    @model_validator(mode='after')
    def validate_amount_calculation(self):
        """Validate amount is provided or calculated from quantity * unit_price"""
        if self.quantity is not None and self.unit_price is not None:
            self.amount = self.quantity * self.unit_price
        elif self.amount is None:
            raise ValueError('Either provide amount or both quantity and unit_price')
        return self

class TransactionResponse(BaseModel):
    id: int
    society_id: int
    type: str
    category: str
    description: str
    amount: float
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    account_code: Optional[str] = None
    date: datetime
    added_by: int
    created_at: datetime

    model_config = {"from_attributes": True}
```

### SQLAlchemy Async Patterns
```python
# Query examples
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload

# Simple select
result = await db.execute(select(User).where(User.id == user_id))
user = result.scalar_one_or_none()

# Select with filter
result = await db.execute(
    select(Transaction).where(
        Transaction.society_id == society_id,
        Transaction.type == "income"
    )
)
transactions = result.scalars().all()

# Select with join/relationship loading
result = await db.execute(
    select(MaintenanceBill).options(
        selectinload(MaintenanceBill.flat)
    ).where(MaintenanceBill.society_id == society_id)
)
bills = result.scalars().all()

# Insert
new_user = User(**user_data)
db.add(new_user)
await db.commit()
await db.refresh(new_user)

# Update
result = await db.execute(
    select(User).where(User.id == user_id)
)
user = result.scalar_one_or_none()
user.name = "New Name"
await db.commit()
await db.refresh(user)

# Delete
result = await db.execute(
    select(Transaction).where(Transaction.id == transaction_id)
)
transaction = result.scalar_one_or_none()
await db.delete(transaction)
await db.commit()
```

---

## Frontend Patterns

### Service Layer Pattern
```typescript
// src/services/exampleService.ts
import api from './api';
import { ExampleData, ExampleCreate } from '@types/models';

export const exampleService = {
  // GET /api/examples
  getAll: async () => {
    return api.get<ExampleData[]>('/examples');
  },

  // GET /api/examples/:id
  getById: async (id: string | number) => {
    return api.get<ExampleData>(`/examples/${id}`);
  },

  // POST /api/examples
  create: async (data: ExampleCreate) => {
    return api.post<ExampleData>('/examples', data);
  },

  // PUT /api/examples/:id
  update: async (id: string | number, data: Partial<ExampleCreate>) => {
    return api.put<ExampleData>(`/examples/${id}`, data);
  },

  // DELETE /api/examples/:id
  delete: async (id: string | number) => {
    return api.delete(`/examples/${id}`);
  },
};
```

### Axios Interceptor Setup
```typescript
// src/services/api.ts
import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { API_URL } from '@/config/env';

const api = axios.create({
  baseURL: API_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor: Add auth token
api.interceptors.request.use(
  async (config) => {
    const token = await AsyncStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor: Handle errors
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    // Network error
    if (error.code === 'ECONNREFUSED' || error.code === 'ECONNABORTED') {
      return Promise.reject({
        message: 'Cannot connect to server. Check:\n1. Backend is running\n2. WiFi connected\n3. IP address correct',
        code: 'CONNECTION_ERROR'
      });
    }

    // 401 Unauthorized - clear token and redirect to login
    if (error.response?.status === 401) {
      await AsyncStorage.removeItem('access_token');
      await AsyncStorage.removeItem('user');
      // Note: Actual navigation handled in App.tsx
    }

    return Promise.reject(error);
  }
);

export default api;
```

### React Navigation Setup
```typescript
// src/navigation/MainTabNavigator.tsx
import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import Icon from 'react-native-vector-icons/Ionicons';

// Import navigators
import DashboardScreen from '@screens/dashboard/DashboardScreen';
import AccountingNavigator from './AccountingNavigator';
import MaintenanceNavigator from './MaintenanceNavigator';
import MessagesNavigator from './MessagesNavigator';
import ProfileNavigator from './ProfileNavigator';

const Tab = createBottomTabNavigator();

const MainTabNavigator = () => {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        tabBarIcon: ({ focused, color, size }) => {
          let iconName;

          if (route.name === 'Dashboard') {
            iconName = focused ? 'home' : 'home-outline';
          } else if (route.name === 'Accounting') {
            iconName = focused ? 'wallet' : 'wallet-outline';
          } else if (route.name === 'Maintenance') {
            iconName = focused ? 'calculator' : 'calculator-outline';
          } else if (route.name === 'Messages') {
            iconName = focused ? 'chatbubbles' : 'chatbubbles-outline';
          } else if (route.name === 'Profile') {
            iconName = focused ? 'person' : 'person-outline';
          }

          return <Icon name={iconName} size={size} color={color} />;
        },
        tabBarActiveTintColor: '#007AFF',
        tabBarInactiveTintColor: 'gray',
      })}
    >
      <Tab.Screen name="Dashboard" component={DashboardScreen} />
      <Tab.Screen name="Accounting" component={AccountingNavigator} options={{ headerShown: false }} />
      <Tab.Screen name="Maintenance" component={MaintenanceNavigator} options={{ headerShown: false }} />
      <Tab.Screen name="Messages" component={MessagesNavigator} options={{ headerShown: false }} />
      <Tab.Screen name="Profile" component={ProfileNavigator} options={{ headerShown: false }} />
    </Tab.Navigator>
  );
};

export default MainTabNavigator;
```

### TypeScript Type Definitions
```typescript
// src/types/models.ts
export interface User {
  id: number;
  society_id: number;
  email: string;
  name: string;
  phone?: string;
  flat_id?: number;
  role: 'super_admin' | 'admin' | 'resident';
  created_at: string;
}

export interface Transaction {
  id: number;
  society_id: number;
  type: 'income' | 'expense';
  category: string;
  description: string;
  amount: number;
  quantity?: number;
  unit_price?: number;
  account_code?: string;
  date: string;
  added_by: number;
  created_at: string;
}

export interface Flat {
  id: number;
  society_id: number;
  flat_number: string;
  owner_name: string;
  owner_email?: string;
  owner_phone?: string;
  area_sqft: number;
  occupants: number;
  is_occupied: boolean;
  created_at: string;
}

// Request types
export interface TransactionCreate {
  type: 'income' | 'expense';
  category: string;
  description: string;
  amount?: number;
  quantity?: number;
  unit_price?: number;
  account_code?: string;
  date: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  name: string;
  phone?: string;
  society_id: number;
}

// Response types
export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}
```

---

## Authentication & Security

### Frontend Auth Flow
```typescript
// src/services/authService.ts
import api from './api';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { LoginCredentials, RegisterData, AuthResponse, User } from '@types/models';

export const authService = {
  // Login
  login: async (credentials: LoginCredentials): Promise<AuthResponse> => {
    const response = await api.post<AuthResponse>('/auth/login', credentials);
    const { access_token, user } = response.data;

    // Store token and user
    await AsyncStorage.setItem('access_token', access_token);
    await AsyncStorage.setItem('user', JSON.stringify(user));

    return response.data;
  },

  // Register
  register: async (data: RegisterData): Promise<AuthResponse> => {
    const response = await api.post<AuthResponse>('/auth/register', data);
    const { access_token, user } = response.data;

    // Store token and user
    await AsyncStorage.setItem('access_token', access_token);
    await AsyncStorage.setItem('user', JSON.stringify(user));

    return response.data;
  },

  // Logout
  logout: async (): Promise<void> => {
    await AsyncStorage.removeItem('access_token');
    await AsyncStorage.removeItem('user');
  },

  // Get current user from storage
  getCurrentUser: async (): Promise<User | null> => {
    const userJson = await AsyncStorage.getItem('user');
    return userJson ? JSON.parse(userJson) : null;
  },

  // Check if user is authenticated
  isAuthenticated: async (): Promise<boolean> => {
    const token = await AsyncStorage.getItem('access_token');
    return !!token;
  },
};
```

### Backend Auth Flow
```python
# app/routes/auth.py
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models_db import User
from app.models.user import UserCreate, UserResponse, LoginRequest
from app.utils.security import hash_password, verify_password, create_access_token

router = APIRouter()

@router.post("/register", response_model=dict)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """Register new user"""
    # Check if user exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create user
    hashed_password = hash_password(user_data.password)
    new_user = User(
        email=user_data.email,
        password_hash=hashed_password,
        name=user_data.name,
        phone=user_data.phone,
        society_id=user_data.society_id,
        role=user_data.role or "resident"
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    # Generate token
    access_token = create_access_token(data={"sub": str(new_user.id)})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse.model_validate(new_user)
    }

@router.post("/login", response_model=dict)
async def login(
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """Login user"""
    # Find user
    result = await db.execute(select(User).where(User.email == credentials.email))
    user = result.scalar_one_or_none()

    # Verify credentials
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    # Generate token
    access_token = create_access_token(data={"sub": str(user.id)})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse.model_validate(user)
    }
```

### JWT Token Utilities
```python
# app/utils/security.py
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    """Decode and validate JWT token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None
```

### Role-Based Access Control
```python
# In routes - restrict to admin only
@router.post("/")
async def create_item(
    data: ItemCreate,
    current_user: UserResponse = Depends(get_current_admin_user),  # Admin only
    db: AsyncSession = Depends(get_db)
):
    # Only admins can create
    pass

# In routes - any authenticated user
@router.get("/")
async def list_items(
    current_user: UserResponse = Depends(get_current_user),  # Any authenticated user
    db: AsyncSession = Depends(get_db)
):
    # Filter by user's society
    pass
```

---

## Database Patterns

### Multi-Tenancy Pattern
**CRITICAL**: All tables have `society_id` column for multi-tenancy isolation.

```python
# SQLAlchemy model
class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    society_id = Column(Integer, ForeignKey("societies.id"), default=1, index=True, nullable=False)
    # ... other fields

    # Relationship
    society = relationship("Society", back_populates="transactions")
```

**ALWAYS filter by society_id in queries:**
```python
# ✅ CORRECT - Filter by society
query = select(Transaction).where(
    Transaction.society_id == current_user.society_id
)

# ❌ WRONG - Missing society filter (security issue!)
query = select(Transaction)  # Returns all societies' data
```

### Database Model Relationships
```python
# app/models_db.py
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum

Base = declarative_base()

class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    RESIDENT = "resident"

class Society(Base):
    __tablename__ = "societies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    address = Column(String(500))
    total_flats = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    users = relationship("User", back_populates="society")
    flats = relationship("Flat", back_populates="society")
    transactions = relationship("Transaction", back_populates="society")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    society_id = Column(Integer, ForeignKey("societies.id"), default=1, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(100), nullable=False)
    phone = Column(String(20))
    flat_id = Column(Integer, ForeignKey("flats.id"))
    role = Column(Enum(UserRole), default=UserRole.RESIDENT, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    society = relationship("Society", back_populates="users")
    flat = relationship("Flat", foreign_keys=[flat_id])
    transactions = relationship("Transaction", back_populates="added_by_user")

class Flat(Base):
    __tablename__ = "flats"

    id = Column(Integer, primary_key=True, index=True)
    society_id = Column(Integer, ForeignKey("societies.id"), default=1, nullable=False)
    flat_number = Column(String(20), nullable=False)
    owner_name = Column(String(100), nullable=False)
    area_sqft = Column(Float, nullable=False)
    occupants = Column(Integer, default=0)
    is_occupied = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    society = relationship("Society", back_populates="flats")
    maintenance_bills = relationship("MaintenanceBill", back_populates="flat")
```

### Database Session Management
```python
# app/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True
)

# Session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Dependency for FastAPI
async def get_db() -> AsyncSession:
    """Database session dependency"""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()

# Lifespan events
async def init_db():
    """Initialize database on startup"""
    from app.models_db import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database initialized")

async def close_db():
    """Close database on shutdown"""
    await engine.dispose()
    logger.info("Database closed")
```

---

## Testing

### Backend Testing (Pytest)

#### Test Setup
```python
# backend/tests/conftest.py
import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.models_db import Base

# Test database (in-memory SQLite)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

@pytest.fixture(scope="function", autouse=True)
async def setup_db():
    """Setup and teardown test database for each test"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def db_session():
    """Get database session for tests"""
    async with TestSessionLocal() as session:
        yield session
```

#### Example Test
```python
# backend/tests/test_transactions.py
import pytest
from app.models_db import User, Society, Transaction
from datetime import datetime

@pytest.mark.asyncio
async def test_create_transaction(db_session):
    """Test creating a transaction"""
    # Create society
    society = Society(name="Test Society", total_flats=10)
    db_session.add(society)
    await db_session.commit()
    await db_session.refresh(society)

    # Create user
    user = User(
        email="test@example.com",
        password_hash="hashed",
        name="Test User",
        society_id=society.id
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Create transaction
    transaction = Transaction(
        society_id=society.id,
        type="income",
        category="Maintenance",
        description="Test transaction",
        amount=1000.0,
        date=datetime.utcnow(),
        added_by=user.id
    )
    db_session.add(transaction)
    await db_session.commit()
    await db_session.refresh(transaction)

    # Assertions
    assert transaction.id is not None
    assert transaction.society_id == society.id
    assert transaction.type == "income"
    assert transaction.amount == 1000.0

@pytest.mark.asyncio
async def test_multi_tenancy_isolation(db_session):
    """Test that transactions are isolated by society"""
    # Create two societies
    society1 = Society(name="Society 1", total_flats=10)
    society2 = Society(name="Society 2", total_flats=15)
    db_session.add_all([society1, society2])
    await db_session.commit()

    # Create users for each society
    user1 = User(email="user1@test.com", password_hash="hash", name="User 1", society_id=society1.id)
    user2 = User(email="user2@test.com", password_hash="hash", name="User 2", society_id=society2.id)
    db_session.add_all([user1, user2])
    await db_session.commit()

    # Create transactions for each society
    trans1 = Transaction(
        society_id=society1.id,
        type="income",
        category="Maintenance",
        description="Society 1 transaction",
        amount=1000.0,
        date=datetime.utcnow(),
        added_by=user1.id
    )
    trans2 = Transaction(
        society_id=society2.id,
        type="income",
        category="Maintenance",
        description="Society 2 transaction",
        amount=2000.0,
        date=datetime.utcnow(),
        added_by=user2.id
    )
    db_session.add_all([trans1, trans2])
    await db_session.commit()

    # Query transactions for society 1
    from sqlalchemy import select
    result = await db_session.execute(
        select(Transaction).where(Transaction.society_id == society1.id)
    )
    society1_transactions = result.scalars().all()

    # Assertions
    assert len(society1_transactions) == 1
    assert society1_transactions[0].amount == 1000.0
    assert society1_transactions[0].description == "Society 1 transaction"
```

### Running Tests
```bash
cd backend

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_transactions.py

# Run specific test
pytest tests/test_transactions.py::test_create_transaction

# Run with coverage
pytest --cov=app --cov-report=html
```

---

## Common Development Tasks

### Adding a New API Endpoint

**1. Define Pydantic Models**
```python
# backend/app/models/example.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ExampleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None

class ExampleCreate(ExampleBase):
    pass

class ExampleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None

class ExampleResponse(ExampleBase):
    id: int
    society_id: int
    created_at: datetime

    model_config = {"from_attributes": True}
```

**2. Create Database Model**
```python
# backend/app/models_db.py
class Example(Base):
    __tablename__ = "examples"

    id = Column(Integer, primary_key=True, index=True)
    society_id = Column(Integer, ForeignKey("societies.id"), default=1, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)

    society = relationship("Society")
```

**3. Create Route**
```python
# backend/app/routes/example.py
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from app.dependencies import get_current_user, get_current_admin_user
from app.models_db import Example
from app.models.example import ExampleCreate, ExampleUpdate, ExampleResponse
from app.models.user import UserResponse

router = APIRouter()

@router.get("/", response_model=List[ExampleResponse])
async def list_examples(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(Example).where(Example.society_id == current_user.society_id)
    result = await db.execute(query)
    examples = result.scalars().all()
    return [ExampleResponse.model_validate(ex) for ex in examples]

@router.post("/", response_model=ExampleResponse, status_code=status.HTTP_201_CREATED)
async def create_example(
    example_data: ExampleCreate,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    new_example = Example(
        **example_data.model_dump(),
        society_id=current_user.society_id
    )
    db.add(new_example)
    await db.commit()
    await db.refresh(new_example)
    return ExampleResponse.model_validate(new_example)
```

**4. Register Router**
```python
# backend/app/main.py
from app.routes import example

app.include_router(example.router, prefix="/api/examples", tags=["Examples"])
```

**5. Create Frontend Service**
```typescript
// src/services/exampleService.ts
import api from './api';
import { ExampleData, ExampleCreate } from '@types/models';

export const exampleService = {
  getAll: async () => {
    return api.get<ExampleData[]>('/examples');
  },

  create: async (data: ExampleCreate) => {
    return api.post<ExampleData>('/examples', data);
  },
};
```

**6. Create Frontend Screen**
```typescript
// src/screens/example/ExampleListScreen.tsx
import React, { useState, useEffect } from 'react';
import { View, Text, FlatList, TouchableOpacity } from 'react-native';
import { exampleService } from '@services/exampleService';

const ExampleListScreen = ({ navigation }: any) => {
  const [examples, setExamples] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadExamples();
  }, []);

  const loadExamples = async () => {
    setLoading(true);
    try {
      const response = await exampleService.getAll();
      setExamples(response.data);
    } catch (error) {
      Alert.alert('Error', 'Failed to load examples');
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={{ flex: 1 }}>
      <FlatList
        data={examples}
        renderItem={({ item }) => (
          <TouchableOpacity onPress={() => navigation.navigate('ExampleDetail', { id: item.id })}>
            <Text>{item.name}</Text>
          </TouchableOpacity>
        )}
        keyExtractor={(item) => item.id.toString()}
      />
    </View>
  );
};

export default ExampleListScreen;
```

### Adding IP Configuration

The project includes automation scripts for IP configuration:

```bash
# Auto-detect IP and configure
node scripts/auto-configure-ip.js

# Manually update IP in env.ts
node scripts/update-ip.js <your-ip-address>

# Get current IP
node scripts/get-ip.js
```

### Database Schema Changes

**IMPORTANT**: SQLite doesn't support all ALTER TABLE operations. For schema changes:

1. **Simple changes** (add nullable column):
```python
# In models_db.py
class User(Base):
    # Add new column
    new_field = Column(String(100))  # Nullable by default
```

2. **Complex changes** (add non-nullable, change types):
- Create migration script to recreate table
- Or manually in SQLite:
```sql
-- Rename old table
ALTER TABLE users RENAME TO users_old;

-- Create new table with updated schema
CREATE TABLE users (...);

-- Copy data
INSERT INTO users SELECT ... FROM users_old;

-- Drop old table
DROP TABLE users_old;
```

---

## Key Files Reference

| File | Purpose | When to Modify |
|------|---------|----------------|
| `/backend/app/main.py` | FastAPI app setup, router registration | Adding new routers, middleware |
| `/backend/app/config.py` | Configuration settings | Adding environment variables |
| `/backend/app/database.py` | Database connection, session management | Changing database URL, connection pooling |
| `/backend/app/dependencies.py` | FastAPI dependencies (auth, DB) | Adding new dependencies |
| `/backend/app/models_db.py` | SQLAlchemy ORM models | Adding/modifying database tables |
| `/backend/app/utils/security.py` | JWT, password hashing | Changing auth mechanism |
| `/backend/requirements.txt` | Python dependencies | Adding Python packages |
| `/src/config/env.ts` | API URL configuration | Changing backend URL, IP address |
| `/src/services/api.ts` | Axios instance, interceptors | Changing request/response handling |
| `/src/types/models.ts` | TypeScript interfaces | Adding new data types |
| `/src/navigation/MainTabNavigator.tsx` | Bottom tab navigation | Adding/removing tabs |
| `/package.json` | Frontend dependencies, scripts | Adding npm packages, scripts |
| `/tsconfig.json` | TypeScript config, path aliases | Adding path aliases |
| `/App.tsx` | Root component, auth flow | Changing app initialization |

---

## Important Gotchas

### 1. Multi-Tenancy is CRITICAL
**ALWAYS filter by `society_id`** in queries. Missing this filter is a security vulnerability.

```python
# ✅ CORRECT
query = select(Transaction).where(Transaction.society_id == current_user.society_id)

# ❌ WRONG - Returns data from all societies!
query = select(Transaction)
```

### 2. TypeScript Path Aliases
Use path aliases defined in `tsconfig.json`:
```typescript
// ✅ CORRECT
import { authService } from '@services/authService';

// ❌ WRONG - Relative paths
import { authService } from '../../../services/authService';
```

### 3. Async/Await Everywhere
Both frontend and backend use async patterns. Always `await` database operations:
```python
# ✅ CORRECT
result = await db.execute(query)
await db.commit()

# ❌ WRONG - Missing await
result = db.execute(query)  # Returns coroutine, not result
```

### 4. Error Handling in Frontend
Always handle both network errors and API errors:
```typescript
catch (error: any) {
  if (error.code === 'CONNECTION_ERROR') {
    // Network error
    Alert.alert('Connection Error', error.message);
  } else if (error.response?.status === 401) {
    // Unauthorized
    Alert.alert('Error', 'Please login again');
  } else if (error.response?.data?.detail) {
    // API error with detail
    Alert.alert('Error', error.response.data.detail);
  } else {
    // Generic error
    Alert.alert('Error', 'Something went wrong');
  }
}
```

### 5. SQLite Limitations
- No `ALTER TABLE` for most operations
- Integer IDs (no UUIDs)
- Limited concurrent writes
- File-based (backup = copy file)

### 6. React Native Platform Differences
```typescript
import { Platform } from 'react-native';

// iOS vs Android
const behavior = Platform.OS === 'ios' ? 'padding' : undefined;

// Network URLs
// iOS simulator: localhost or actual IP
// Android emulator: 10.0.2.2 or actual IP
// Physical device: Must use actual IP (192.168.x.x)
```

### 7. JWT Token Expiry
- Default: 30 days (`ACCESS_TOKEN_EXPIRE_MINUTES = 43200`)
- No refresh token mechanism (uses long-lived tokens)
- On 401, frontend clears token and redirects to login

### 8. Role-Based Access
- `super_admin`: Can create societies, access all features
- `admin`: Can manage society settings, generate bills, admin features
- `resident`: Can view own flat, bills, participate in messaging

### 9. Date Handling
```typescript
// Frontend - Always use ISO format
const date = new Date().toISOString();

// Backend - Python datetime
from datetime import datetime
date = datetime.utcnow()
```

### 10. Form Validation
- Frontend: Formik + Yup
- Backend: Pydantic validators
- **Always validate on both sides**

---

## Summary

### When Making Changes

1. **Backend Changes:**
   - Add/modify Pydantic models in `app/models/`
   - Add/modify SQLAlchemy models in `app/models_db.py`
   - Add/modify routes in `app/routes/`
   - Register router in `app/main.py`
   - **ALWAYS filter by `society_id`**
   - Use dependency injection for auth and DB
   - Test with pytest

2. **Frontend Changes:**
   - Add/modify TypeScript types in `src/types/models.ts`
   - Add/modify services in `src/services/`
   - Add/modify screens in `src/screens/`
   - Update navigation if needed
   - Use path aliases (`@services`, `@screens`, etc.)
   - Handle errors properly

3. **Full-Stack Feature:**
   - Define data model (Pydantic + SQLAlchemy)
   - Create API endpoints (FastAPI route)
   - Create service (Axios client)
   - Create UI screens (React Native)
   - Update navigation
   - Test end-to-end

### Best Practices
- ✅ Follow existing patterns and conventions
- ✅ Use TypeScript types for all frontend code
- ✅ Use Pydantic models for all backend requests/responses
- ✅ Always filter by `society_id` for multi-tenancy
- ✅ Use dependency injection for auth and database
- ✅ Handle errors gracefully on both frontend and backend
- ✅ Write tests for critical business logic
- ✅ Use path aliases in frontend imports
- ✅ Keep components focused (separation of concerns)
- ✅ Document complex logic with comments

### Common Mistakes to Avoid
- ❌ Missing `society_id` filter in queries (security issue!)
- ❌ Not awaiting async operations
- ❌ Using relative imports instead of path aliases
- ❌ Not handling network errors in frontend
- ❌ Not validating input on both frontend and backend
- ❌ Hardcoding values that should be in env/config
- ❌ Not testing multi-tenancy isolation
- ❌ Mixing platform-specific code without checking `Platform.OS`

---

## Additional Resources

- **API Documentation**: http://localhost:8000/docs (when backend is running)
- **React Native Docs**: https://reactnavigation.org/
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **SQLAlchemy Async**: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
- **TypeScript**: https://www.typescriptlang.org/docs/

---

**Last Updated**: December 2025

For questions or clarifications about this codebase, refer to this document first. If you're an AI assistant, follow these conventions strictly to maintain consistency across the codebase.
