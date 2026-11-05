import re
from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict

# --- Authentication & OTP Schemas ---
class PhoneRequest(BaseModel):
    phone_number: str = Field(..., description="International phone number in E.164 format", examples=["+14155552671"])

    @field_validator("phone_number")
    def validate_e164(cls, v: str) -> str:
        cleaned = v.strip().replace(" ", "").replace("-", "")
        if not re.match(r"^\+[1-9]\d{9,14}$", cleaned):
            raise ValueError("Phone number must be a valid international E.164 format starting with '+' (e.g., +14155552671).")
        return cleaned

class OTPVerifyRequest(BaseModel):
    phone_number: str = Field(..., examples=["+14155552671"])
    otp_code: str = Field(..., min_length=6, max_length=6, description="6-digit verification code", examples=["123456"])

    @field_validator("otp_code")
    def validate_otp(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError("OTP code must consist of digits only.")
        return v

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class UserProfileResponse(BaseModel):
    id: int
    phone_number: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    role: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in_seconds: int
    user: UserProfileResponse

# --- Master Schemas (Parties / Customers / Vendors) ---
class PartyBase(BaseModel):
    party_type: str = Field(..., pattern="^(customer|vendor)$")
    name: str = Field(..., min_length=2, max_length=150)
    tax_identifier: Optional[str] = Field(None, max_length=50)
    phone: Optional[str] = None
    email: Optional[str] = None
    billing_address: Optional[str] = None
    credit_limit: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"))

class PartyCreate(PartyBase):
    pass

class PartyResponse(PartyBase):
    id: int
    current_balance: Decimal
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Master Schemas (Products) ---
class ProductBase(BaseModel):
    sku: str = Field(..., min_length=2, max_length=50)
    barcode: Optional[str] = Field(None, max_length=64)
    name: str = Field(..., min_length=2, max_length=150)
    category: str = Field(default="General", max_length=100)
    unit_of_measure: str = Field(default="pcs", max_length=20)
    selling_price: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"))
    cost_price: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"))
    current_stock: Decimal = Field(default=Decimal("0.000"))
    reorder_level: Decimal = Field(default=Decimal("10.000"), ge=Decimal("0.000"))

class ProductCreate(ProductBase):
    pass

class ProductResponse(ProductBase):
    id: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Transaction Schemas ---
class TransactionItemCreate(BaseModel):
    product_id: int
    quantity: Decimal = Field(..., gt=Decimal("0.000"))
    unit_price: Decimal = Field(..., ge=Decimal("0.00"))
    tax_rate_percent: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"))

class TransactionItemResponse(BaseModel):
    id: int
    product_id: int
    product_name: Optional[str] = None
    quantity: Decimal
    unit_price: Decimal
    tax_rate_percent: Decimal
    line_total: Decimal

    model_config = ConfigDict(from_attributes=True)

class TransactionCreate(BaseModel):
    transaction_type: str = Field(..., pattern="^(sales_invoice|purchase_bill|payment_in|payment_out)$")
    transaction_date: date = Field(default_factory=date.today)
    party_id: int
    payment_status: str = Field(default="unpaid", pattern="^(unpaid|partially_paid|paid|cancelled)$")
    notes: Optional[str] = None
    items: List[TransactionItemCreate] = Field(default_factory=list)

class TransactionResponse(BaseModel):
    id: int
    transaction_number: str
    transaction_type: str
    transaction_date: date
    party_id: int
    party_name: Optional[str] = None
    subtotal: Decimal
    tax_total: Decimal
    grand_total: Decimal
    payment_status: str
    notes: Optional[str] = None
    created_by: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class TransactionDetailResponse(TransactionResponse):
    items: List[TransactionItemResponse] = []

# --- Dashboard & Reports Schemas ---
class DashboardKPISummary(BaseModel):
    total_revenue: Decimal
    revenue_growth_pct: float
    total_receivables: Decimal
    total_payables: Decimal
    pending_invoices_count: int
    low_stock_alerts_count: int
    cash_balance: Decimal

class RevenueTrendPoint(BaseModel):
    date: str
    revenue: Decimal

class TopProductSummary(BaseModel):
    product_id: int
    name: str
    sku: str
    units_sold: Decimal
    total_revenue: Decimal

class DashboardSummaryResponse(BaseModel):
    kpis: DashboardKPISummary
    revenue_trend: List[RevenueTrendPoint]
    top_products: List[TopProductSummary]
