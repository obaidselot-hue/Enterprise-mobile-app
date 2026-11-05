from typing import Optional
from datetime import date, datetime, timedelta
from decimal import Decimal
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db
import models
from security import get_current_user, require_roles

router = APIRouter(prefix="/reports", tags=["Reports & Analytics"])

@router.get("/pl-statement", summary="Profit & Loss Statement")
def get_pl_statement(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(["admin", "manager"]))
):
    sales_q = db.query(func.coalesce(func.sum(models.Transaction.subtotal), 0)).filter(
        models.Transaction.transaction_type == "sales_invoice",
        models.Transaction.payment_status != "cancelled"
    )
    purchases_q = db.query(func.coalesce(func.sum(models.Transaction.subtotal), 0)).filter(
        models.Transaction.transaction_type == "purchase_bill",
        models.Transaction.payment_status != "cancelled"
    )

    if start_date:
        sales_q = sales_q.filter(models.Transaction.transaction_date >= start_date)
        purchases_q = purchases_q.filter(models.Transaction.transaction_date >= start_date)
    if end_date:
        sales_q = sales_q.filter(models.Transaction.transaction_date <= end_date)
        purchases_q = purchases_q.filter(models.Transaction.transaction_date <= end_date)

    total_sales = float(sales_q.scalar() or 0.00)
    total_purchases = float(purchases_q.scalar() or 0.00)
    gross_profit = total_sales - total_purchases
    margin_percent = round((gross_profit / total_sales * 100), 2) if total_sales > 0 else 0.00

    return {
        "period": {
            "start_date": start_date.isoformat() if start_date else "All Time",
            "end_date": end_date.isoformat() if end_date else "Present"
        },
        "revenue": {
            "gross_sales": total_sales,
            "discounts": 0.00,
            "net_sales": total_sales
        },
        "cost_of_goods_sold": {
            "purchases": total_purchases
        },
        "gross_profit": gross_profit,
        "gross_margin_percent": margin_percent
    }

@router.get("/aging-analysis", summary="Accounts Receivable & Payable Aging Analysis")
def get_aging_analysis(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(["admin", "manager"]))
):
    today = date.today()
    unpaid_txs = db.query(models.Transaction).filter(
        models.Transaction.payment_status.in_(["unpaid", "partially_paid"])
    ).all()

    receivables_aging = {"current_0_30": 0.00, "overdue_31_60": 0.00, "overdue_60_plus": 0.00, "total": 0.00}
    payables_aging = {"current_0_30": 0.00, "overdue_31_60": 0.00, "overdue_60_plus": 0.00, "total": 0.00}

    for tx in unpaid_txs:
        age_days = (today - tx.transaction_date).days
        amount = float(tx.grand_total)

        bucket = "current_0_30" if age_days <= 30 else ("overdue_31_60" if age_days <= 60 else "overdue_60_plus")

        if tx.transaction_type == "sales_invoice":
            receivables_aging[bucket] += amount
            receivables_aging["total"] += amount
        elif tx.transaction_type == "purchase_bill":
            payables_aging[bucket] += amount
            payables_aging["total"] += amount

    return {
        "receivables_customers": receivables_aging,
        "payables_vendors": payables_aging
    }

@router.get("/tax-summary", summary="GST/VAT Tax Summary")
def get_tax_summary(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(["admin", "manager", "auditor"]))
):
    output_tax_q = db.query(func.coalesce(func.sum(models.Transaction.tax_total), 0)).filter(
        models.Transaction.transaction_type == "sales_invoice",
        models.Transaction.payment_status != "cancelled"
    )
    input_tax_q = db.query(func.coalesce(func.sum(models.Transaction.tax_total), 0)).filter(
        models.Transaction.transaction_type == "purchase_bill",
        models.Transaction.payment_status != "cancelled"
    )

    if start_date:
        output_tax_q = output_tax_q.filter(models.Transaction.transaction_date >= start_date)
        input_tax_q = input_tax_q.filter(models.Transaction.transaction_date >= start_date)
    if end_date:
        output_tax_q = output_tax_q.filter(models.Transaction.transaction_date <= end_date)
        input_tax_q = input_tax_q.filter(models.Transaction.transaction_date <= end_date)

    output_tax = float(output_tax_q.scalar() or 0.00)
    input_tax = float(input_tax_q.scalar() or 0.00)
    net_liability = output_tax - input_tax

    return {
        "output_tax_collected": output_tax,
        "input_tax_credit": input_tax,
        "net_tax_payable": max(0.00, net_liability),
        "tax_credit_carried_forward": max(0.00, -net_liability)
    }
