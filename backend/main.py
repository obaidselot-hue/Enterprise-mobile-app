import logging
from datetime import date
from decimal import Decimal
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database import engine, Base, SessionLocal
import models
from routers import auth, masters, transactions, registers, reports, dashboard

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("uvicorn.info")

# Create tables
Base.metadata.create_all(bind=engine)

def seed_initial_data_if_empty():
    """Seeds baseline master data and demonstration entries if database is freshly initialized."""
    db = SessionLocal()
    try:
        # Check if users exist
        user_count = db.query(models.User).count()
        if user_count == 0:
            logger.info("Database is empty. Populating initial enterprise seed data...")
            # 1. Users
            u1 = models.User(phone_number="+14155552671", full_name="Admin Supervisor", role="admin", is_active=True)
            u2 = models.User(phone_number="+14155558888", full_name="Alex Morgan (Manager)", role="manager", is_active=True)
            u3 = models.User(phone_number="+14155559999", full_name="Sam Taylor (Operator)", role="operator", is_active=True)
            db.add_all([u1, u2, u3])
            db.flush()

            # 2. Parties
            p1 = models.Party(party_type="customer", name="Acme Industrial Solutions", tax_identifier="US-EIN-123456789", phone="+14155551001", email="accounts@acmeind.com", credit_limit=50000.00, current_balance=12450.00)
            p2 = models.Party(party_type="customer", name="Apex Logistics Corp", tax_identifier="US-EIN-987654321", phone="+14155551002", email="finance@apexlogistics.com", credit_limit=25000.00, current_balance=4800.00)
            p3 = models.Party(party_type="vendor", name="Pacific Tech Components", tax_identifier="US-EIN-444333222", phone="+14155552001", email="orders@pacifictech.com", credit_limit=0.00, current_balance=-8200.00)
            db.add_all([p1, p2, p3])
            db.flush()

            # 3. Products
            prod1 = models.Product(sku="PRD-SN-001", barcode="8901234567890", name="Industrial IoT Sensor Pro", category="Sensors", unit_of_measure="pcs", selling_price=145.00, cost_price=85.00, current_stock=45.000, reorder_level=10.000)
            prod2 = models.Product(sku="PRD-GW-002", barcode="8901234567891", name="Wireless Edge Gateway X2", category="Networking", unit_of_measure="pcs", selling_price=320.00, cost_price=195.00, current_stock=18.000, reorder_level=5.000)
            prod3 = models.Product(sku="PRD-CB-003", barcode="8901234567892", name="Shielded Fieldbus Cable 50m", category="Cabling", unit_of_measure="roll", selling_price=75.00, cost_price=42.00, current_stock=120.000, reorder_level=20.000)
            prod4 = models.Product(sku="PRD-PS-004", barcode="8901234567893", name="DIN-Rail Power Supply 24V", category="Power", unit_of_measure="pcs", selling_price=88.00, cost_price=52.00, current_stock=4.000, reorder_level=10.000)
            db.add_all([prod1, prod2, prod3, prod4])
            db.flush()

            # 4. Initial Invoices
            tx1 = models.Transaction(
                transaction_number="INV-2026-0001",
                transaction_type="sales_invoice",
                transaction_date=date.today(),
                party_id=p1.id,
                subtotal=Decimal("4350.00"),
                tax_total=Decimal("391.50"),
                grand_total=Decimal("4741.50"),
                payment_status="paid",
                notes="Automated seed invoice",
                created_by=u1.id
            )
            db.add(tx1)
            db.flush()

            it1 = models.TransactionItem(
                transaction_id=tx1.id,
                product_id=prod1.id,
                quantity=Decimal("30.000"),
                unit_price=Decimal("145.00"),
                tax_rate_percent=Decimal("9.00"),
                line_total=Decimal("4741.50")
            )
            db.add(it1)
            db.commit()
            logger.info("Initial seed data successfully committed.")
    except Exception as e:
        logger.warning(f"Seed data execution note: {e}")
        db.rollback()
    finally:
        db.close()

seed_initial_data_if_empty()

# Initialize FastAPI App
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Secure, Decoupled Mobile API Backend supporting OTP Authentication, Masters, Transactions, Registers, and Reports.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Policy
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Exception Handling Middleware
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

# Mount API Routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(masters.router, prefix="/api/v1")
app.include_router(transactions.router, prefix="/api/v1")
app.include_router(registers.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")

@app.get("/api/v1/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
