from typing import List, Optional
from decimal import Decimal
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from database import get_db
import models
import schemas
from security import get_current_user, require_roles

router = APIRouter(prefix="/transactions", tags=["Transactions Management"])

def generate_transaction_number(tx_type: str, count: int) -> str:
    prefix = "INV" if tx_type == "sales_invoice" else ("PUR" if tx_type == "purchase_bill" else "PAY")
    year = datetime.utcnow().year
    return f"{prefix}-{year}-{count + 1:04d}"

@router.get("", response_model=List[schemas.TransactionResponse], summary="List transactions")
def list_transactions(
    transaction_type: Optional[str] = None,
    payment_status: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    query = db.query(models.Transaction)
    if transaction_type:
        query = query.filter(models.Transaction.transaction_type == transaction_type)
    if payment_status:
        query = query.filter(models.Transaction.payment_status == payment_status)
    
    txs = query.order_by(models.Transaction.created_at.desc()).limit(limit).all()
    
    # Enrich with party names
    results = []
    for tx in txs:
        resp = schemas.TransactionResponse.model_validate(tx)
        resp.party_name = tx.party.name if tx.party else "Unknown"
        results.append(resp)
    return results

@router.post("", response_model=schemas.TransactionDetailResponse, status_code=status.HTTP_201_CREATED, summary="Create a new transaction")
def create_transaction(
    payload: schemas.TransactionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(["admin", "manager", "operator"]))
):
    # Verify party exists
    party = db.query(models.Party).filter(models.Party.id == payload.party_id).first()
    if not party:
        raise HTTPException(status_code=400, detail="Specified Customer/Vendor does not exist.")

    total_count = db.query(models.Transaction).count()
    tx_num = generate_transaction_number(payload.transaction_type, total_count)

    subtotal = Decimal("0.00")
    tax_total = Decimal("0.00")
    items_to_create = []

    for item in payload.items:
        prod = db.query(models.Product).filter(models.Product.id == item.product_id).first()
        if not prod:
            raise HTTPException(status_code=400, detail=f"Product ID {item.product_id} does not exist.")

        # Business Rule: Check stock for sales
        if payload.transaction_type == "sales_invoice" and prod.current_stock < item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for '{prod.name}'. Available: {prod.current_stock}, Requested: {item.quantity}."
            )

        line_sub = (item.quantity * item.unit_price)
        line_tax = line_sub * (item.tax_rate_percent / Decimal("100.00"))
        line_total = line_sub + line_tax

        subtotal += line_sub
        tax_total += line_tax

        # Adjust stock
        if payload.transaction_type == "sales_invoice":
            prod.current_stock -= item.quantity
        elif payload.transaction_type == "purchase_bill":
            prod.current_stock += item.quantity

        items_to_create.append({
            "product_id": prod.id,
            "product_name": prod.name,
            "quantity": item.quantity,
            "unit_price": item.unit_price,
            "tax_rate_percent": item.tax_rate_percent,
            "line_total": line_total
        })

    grand_total = subtotal + tax_total

    # Create transaction header
    tx = models.Transaction(
        transaction_number=tx_num,
        transaction_type=payload.transaction_type,
        transaction_date=payload.transaction_date,
        party_id=payload.party_id,
        subtotal=subtotal,
        tax_total=tax_total,
        grand_total=grand_total,
        payment_status=payload.payment_status,
        notes=payload.notes,
        created_by=current_user.id
    )
    db.add(tx)
    db.flush()

    # Create line items
    for it in items_to_create:
        line_item = models.TransactionItem(
            transaction_id=tx.id,
            product_id=it["product_id"],
            quantity=it["quantity"],
            unit_price=it["unit_price"],
            tax_rate_percent=it["tax_rate_percent"],
            line_total=it["line_total"]
        )
        db.add(line_item)

    # Adjust party balance if invoice is unpaid
    if payload.payment_status != "paid":
        if payload.transaction_type == "sales_invoice":
            party.current_balance += grand_total
        elif payload.transaction_type == "purchase_bill":
            party.current_balance -= grand_total

    # Audit log
    audit = models.AuditLog(
        user_id=current_user.id,
        action_type="CREATE_TRANSACTION",
        entity_name="transactions",
        entity_id=tx.id,
        details={"number": tx_num, "type": payload.transaction_type, "total": str(grand_total)}
    )
    db.add(audit)

    db.commit()
    db.refresh(tx)

    # Build response
    resp = schemas.TransactionDetailResponse.model_validate(tx)
    resp.party_name = party.name
    resp.items = [
        schemas.TransactionItemResponse(
            id=item.id,
            product_id=item.product_id,
            product_name=item.product.name if item.product else "Item",
            quantity=item.quantity,
            unit_price=item.unit_price,
            tax_rate_percent=item.tax_rate_percent,
            line_total=item.line_total
        )
        for item in tx.items
    ]
    return resp

@router.get("/{tx_id}", response_model=schemas.TransactionDetailResponse)
def get_transaction_details(
    tx_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    tx = db.query(models.Transaction).filter(models.Transaction.id == tx_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found.")
    
    resp = schemas.TransactionDetailResponse.model_validate(tx)
    resp.party_name = tx.party.name if tx.party else "Unknown"
    resp.items = [
        schemas.TransactionItemResponse(
            id=item.id,
            product_id=item.product_id,
            product_name=item.product.name if item.product else "Item",
            quantity=item.quantity,
            unit_price=item.unit_price,
            tax_rate_percent=item.tax_rate_percent,
            line_total=item.line_total
        )
        for item in tx.items
    ]
    return resp
