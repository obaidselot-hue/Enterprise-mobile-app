from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from database import get_db
import models
import schemas
from security import get_current_user, require_roles

router = APIRouter(prefix="/masters", tags=["Masters Management"])

# --- Parties (Customers & Vendors) Endpoints ---
@router.get("/parties", response_model=List[schemas.PartyResponse], summary="List customers and vendors")
def list_parties(
    party_type: Optional[str] = Query(None, pattern="^(customer|vendor)$"),
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    query = db.query(models.Party).filter(models.Party.is_active == True)
    if party_type:
        query = query.filter(models.Party.party_type == party_type)
    if search:
        search_fmt = f"%{search}%"
        query = query.filter(
            or_(
                models.Party.name.ilike(search_fmt),
                models.Party.phone.ilike(search_fmt),
                models.Party.tax_identifier.ilike(search_fmt)
            )
        )
    return query.order_by(models.Party.name.asc()).all()

@router.post("/parties", response_model=schemas.PartyResponse, status_code=status.HTTP_201_CREATED, summary="Create a new Customer or Vendor")
def create_party(
    payload: schemas.PartyCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(["admin", "manager", "operator"]))
):
    party = models.Party(
        party_type=payload.party_type,
        name=payload.name,
        tax_identifier=payload.tax_identifier,
        phone=payload.phone,
        email=payload.email,
        billing_address=payload.billing_address,
        credit_limit=payload.credit_limit,
        current_balance=0.00,
        is_active=True
    )
    db.add(party)
    db.commit()
    db.refresh(party)
    return party

@router.get("/parties/{party_id}", response_model=schemas.PartyResponse)
def get_party(
    party_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    party = db.query(models.Party).filter(models.Party.id == party_id).first()
    if not party:
        raise HTTPException(status_code=404, detail="Party entity not found.")
    return party

# --- Products Master Endpoints ---
@router.get("/products", response_model=List[schemas.ProductResponse], summary="List products and stock")
def list_products(
    category: Optional[str] = None,
    search: Optional[str] = None,
    low_stock_only: bool = False,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    query = db.query(models.Product).filter(models.Product.is_active == True)
    if category:
        query = query.filter(models.Product.category == category)
    if low_stock_only:
        query = query.filter(models.Product.current_stock <= models.Product.reorder_level)
    if search:
        search_fmt = f"%{search}%"
        query = query.filter(
            or_(
                models.Product.name.ilike(search_fmt),
                models.Product.sku.ilike(search_fmt),
                models.Product.barcode.ilike(search_fmt)
            )
        )
    return query.order_by(models.Product.name.asc()).all()

@router.post("/products", response_model=schemas.ProductResponse, status_code=status.HTTP_201_CREATED, summary="Create a new Product")
def create_product(
    payload: schemas.ProductCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(["admin", "manager"]))
):
    # Check duplicate SKU
    existing = db.query(models.Product).filter(models.Product.sku == payload.sku).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"A product with SKU '{payload.sku}' already exists.")

    product = models.Product(
        sku=payload.sku,
        barcode=payload.barcode,
        name=payload.name,
        category=payload.category,
        unit_of_measure=payload.unit_of_measure,
        selling_price=payload.selling_price,
        cost_price=payload.cost_price,
        current_stock=payload.current_stock,
        reorder_level=payload.reorder_level,
        is_active=True
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product

@router.get("/products/{product_id}", response_model=schemas.ProductResponse)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")
    return product
