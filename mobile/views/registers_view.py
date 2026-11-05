import flet as ft
from api_client import api_client

def create_registers_view(page: ft.Page):
    view_column = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)
    summary_banner = ft.Container()
    entries_container = ft.Column()
    current_reg = "sales" # "sales" | "purchases" | "stock"

    def refresh_register():
        entries_container.controls.clear()
        try:
            if current_reg == "sales":
                data = api_client.get_sales_register()
                total_rev = data.get("total_revenue", 0.0)
                total_tax = data.get("total_tax_collected", 0.0)

                summary_banner.content = ft.Card(
                    elevation=1,
                    color="#E8EAF6",
                    content=ft.Container(
                        padding=12,
                        content=ft.Row([
                            ft.Column([ft.Text("Total Sales Revenue", size=11, color=ft.Colors.GREY_700), ft.Text(f"${total_rev:,.2f}", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900)]),
                            ft.Column([ft.Text("Total Output Tax", size=11, color=ft.Colors.GREY_700), ft.Text(f"${total_tax:,.2f}", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_900)]),
                        ], alignment=ft.MainAxisAlignment.SPACE_AROUND)
                    )
                )

                for e in data.get("entries", []):
                    card = ft.Card(
                        elevation=1,
                        content=ft.Container(
                            padding=12,
                            content=ft.Column([
                                ft.Row([
                                    ft.Text(e.get("invoice_number"), weight=ft.FontWeight.BOLD),
                                    ft.Text(f"${float(e.get('grand_total', 0)):,.2f}", weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_800)
                                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                ft.Text(f"Customer: {e.get('customer_name')} • Date: {e.get('date')}", size=12, color=ft.Colors.GREY_700),
                                ft.Text(f"Tax: ${float(e.get('tax_total', 0)):,.2f} • Status: {e.get('payment_status').upper()} • Billed by: {e.get('created_by')}", size=11, color=ft.Colors.GREY_600),
                            ])
                        )
                    )
                    entries_container.controls.append(card)

            elif current_reg == "purchases":
                data = api_client.get_purchase_register()
                total_pur = data.get("total_purchase_amount", 0.0)
                total_in_tax = data.get("total_input_tax", 0.0)

                summary_banner.content = ft.Card(
                    elevation=1,
                    color="#E0F2F1",
                    content=ft.Container(
                        padding=12,
                        content=ft.Row([
                            ft.Column([ft.Text("Total Purchases", size=11, color=ft.Colors.GREY_700), ft.Text(f"${total_pur:,.2f}", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.TEAL_900)]),
                            ft.Column([ft.Text("Input Tax Credit", size=11, color=ft.Colors.GREY_700), ft.Text(f"${total_in_tax:,.2f}", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_900)]),
                        ], alignment=ft.MainAxisAlignment.SPACE_AROUND)
                    )
                )

                for e in data.get("entries", []):
                    card = ft.Card(
                        elevation=1,
                        content=ft.Container(
                            padding=12,
                            content=ft.Column([
                                ft.Row([
                                    ft.Text(e.get("bill_number"), weight=ft.FontWeight.BOLD),
                                    ft.Text(f"${float(e.get('grand_total', 0)):,.2f}", weight=ft.FontWeight.BOLD, color=ft.Colors.TEAL_800)
                                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                ft.Text(f"Vendor: {e.get('vendor_name')} • Date: {e.get('date')}", size=12, color=ft.Colors.GREY_700),
                                ft.Text(f"Tax: ${float(e.get('tax_total', 0)):,.2f} • Status: {e.get('payment_status').upper()}", size=11, color=ft.Colors.GREY_600),
                            ])
                        )
                    )
                    entries_container.controls.append(card)

            elif current_reg == "stock":
                data = api_client.get_stock_register()
                summary_banner.content = ft.Container()
                for m in data.get("movements", []):
                    is_out = m.get("direction") == "OUT"
                    badge = ft.Container(
                        content=ft.Text(f"{m.get('direction')} ({m.get('quantity')})", size=10, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                        bgcolor=ft.Colors.RED_700 if is_out else ft.Colors.GREEN_700,
                        padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                        border_radius=ft.BorderRadius.all(8)
                    )
                    card = ft.Card(
                        elevation=1,
                        content=ft.Container(
                            padding=12,
                            content=ft.Row([
                                ft.Column([
                                    ft.Text(m.get("product_name"), weight=ft.FontWeight.BOLD),
                                    ft.Text(f"Ref: {m.get('transaction_number')} • SKU: {m.get('sku')} • Date: {m.get('date')}", size=11, color=ft.Colors.GREY_600),
                                ]),
                                badge
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                        )
                    )
                    entries_container.controls.append(card)

        except Exception as ex:
            entries_container.controls.append(ft.Text(f"Connect to API to load registers ({str(ex)})", color=ft.Colors.GREY_700))

        if page:
            page.update()

    def set_reg(name: str):
        nonlocal current_reg
        current_reg = name
        btn_sales.bgcolor = ft.Colors.INDIGO_600 if name == "sales" else ft.Colors.GREY_200
        btn_sales.color = ft.Colors.WHITE if name == "sales" else ft.Colors.BLACK
        btn_pur.bgcolor = ft.Colors.INDIGO_600 if name == "purchases" else ft.Colors.GREY_200
        btn_pur.color = ft.Colors.WHITE if name == "purchases" else ft.Colors.BLACK
        btn_stock.bgcolor = ft.Colors.INDIGO_600 if name == "stock" else ft.Colors.GREY_200
        btn_stock.color = ft.Colors.WHITE if name == "stock" else ft.Colors.BLACK
        refresh_register()

    btn_sales = ft.FilledButton(content="Sales Register", bgcolor=ft.Colors.INDIGO_600, color=ft.Colors.WHITE, on_click=lambda _: set_reg("sales"))
    btn_pur = ft.FilledButton(content="Purchase Register", bgcolor=ft.Colors.GREY_200, color=ft.Colors.BLACK, on_click=lambda _: set_reg("purchases"))
    btn_stock = ft.FilledButton(content="Stock Movement", bgcolor=ft.Colors.GREY_200, color=ft.Colors.BLACK, on_click=lambda _: set_reg("stock"))

    view_column.controls.extend([
        ft.Container(
            padding=16,
            content=ft.Column([
                ft.Text("Operational Registers", size=20, weight=ft.FontWeight.BOLD),
                ft.Row([btn_sales, btn_pur, btn_stock], spacing=8),
                ft.Divider(height=6, color="transparent"),
                summary_banner,
                ft.Divider(height=6, color="transparent"),
                entries_container
            ])
        )
    ])

    refresh_register()
    return view_column
