import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from decimal import Decimal
from database import SessionLocal
import models
import schemas
from routers import masters, transactions, registers, reports, dashboard

@pytest.fixture
def db_session():
    db = SessionLocal()
    yield db
    db.close()

@pytest.fixture
def admin_user(db_session):
    admin = db_session.query(models.User).filter(models.User.role == "admin").first()
    return admin

def test_masters_parties_and_products(db_session, admin_user):
    # 1. Fetch parties
    parties = masters.list_parties(party_type=None, search=None, db=db_session, current_user=admin_user)
    assert len(parties) >= 1

    # 2. Fetch products
    products = masters.list_products(category=None, search=None, low_stock_only=False, db=db_session, current_user=admin_user)
    assert len(products) >= 1

    # 3. Create a new product
    sku_name = f"TEST-SKU-{len(products) + 100}"
    new_prod = schemas.ProductCreate(
        sku=sku_name,
        barcode=None,
        name="Integration Test Sensor",
        category="Sensors",
        unit_of_measure="pcs",
        selling_price=Decimal("120.00"),
        cost_price=Decimal("60.00"),
        current_stock=Decimal("80.000"),
        reorder_level=Decimal("10.000")
    )
    created_prod = masters.create_product(new_prod, db=db_session, current_user=admin_user)
    assert created_prod.sku == sku_name
    assert created_prod.selling_price == Decimal("120.00")

def test_create_transaction_and_stock_deduction(db_session, admin_user):
    customer = db_session.query(models.Party).filter(models.Party.party_type == "customer").first()
    product = db_session.query(models.Product).filter(models.Product.current_stock > 10).first()
    initial_stock = product.current_stock

    tx_payload = schemas.TransactionCreate(
        transaction_type="sales_invoice",
        party_id=customer.id,
        payment_status="unpaid",
        notes="Automated integration test order",
        items=[
            schemas.TransactionItemCreate(
                product_id=product.id,
                quantity=Decimal("3.000"),
                unit_price=product.selling_price,
                tax_rate_percent=Decimal("10.00")
            )
        ]
    )

    created_tx = transactions.create_transaction(tx_payload, db=db_session, current_user=admin_user)
    assert created_tx.transaction_number.startswith("INV-")
    assert len(created_tx.items) == 1

    # Verify inventory was decremented
    db_session.refresh(product)
    assert product.current_stock == initial_stock - Decimal("3.000")

def test_dashboard_and_registers(db_session, admin_user):
    # Dashboard summary
    dash_data = dashboard.get_dashboard_summary(range_filter="this_month", db=db_session, current_user=admin_user)
    assert dash_data.kpis.total_revenue >= Decimal("0.00")
    assert len(dash_data.revenue_trend) == 7

    # Sales Register
    sales_reg = registers.get_sales_register(start_date=None, end_date=None, payment_status=None, db=db_session, current_user=admin_user)
    assert "entries" in sales_reg
    assert sales_reg["record_count"] >= 1

    # P&L Report
    pl = reports.get_pl_statement(start_date=None, end_date=None, db=db_session, current_user=admin_user)
    assert "gross_profit" in pl
    assert "gross_margin_percent" in pl
