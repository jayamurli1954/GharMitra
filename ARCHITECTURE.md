# GharMitra Architecture Overview

This document provides a technical overview of the GharMitra application, detailing the technology stack, structure, and key components of both the Backend and Frontend.

## 🏗️ High-Level Architecture

GharMitra follows a classic **Client-Server Architecture**:
*   **Frontend (Client)**: A React-based Single Page Application (SPA) running in the browser.
*   **Backend (Server)**: A FastAPI Python application exposing RESTful APIs.
*   **Database**: An embedded SQLite database managed via SQLAlchemy.

---

## 🐍 Backend Architecture

The backend is built for performance and modern standards using **Python 3.11+**.

### **Core Stack:**
*   **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (High-performance, easy to use).
*   **Server**: Uvicorn (ASGI server).
*   **Database**: SQLite (File-based `GharMitra.db`).
*   **ORM**: SQLAlchemy 2.0 (Async/Await support via `aiosqlite`).
*   **Validation**: Pydantic v2 (Data validation and serialization).

### **Key Modules:**
*   **Authentication**: OAuth2 with Password Flow (JWT Tokens). Uses `passlib` for bcrypt hashing.
*   **routers/**: A modular router design separating concerns (e.g., `auth`, `users`, `flats`, `accounting`).
*   **models/**: Database models defined using SQLAlchemy Declatative Base.
*   **schemas/**: Pydantic models for Request/Response validation.
*   **PDF Generation**: Uses `reportlab` and `weasyprint` for generating bills and reports.

### **Directory Structure:**
```
backend/
├── app/
│   ├── main.py            # Application Entry Point
│   ├── database.py        # Database Connection Logic
│   ├── models/            # Database Tables (SQLAlchemy)
│   ├── schemas/           # Pydantic Objects (API Inputs/Outputs)
│   ├── routes/            # API Endpoints (separated by feature)
│   ├── services/          # Business Logic
│   └── utils/             # Helper functions (Security, PDF, etc.)
├── requirements.txt       # Python Dependencies
└── GharMitra.db           # SQLite Database File
```

---

## ⚛️ Frontend Architecture

The frontend is a **React 18** application, uniquely designed to be compatible with **React Native** patterns (via `react-native-web`), allowing for potential future mobile apps sharing the same codebase.

### **Core Stack:**
*   **Library**: React 18.
*   **Build Tool**: Webpack 5.
*   **Routing**: React Router v6.
*   **Styling**: `react-native-web` (Allows using React Native's StyleSheet API on the web).
*   **HTTP Client**: Axios (For communicating with the backend API).

### **Key Features:**
*   **React Native Web**: This allows the app to validly use components like `<View>` and `<Text>` which are then compiled to HTML `<div>` and `<span>` tags. This creates a "Universal App" architecture.
*   **Webpack Configuration**: Custom configuration to alias `react-native` imports to `react-native-web`.
*   **Services**: Dedicated service files (e.g., `authService.js`, `api.js`) to handle API communication, keeping UI components clean.

### **Directory Structure:**
```
web/
├── public/
│   └── index.html         # HTML Entry Point
├── src/
│   ├── index.js           # React Entry Point
│   ├── App.js             # Main Component & Routing
│   ├── components/        # Reusable UI Components
│   ├── screens/           # Page Views (Dashboard, Members, etc.)
│   ├── services/          # API Communication Logic
│   └── utils/             # Helper functions
└── webpack.config.js      # Build Configuration
```

---

## 🔌 API Communication

*   **Protocol**: HTTP/1.1 (REST).
*   **Authentication**: Bearer Token (JWT) sent in the `Authorization` header.
*   **Data Format**: JSON.
*   **CORS**: Configured in FastAPI to allow requests from the Frontend origin.

---

## 🚀 Deployment Summary

*   **Backend**: Deployed as a Python process (e.g., on Railway) with a persistent volume for the SQLite DB.
*   **Frontend**: Built into static HTML/JS/CSS files (`npm run build`) and served by a static host (e.g., Netlify).
