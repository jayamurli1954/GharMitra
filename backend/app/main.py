"""
FastAPI Main Application
GharMitra - Apartment Accounting & Management System
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

# Trigger reload - Schema update verified
from app.config import settings
from app.database import init_db, close_db

# Import routers (will create these)
# Triggering reload for schema update - Retry 2
from app.routes import (
    auth,
    users,
    transactions,
    flats,
    maintenance,
    accounting,
    reports,
    messages,
    resources,
    society,
    journal,
    settings as settings_router,
    roles,
    permissions,
    user_roles,
    expense_heads,
    admin_guidelines,
    meetings,
    member_onboarding,
    physical_documents,
    legal,
    templates,
    chart_of_accounts,
    pincode,
    dashboard,
    financial_year_enhanced,
    opening_balances,
    payments,
    payment_gateway,
    vendors,
    complaints,
    supplementary,
    move_governance,
    attachments,
    assets,
    database as db_mgmt,
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Suppress verbose logs from database libraries
# Set to WARNING to hide INFO and DEBUG messages during startup
logging.getLogger('aiosqlite').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy.pool').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy.dialects').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy').setLevel(logging.WARNING)  # Catch-all for all SQLAlchemy loggers


# Lifespan context manager for startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting GharMitra API...")
    await init_db()
    logger.info("GharMitra API started successfully")
    yield
    # Shutdown
    logger.info("Shutting down GharMitra API...")
    await close_db()
    logger.info("GharMitra API shut down successfully")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="Professional apartment accounting and management system API",
    version=settings.API_VERSION,
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# CORS middleware - Allow all origins for Vercel dynamic URLs
# Note: When allow_credentials=True, cannot use ["*"] - must specify origins
# For production, use settings.allowed_origins_list or allow all with credentials=False
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https://gharmitra.*\.vercel\.app|http://localhost:\d+",
    allow_origins=["https://gharmitra.vercel.app"], # Main production domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Health check endpoint
@app.get("/", tags=["Health"])
async def root():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.API_VERSION,
        "message": "GharMitra API is running"
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint - doesn't require DB to be up"""
    from sqlalchemy import text
    from app.database import engine, create_engine_instance
    
    # Ensure engine is initialized for health check
    if engine is None:
        try:
            create_engine_instance()
        except Exception as e:
            return {
                "status": "healthy",
                "database": f"initialization_failed: {str(e)[:50]}",
                "version": settings.API_VERSION
            }
    
    db_status = "unknown"
    if engine:
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            db_status = "connected"
        except Exception as e:
            db_status = f"disconnected: {str(e)[:50]}"
    else:
        db_status = "not_initialized"
    
    return {
        "status": "healthy",
        "database": db_status,
        "version": settings.API_VERSION
    }

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(transactions.router, prefix="/api/transactions", tags=["Transactions"])
app.include_router(flats.router, prefix="/api/flats", tags=["Flats"])
app.include_router(maintenance.router, prefix="/api/maintenance", tags=["Maintenance"])
app.include_router(accounting.router, prefix="/api/accounting", tags=["Accounting"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
app.include_router(messages.router, prefix="/api/messages", tags=["Messages"])
app.include_router(resources.router, prefix="/api/resources", tags=["Resources"])
app.include_router(templates.router, tags=["Templates"])
app.include_router(society.router, prefix="/api/society", tags=["Society"])
app.include_router(pincode.router, prefix="/api/pincode", tags=["PIN Code"])
app.include_router(journal.router, prefix="/api/journal", tags=["Journal"])
app.include_router(settings_router.router, prefix="/api/settings", tags=["Settings"])
app.include_router(expense_heads.router, prefix="/api/maintenance", tags=["Expense Heads"])
app.include_router(admin_guidelines.router, prefix="/api/admin-guidelines", tags=["Admin Guidelines"])
app.include_router(member_onboarding.router, prefix="/api/member-onboarding", tags=["Member Onboarding"])
app.include_router(meetings.router, prefix="/api", tags=["Meetings"])
app.include_router(roles.router, prefix="/api/roles", tags=["Roles"])
app.include_router(permissions.router, prefix="/api/permissions", tags=["Permissions"])
app.include_router(user_roles.router, prefix="/api/user-roles", tags=["User Roles"])
app.include_router(vendors.router, prefix="/api/vendors", tags=["Vendors"]) # Added
app.include_router(physical_documents.router, tags=["Physical Documents"])
app.include_router(legal.router, prefix="/api/legal", tags=["Legal"])
app.include_router(chart_of_accounts.router, prefix="/api/chart-of-accounts", tags=["Chart of Accounts"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(financial_year_enhanced.router, prefix="/api", tags=["Financial Years"])
app.include_router(opening_balances.router, prefix="/api", tags=["Opening Balances"])
app.include_router(payments.router, prefix="/api", tags=["Payments"])
app.include_router(payment_gateway.router, prefix="/api", tags=["Payment Gateway"])
app.include_router(complaints.router, prefix="/api/complaints", tags=["Complaints"])
app.include_router(supplementary.router, prefix="/api/maintenance/supplementary", tags=["Supplementary Billing"])
app.include_router(move_governance.router, prefix="/api/move-governance", tags=["Move-In/Move-Out Governance"])
app.include_router(attachments.router, prefix="/api/attachments", tags=["Voucher Attachments"])
app.include_router(assets.router, prefix="/api/assets", tags=["Assets"])
app.include_router(db_mgmt.router, prefix="/api/database", tags=["Database Management"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
