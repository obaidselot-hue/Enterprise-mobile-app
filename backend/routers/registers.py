from typing import List, Optional
from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
import models
from security import get_current_user

router = APIRouter(prefix="/registers", tags=["Registers (Journals & Audit Trails)"])

@router.get("/sales", summary="Sales Register (Chronological Invoices)")
def get_sales_register(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    payment_status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    query = db.query(models.Transaction).filter(models.Transaction.transaction_type == "sales_invoice")
    if start_date:
        query = query.filter(models.Transaction.transaction_date >= start_date)
    if end_date:
        query = query.filter(models.Transaction.transaction_date <= end_date)
    if payment_status:
        query = query.filter(models.Transaction.payment_status == payment_status)

    invoices = query.order_by(models.Transaction.transaction_date.desc(), models.Transaction.id.desc()).all()

    total_value = sum(tx.grand_total for tx in invoices) if invoices else Decimal("0.00")
    total_tax = sum(tx.tax_total for tx in invoices) if invoices else Decimal("0.00")

    entries = []
    for tx in invoices:
        entries.append({
            "id": tx.id,
            "invoice_number": tx.transaction_number,
            "date": tx.transaction_date.isoformat(),
            "customer_name": tx.party.name if tx.party else "Unknown",
            "customer_tax_id": tx.party.tax_identifier if tx.party else None,
            "subtotal": float(tx.subtotal),
            "tax_total": float(tx.tax_total),
            "grand_total": float(tx.grand_total),
            "payment_status": tx.payment_status,
            "created_by": tx.creator.full_name or tx.creator.phone_number if tx.creator else "System"
        })

    return {
        "record_count": len(entries),
        "total_revenue": float(total_value),
        "total_tax_collected": float(total_tax),
        "entries": entries
    }

@router.get("/purchases", summary="Purchase Register (Chronological Supplier Bills)")
def get_purchase_register(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    query = db.query(models.Transaction).filter(models.Transaction.transaction_type == "purchase_bill")
    if start_date:
        query = query.filter(models.Transaction.transaction_date >= start_date)
    if end_date:
        query = query.filter(models.Transaction.transaction_date <= end_date)

    bills = query.order_by(models.Transaction.transaction_date.desc(), models.Transaction.id.desc()).all()

    total_value = sum(tx.grand_total for tx in bills) if bills else Decimal("0.00")
    total_tax = sum(tx.tax_total for tx in bills) if bills else Decimal("0.00")

    entries = []
    for tx in bills:
        entries.append({
            "id": tx.id,
            "bill_number": tx.transaction_number,
            "date": tx.transaction_date.isoformat(),
            "vendor_name": tx.party.name if tx.party else "Unknown",
            "vendor_tax_id": tx.party.tax_identifier if tx.party else None,
            "subtotal": float(tx.subtotal),
            "tax_total": float(tx.tax_total),
            "grand_total": float(tx.grand_total),
            "payment_status": tx.payment_status,
            "created_by": tx.creator.full_name or tx.creator.phone_number if tx.creator else "System"
        })

    return {
        "record_count": len(entries),
        "total_purchase_amount": float(total_value),
        "total_input_tax": float(total_tax),
        "entries": entries
    }

@router.get("/stock", summary="Stock Movement Register")
def get_stock_register(
    product_id: Optional[int] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    query = db.query(models.TransactionItem).join(models.Transaction)
    if product_id:
        query = query.filter(models.TransactionItem.product_id == product_id)

    items = query.order_by(models.Transaction.transaction_date.desc(), models.TransactionItem.id.desc()).limit(limit).all()

    movements = []
    for item in items:
        tx = item.transaction
        direction = "OUT" if tx.transaction_type == "sales_invoice" else "IN"
        movements.append({
            "date": tx.transaction_date.isoformat(),
            "transaction_number": tx.transaction_number,
            "type": tx.transaction_type,
            "sku": item.product.sku if item.product else "-",
            "product_name": item.product.name if item.product else "Item",
            "direction": direction,
            "quantity": float(item.quantity),
            "unit_price": float(item.unit_price),
            "line_total": float(item.line_total)
        })

    return {"count": len(movements), "movements": movements}
