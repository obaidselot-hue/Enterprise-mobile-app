import flet as ft
from api_client import api_client

def create_reports_view(page: ft.Page):
    view_column = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)
    content_container = ft.Column()

    def refresh_reports():
        content_container.controls.clear()
        content_container.controls.append(ft.ProgressBar())
        if page:
            page.update()

        try:
            pl_data = api_client.get_pl_statement()
            aging_data = api_client.get_aging_analysis()
            tax_data = api_client.get_tax_summary()

            # 1. Profit & Loss Card
            gross_sales = pl_data.get("revenue", {}).get("net_sales", 0.0)
            cogs = pl_data.get("cost_of_goods_sold", {}).get("purchases", 0.0)
            gross_profit = pl_data.get("gross_profit", 0.0)
            margin = pl_data.get("gross_margin_percent", 0.0)

            pl_card = ft.Card(
                elevation=2,
                content=ft.Container(
                    padding=16,
                    content=ft.Column([
                        ft.Row([
                            ft.Text("Profit & Loss Summary", size=16, weight=ft.FontWeight.BOLD),
                            ft.Icon(ft.Icons.ACCOUNT_BALANCE, color=ft.Colors.INDIGO_600)
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Divider(height=10),
                        ft.Row([ft.Text("Total Sales Revenue:", size=13), ft.Text(f"${gross_sales:,.2f}", weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_800)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Row([ft.Text("Cost of Goods (Purchases):", size=13), ft.Text(f"-${cogs:,.2f}", weight=ft.FontWeight.BOLD, color=ft.Colors.RED_800)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Divider(height=10),
                        ft.Row([
                            ft.Column([ft.Text("Gross Profit", size=11, color=ft.Colors.GREY_700), ft.Text(f"${gross_profit:,.2f}", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900)]),
                            ft.Column([ft.Text("Gross Margin", size=11, color=ft.Colors.GREY_700), ft.Text(f"{margin}%", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.TEAL_800)]),
                        ], alignment=ft.MainAxisAlignment.SPACE_AROUND)
                    ])
                )
            )

            # 2. Aging Analysis Card
            rec = aging_data.get("receivables_customers", {})
            pay = aging_data.get("payables_vendors", {})

            aging_card = ft.Card(
                elevation=2,
                content=ft.Container(
                    padding=16,
                    content=ft.Column([
                        ft.Row([
                            ft.Text("Overdue Aging Analysis", size=16, weight=ft.FontWeight.BOLD),
                            ft.Icon(ft.Icons.TIMER, color=ft.Colors.ORANGE_800)
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Divider(height=10),
                        ft.Text("Receivables (Due from Customers):", size=13, weight=ft.FontWeight.W_500),
                        ft.Row([
                            ft.Text(f"0-30 Days: ${float(rec.get('current_0_30', 0)):,.0f}", size=11),
                            ft.Text(f"31-60 Days: ${float(rec.get('overdue_31_60', 0)):,.0f}", size=11, color=ft.Colors.ORANGE_900),
                            ft.Text(f"60+ Days: ${float(rec.get('overdue_60_plus', 0)):,.0f}", size=11, color=ft.Colors.RED_900, weight=ft.FontWeight.BOLD),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Divider(height=10),
                        ft.Text("Payables (Due to Suppliers):", size=13, weight=ft.FontWeight.W_500),
                        ft.Row([
                            ft.Text(f"0-30 Days: ${float(pay.get('current_0_30', 0)):,.0f}", size=11),
                            ft.Text(f"31-60 Days: ${float(pay.get('overdue_31_60', 0)):,.0f}", size=11, color=ft.Colors.ORANGE_900),
                            ft.Text(f"60+ Days: ${float(pay.get('overdue_60_plus', 0)):,.0f}", size=11, color=ft.Colors.RED_900, weight=ft.FontWeight.BOLD),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ])
                )
            )

            # 3. Tax Liability Card
            out_tax = tax_data.get("output_tax_collected", 0.0)
            in_tax = tax_data.get("input_tax_credit", 0.0)
            net_tax = tax_data.get("net_tax_payable", 0.0)

            tax_card = ft.Card(
                elevation=2,
                content=ft.Container(
                    padding=16,
                    content=ft.Column([
                        ft.Row([
                            ft.Text("Tax Liability Summary (GST/VAT)", size=16, weight=ft.FontWeight.BOLD),
                            ft.Icon(ft.Icons.RECEIPT_LONG, color=ft.Colors.BLUE_800)
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Divider(height=10),
                        ft.Row([ft.Text("Output Tax Collected (Sales):", size=13), ft.Text(f"${out_tax:,.2f}", weight=ft.FontWeight.BOLD)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Row([ft.Text("Input Tax Credit (Purchases):", size=13), ft.Text(f"-${in_tax:,.2f}", weight=ft.FontWeight.BOLD)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Divider(height=10),
                        ft.Row([
                            ft.Text("Net Tax Payable to Government:", size=14, weight=ft.FontWeight.BOLD),
                            ft.Text(f"${net_tax:,.2f}", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_800)
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                    ])
                )
            )

            content_container.controls.clear()
            content_container.controls.extend([
                pl_card,
                ft.Container(height=10),
                aging_card,
                ft.Container(height=10),
                tax_card,
                ft.Container(height=30)
            ])

        except Exception as ex:
            content_container.controls.clear()
            content_container.controls.append(ft.Text(f"Connect to API to load reports ({str(ex)})", color=ft.Colors.GREY_700))

        if page:
            page.update()

    view_column.controls.extend([
        ft.Container(
            padding=16,
            content=ft.Column([
                ft.Row([
                    ft.Text("Financial & Compliance Reports", size=20, weight=ft.FontWeight.BOLD),
                    ft.IconButton(ft.Icons.REFRESH, on_click=lambda _: refresh_reports())
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(height=10),
                content_container
            ])
        )
    ])

    refresh_reports()
    return view_column
