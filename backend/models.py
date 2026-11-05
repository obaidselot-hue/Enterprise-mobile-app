from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import (
    Column, BigInteger, Integer, String, Boolean, DateTime, Date,
    ForeignKey, Numeric, Text, JSON
)
from sqlalchemy.orm import relationship
from database import Base

# Multi-dialect primary key: BIGINT in MySQL, INTEGER in SQLite (for autoincrement)
PK_ID = BigInteger().with_variant(Integer, "sqlite")
FK_ID = BigInteger().with_variant(Integer, "sqlite")

class User(Base):
    __tablename__ = "users"

    id = Column(PK_ID, primary_key=True, autoincrement=True)
    phone_number = Column(String(20), unique=True, nullable=False, index=True)
    full_name = Column(String(100), nullable=True)
    email = Column(String(150), unique=True, nullable=True)
    role = Column(String(20), default="operator", nullable=False, index=True) # admin, manager, operator, auditor
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    transactions = relationship("Transaction", back_populates="creator")
    audit_logs = relationship("AuditLog", back_populates="user")


class OTPVerification(Base):
    __tablename__ = "otp_verifications"

    id = Column(PK_ID, primary_key=True, autoincrement=True)
    phone_number = Column(String(20), nullable=False, index=True)
    otp_hash = Column(String(64), nullable=False) # SHA-256 hash of the 6-digit code
    attempts_count = Column(Integer, default=0, nullable=False)
    max_attempts = Column(Integer, default=3, nullable=False)
    status = Column(String(20), default="pending", nullable=False, index=True) # pending, verified, expired, failed
    expires_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Party(Base):
    __tablename__ = "parties"

    id = Column(PK_ID, primary_key=True, autoincrement=True)
    party_type = Column(String(20), nullable=False, index=True) # 'customer' or 'vendor'
    name = Column(String(150), nullable=False, index=True)
    tax_identifier = Column(String(50), nullable=True) # GSTIN / VAT / EIN
    phone = Column(String(20), nullable=True)
    email = Column(String(150), nullable=True)
    billing_address = Column(Text, nullable=True)
    credit_limit = Column(Numeric(12, 2), default=0.00, nullable=False)
    current_balance = Column(Numeric(12, 2), default=0.00, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    transactions = relationship("Transaction", back_populates="party")


class Product(Base):
    __tablename__ = "products"

    id = Column(PK_ID, primary_key=True, autoincrement=True)
    sku = Column(String(50), unique=True, nullable=False, index=True)
    barcode = Column(String(64), unique=True, nullable=True)
    name = Column(String(150), nullable=False)
    category = Column(String(100), default="General", nullable=False, index=True)
    unit_of_measure = Column(String(20), default="pcs", nullable=False)
    selling_price = Column(Numeric(12, 2), default=0.00, nullable=False)
    cost_price = Column(Numeric(12, 2), default=0.00, nullable=False)
    current_stock = Column(Numeric(12, 3), default=0.000, nullable=False)
    reorder_level = Column(Numeric(12, 3), default=10.000, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    transaction_items = relationship("TransactionItem", back_populates="product")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(PK_ID, primary_key=True, autoincrement=True)
    transaction_number = Column(String(50), unique=True, nullable=False, index=True)
    transaction_type = Column(String(30), nullable=False, index=True) # sales_invoice, purchase_bill, payment_in, payment_out
    transaction_date = Column(Date, default=date.today, nullable=False, index=True)
    party_id = Column(FK_ID, ForeignKey("parties.id", ondelete="RESTRICT"), nullable=False)
    subtotal = Column(Numeric(14, 2), default=0.00, nullable=False)
    tax_total = Column(Numeric(14, 2), default=0.00, nullable=False)
    grand_total = Column(Numeric(14, 2), default=0.00, nullable=False)
    payment_status = Column(String(20), default="unpaid", nullable=False) # unpaid, partially_paid, paid, cancelled
    notes = Column(Text, nullable=True)
    created_by = Column(FK_ID, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    party = relationship("Party", back_populates="transactions")
    creator = relationship("User", back_populates="transactions")
    items = relationship("TransactionItem", back_populates="transaction", cascade="all, delete-orphan")


class TransactionItem(Base):
    __tablename__ = "transaction_items"

    id = Column(PK_ID, primary_key=True, autoincrement=True)
    transaction_id = Column(FK_ID, ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(FK_ID, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False)
    quantity = Column(Numeric(12, 3), nullable=False)
    unit_price = Column(Numeric(12, 2), nullable=False)
    tax_rate_percent = Column(Numeric(5, 2), default=0.00, nullable=False)
    line_total = Column(Numeric(14, 2), nullable=False)

    transaction = relationship("Transaction", back_populates="items")
    product = relationship("Product", back_populates="transaction_items")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(PK_ID, primary_key=True, autoincrement=True)
    user_id = Column(FK_ID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action_type = Column(String(50), nullable=False, index=True)
    entity_name = Column(String(50), nullable=False)
    entity_id = Column(BigInteger, nullable=True)
    ip_address = Column(String(45), nullable=True)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    user = relationship("User", back_populates="audit_logs")
