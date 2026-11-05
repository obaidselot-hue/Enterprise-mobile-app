import flet as ft
from api_client import api_client

def create_transactions_view(page: ft.Page):
    view_column = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)
    list_container = ft.Column()

    def refresh_transactions():
        list_container.controls.clear()
        try:
            txs = api_client.get_transactions()
            if not txs:
                list_container.controls.append(ft.Text("No transactions recorded yet.", color=ft.Colors.GREY_600))
            for tx in txs:
                is_sales = tx.get("transaction_type") == "sales_invoice"
                is_paid = tx.get("payment_status") == "paid"

                type_badge = ft.Container(
                    content=ft.Text("SALES" if is_sales else "PURCHASE", size=10, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    bgcolor=ft.Colors.INDIGO_600 if is_sales else ft.Colors.TEAL_700,
                    padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                    border_radius=ft.BorderRadius.all(10)
                )

                status_badge = ft.Container(
                    content=ft.Text(tx.get("payment_status", "unpaid").upper(), size=10, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    bgcolor=ft.Colors.GREEN_700 if is_paid else ft.Colors.ORANGE_800,
                    padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                    border_radius=ft.BorderRadius.all(10)
                )

                card = ft.Card(
                    elevation=1,
                    content=ft.Container(
                        padding=12,
                        content=ft.Column([
                            ft.Row([
                                ft.Row([type_badge, ft.Text(tx.get("transaction_number", ""), weight=ft.FontWeight.BOLD)]),
                                status_badge
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Text(f"Party: {tx.get('party_name', 'Customer/Vendor')} • Date: {tx.get('transaction_date', '')}", size=12, color=ft.Colors.GREY_700),
                            ft.Divider(height=10),
                            ft.Row([
                                ft.Text(f"Subtotal: ${float(tx.get('subtotal', 0)):,.2f} (Tax: ${float(tx.get('tax_total', 0)):,.2f})", size=12, color=ft.Colors.GREY_600),
                                ft.Text(f"${float(tx.get('grand_total', 0)):,.2f}", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK87),
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                        ])
                    )
                )
                list_container.controls.append(card)
        except Exception as ex:
            list_container.controls.append(ft.Text(f"Connect to API to load transactions ({str(ex)})", color=ft.Colors.GREY_700))

        if page:
            page.update()

    def show_create_modal(e):
        if not page:
            return

        try:
            parties = api_client.get_parties()
            products = api_client.get_products()
        except Exception:
            parties, products = [], []

        if not parties or not products:
            err_dlg = ft.AlertDialog(
                title=ft.Text("Cannot Create Transaction"),
                content=ft.Text("Please ensure you have created at least one Customer/Vendor and one Product in Masters first."),
                actions=[ft.TextButton(content="OK", on_click=lambda _: page.pop_dialog())]
            )
            page.show_dialog(err_dlg)
            return

        tx_type_dd = ft.Dropdown(
            label="Transaction Type",
            value="sales_invoice",
            options=[
                ft.DropdownOption(key="sales_invoice", text="Sales Invoice"),
                ft.DropdownOption(key="purchase_bill", text="Purchase Bill"),
            ]
        )

        party_dd = ft.Dropdown(
            label="Select Party",
            value=str(parties[0]["id"]),
            options=[ft.DropdownOption(key=str(p["id"]), text=f"{p['name']} ({p['party_type'].title()})") for p in parties]
        )

        prod_dd = ft.Dropdown(
            label="Select Product",
            value=str(products[0]["id"]),
            options=[ft.DropdownOption(key=str(pr["id"]), text=f"{pr['name']} (${float(pr['selling_price']):,.2f})") for pr in products]
        )

        qty_fld = ft.TextField(label="Quantity", value="1.000", keyboard_type=ft.KeyboardType.NUMBER)
        tax_fld = ft.TextField(label="Tax Rate (%)", value="10.00", keyboard_type=ft.KeyboardType.NUMBER)
        status_dd = ft.Dropdown(
            label="Payment Status",
            value="paid",
            options=[
                ft.DropdownOption(key="paid", text="Paid (Immediate)"),
                ft.DropdownOption(key="unpaid", text="Unpaid (Credit)"),
            ]
        )
        error_msg = ft.Text(value="", color=ft.Colors.RED_700, size=12)

        def save_transaction(_):
            try:
                selected_prod_id = int(prod_dd.value)
                prod = next((p for p in products if p["id"] == selected_prod_id), None)
                unit_price = float(prod["selling_price"]) if prod else 100.0

                payload = {
                    "transaction_type": tx_type_dd.value,
                    "party_id": int(party_dd.value),
                    "payment_status": status_dd.value,
                    "notes": "Generated from Mobile App",
                    "items": [
                        {
                            "product_id": selected_prod_id,
                            "quantity": float(qty_fld.value),
                            "unit_price": unit_price,
                            "tax_rate_percent": float(tax_fld.value)
                        }
                    ]
                }
                api_client.create_transaction(payload)
                if page:
                    page.pop_dialog()
                refresh_transactions()
            except Exception as ex:
                error_msg.value = str(ex)
                if page:
                    page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("Create New Transaction"),
            content=ft.Column([
                tx_type_dd,
                party_dd,
                prod_dd,
                ft.Row([qty_fld, tax_fld]),
                status_dd,
                error_msg
            ], tight=True),
            actions=[
                ft.TextButton(content="Cancel", on_click=lambda _: page.pop_dialog()),
                ft.FilledButton(content="Submit & Save", bgcolor=ft.Colors.INDIGO_600, color=ft.Colors.WHITE, on_click=save_transaction)
            ]
        )
        page.show_dialog(dlg)

    view_column.controls.extend([
        ft.Container(
            padding=16,
            content=ft.Column([
                ft.Row([
                    ft.Text("Transactions", size=20, weight=ft.FontWeight.BOLD),
                    ft.FilledButton(content="New Transaction", icon=ft.Icons.ADD_SHOPPING_CART, bgcolor=ft.Colors.INDIGO_600, color=ft.Colors.WHITE, on_click=show_create_modal)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(height=10),
                list_container
            ])
        )
    ])

    refresh_transactions()
    return view_column
