# 🏠 GharMitra - Housing Society Management
**SanMitra Tech Solutions Portfolio**

## Project Overview
GharMitra is a comprehensive housing society management platform for residential complexes and co-operative societies. It provides digital solutions for accounting, billing, member management, complaints, and more.

## Key Features
- **Dashboard:** Real-time overview of society finances and activities
- **Accounting:** Double-entry accounting with Chart of Accounts, Quick Entry, Journal Vouchers
- **Billing:** Automated maintenance bill generation with customizable rules
- **Member Management:** Track owners, tenants, and residents
- **Complaints:** Complaint tracking and resolution system
- **Reports:** Financial reports (Trial Balance, P&L, Balance Sheet, Ledger, Day Book)
- **Settings:** 14 comprehensive settings modules for complete configuration
- **Messages & Meetings:** Society communication and meeting management

## Technology Stack
- **Frontend:** React 18 with Webpack, React Router
- **Backend:** Python 3.11+ with FastAPI
- **Database:** SQLite (default), PostgreSQL/MySQL (optional)
- **Authentication:** JWT token-based authentication
- **Integrations:** Payment gateway (Razorpay/PayU), Email/SMS notifications

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18.x
- npm 8.x+

### Installation

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

**Frontend:**
```bash
cd web
npm install
npm run dev
```

Access the application at `http://localhost:3001`

For detailed installation, see [Installation Guide](./docs/GharMitra/INSTALLATION.md)

## Documentation

### Getting Started
- [Quick Start Guide](./docs/GharMitra/QUICK_START.md) - Get running in 5 minutes
- [Installation Guide](./docs/GharMitra/INSTALLATION.md) - Detailed setup instructions

### User Guides
- [User Manual](./docs/GharMitra/USER_MANUAL.md) - Complete user guide
- [Dashboard Guide](./docs/GharMitra/DASHBOARD_GUIDE.md) - Understanding the dashboard
- [Accounting Guide](./docs/GharMitra/ACCOUNTING_GUIDE.md) - Using accounting features
- [Settings Guide](./docs/GharMitra/SETTINGS_GUIDE.md) - Configuring society settings

### Developer Documentation
- [Developer Guide](./docs/GharMitra/DEVELOPER_GUIDE.md) - Development workflow
- [API Documentation](./docs/GharMitra/API_DOCUMENTATION.md) - Complete API reference
- [Backend README](./backend/README.md) - Backend-specific documentation

### Support
- [Troubleshooting Guide](./docs/GharMitra/TROUBLESHOOTING.md) - Common issues and solutions
- [FAQ](./docs/GharMitra/FAQ.md) - Frequently asked questions

**📚 [View All Documentation](./docs/GharMitra/README.md)**

## Integration with SanMitra Portfolio
- **MitraBooks:** Central accounting hub for financial integration
- **LegalMitra:** Legal compliance and society documentation
- **Shared Infrastructure:** User authentication, notifications, design system

## Project Structure

```
GharMitra/
├── backend/          # FastAPI backend
│   ├── app/         # Application code
│   ├── tests/       # Unit tests
│   └── README.md     # Backend documentation
├── web/             # React frontend
│   ├── src/         # Source code
│   ├── public/      # Static files
│   └── webpack.config.js
└── docs/            # Documentation
    └── GharMitra/   # Complete documentation
```

## Development Status
**Current Phase:** Development (Active)

**Completed:**
- ✅ User authentication (Login/Logout)
- ✅ Dashboard with metrics and quick actions
- ✅ Accounting module (Chart of Accounts, Quick Entry, Journal Voucher)
- ✅ Settings page with 14 sub-modules
- ✅ Profile management
- ✅ Splash screen with logo video
- ✅ Responsive UI with GharMitra branding

**In Progress:**
- 🔄 Maintenance bill generation
- 🔄 Member management
- 🔄 Complaints system
- 🔄 Reports generation
- 🔄 Messages and Meetings

**Planned:**
- 📋 Payment gateway integration
- 📋 Advanced reporting
- 📋 Document management
- 📋 Mobile app

## API Documentation

When backend is running, access interactive API docs:
- **Swagger UI:** `http://localhost:8001/docs`
- **ReDoc:** `http://localhost:8001/redoc`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

MIT License

## Support

- **Documentation:** [docs/GharMitra/](./docs/GharMitra/)
- **Troubleshooting:** [Troubleshooting Guide](./docs/GharMitra/TROUBLESHOOTING.md)
- **FAQ:** [FAQ](./docs/GharMitra/FAQ.md)

---

**Built with ❤️ by SanMitra Tech Solutions**
