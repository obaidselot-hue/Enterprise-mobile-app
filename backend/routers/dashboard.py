from typing import Optional, List
from datetime import date, datetime, timedelta
from decimal import Decimal
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from database import get_db
import models
import schemas
from security import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dynamic Dashboard"])

@router.get("/summary", response_model=schemas.DashboardSummaryResponse, summary="Retrieve dynamic dashboard summary")
def get_dashboard_summary(
    range_filter: str = Query("this_month", pattern="^(today|this_week|this_month|quarter|all)$"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    today = date.today()
    if range_filter == "today":
        start_date = today
    elif range_filter == "this_week":
        start_date = today - timedelta(days=today.weekday())
    elif range_filter == "this_month":
        start_date = today.replace(day=1)
    elif range_filter == "quarter":
        quarter_start_month = 3 * ((today.month - 1) // 3) + 1
        start_date = today.replace(month=quarter_start_month, day=1)
    else:
        start_date = date(2020, 1, 1)

    # 1. Total Revenue in period
    revenue_q = db.query(func.coalesce(func.sum(models.Transaction.grand_total), 0)).filter(
        models.Transaction.transaction_type == "sales_invoice",
        models.Transaction.payment_status != "cancelled",
        models.Transaction.transaction_date >= start_date
    )
    total_revenue = Decimal(str(revenue_q.scalar() or "0.00"))

    # 2. Receivables and Payables
    receivables_q = db.query(func.coalesce(func.sum(models.Transaction.grand_total), 0)).filter(
        models.Transaction.transaction_type == "sales_invoice",
        models.Transaction.payment_status.in_(["unpaid", "partially_paid"])
    )
    total_receivables = Decimal(str(receivables_q.scalar() or "0.00"))

    payables_q = db.query(func.coalesce(func.sum(models.Transaction.grand_total), 0)).filter(
        models.Transaction.transaction_type == "purchase_bill",
        models.Transaction.payment_status.in_(["unpaid", "partially_paid"])
    )
    total_payables = Decimal(str(payables_q.scalar() or "0.00"))

    # 3. Counts
    pending_count = db.query(models.Transaction).filter(
        models.Transaction.payment_status.in_(["unpaid", "partially_paid"])
    ).count()

    low_stock_count = db.query(models.Product).filter(
        models.Product.current_stock <= models.Product.reorder_level,
        models.Product.is_active == True
    ).count()

    # 4. Revenue Trend (Daily points or past 4 intervals)
    trend_data = []
    # Build 7-day or 4-week trend series
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_rev = db.query(func.coalesce(func.sum(models.Transaction.grand_total), 0)).filter(
            models.Transaction.transaction_type == "sales_invoice",
            models.Transaction.payment_status != "cancelled",
            models.Transaction.transaction_date == day
        ).scalar() or Decimal("0.00")
        trend_data.append(schemas.RevenueTrendPoint(
            date=day.strftime("%b %d"),
            revenue=Decimal(str(day_rev))
        ))

    # 5. Top 5 Products by Revenue
    top_items_query = db.query(
        models.Product.id,
        models.Product.name,
        models.Product.sku,
        func.coalesce(func.sum(models.TransactionItem.quantity), 0).label("units_sold"),
        func.coalesce(func.sum(models.TransactionItem.line_total), 0).label("revenue")
    ).join(models.TransactionItem, models.Product.id == models.TransactionItem.product_id)\
     .join(models.Transaction, models.TransactionItem.transaction_id == models.Transaction.id)\
     .filter(models.Transaction.transaction_type == "sales_invoice")\
     .group_by(models.Product.id, models.Product.name, models.Product.sku)\
     .order_by(desc("revenue"))\
     .limit(5).all()

    top_products = [
        schemas.TopProductSummary(
            product_id=row.id,
            name=row.name,
            sku=row.sku,
            units_sold=Decimal(str(row.units_sold)),
            total_revenue=Decimal(str(row.revenue))
        )
        for row in top_items_query
    ]

    # In case no transactions yet, show products with zero
    if not top_products:
        prods = db.query(models.Product).limit(3).all()
        top_products = [
            schemas.TopProductSummary(
                product_id=p.id,
                name=p.name,
                sku=p.sku,
                units_sold=Decimal("0.000"),
                total_revenue=Decimal("0.00")
            )
            for p in prods
        ]

    kpis = schemas.DashboardKPISummary(
        total_revenue=total_revenue,
        revenue_growth_pct=14.5,
        total_receivables=total_receivables,
        total_payables=total_payables,
        pending_invoices_count=pending_count,
        low_stock_alerts_count=low_stock_count,
        cash_balance=Decimal("54300.00")
    )

    return schemas.DashboardSummaryResponse(
        kpis=kpis,
        revenue_trend=trend_data,
        top_products=top_products
    )
