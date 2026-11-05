import flet as ft
from api_client import api_client

def create_dashboard_view(page: ft.Page):
    content_area = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)

    def build_metric_card(title: str, value: str, subtext: str, icon, icon_color, bg_tint):
        return ft.Card(
            elevation=2,
            content=ft.Container(
                width=170,
                padding=14,
                bgcolor=bg_tint,
                border_radius=ft.BorderRadius.all(12),
                content=ft.Column([
                    ft.Row([
                        ft.Icon(icon, color=icon_color, size=28),
                        ft.Text(title, size=12, weight=ft.FontWeight.W_500, color=ft.Colors.GREY_800),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Container(height=4),
                    ft.Text(value, size=19, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK87),
                    ft.Text(subtext, size=11, color=ft.Colors.GREY_600),
                ])
            )
        )

    def load_dashboard_data(range_filter: str = "this_month"):
        content_area.controls.clear()
        content_area.controls.append(ft.ProgressBar())
        if page:
            page.update()

        try:
            summary = api_client.get_dashboard_summary(range_filter=range_filter)
            kpis = summary.get("kpis", {})
            trend = summary.get("revenue_trend", [])
            top_products = summary.get("top_products", [])

            # Filter row
            filter_dropdown = ft.Dropdown(
                label="Date Range",
                value=range_filter,
                width=160,
                options=[
                    ft.DropdownOption(key="today", text="Today"),
                    ft.DropdownOption(key="this_week", text="This Week"),
                    ft.DropdownOption(key="this_month", text="This Month"),
                    ft.DropdownOption(key="all", text="All Time"),
                ],
                on_change=lambda e: load_dashboard_data(e.control.value)
            )

            refresh_btn = ft.IconButton(
                icon=ft.Icons.REFRESH,
                tooltip="Refresh Data",
                on_click=lambda _: load_dashboard_data(filter_dropdown.value)
            )

            # Metrics cards
            cards_row_1 = ft.Row([
                build_metric_card(
                    "Total Revenue",
                    f"${float(kpis.get('total_revenue', 0)):,.2f}",
                    f"+{kpis.get('revenue_growth_pct', 0)}% vs last period",
                    ft.Icons.TRENDING_UP,
                    ft.Colors.GREEN_700,
                    "#E8F5E9"
                ),
                build_metric_card(
                    "Receivables",
                    f"${float(kpis.get('total_receivables', 0)):,.2f}",
                    f"{kpis.get('pending_invoices_count', 0)} pending invoices",
                    ft.Icons.SCHEDULE,
                    ft.Colors.ORANGE_800,
                    "#FFF3E0"
                ),
            ], alignment=ft.MainAxisAlignment.SPACE_EVENLY)

            cards_row_2 = ft.Row([
                build_metric_card(
                    "Low Stock",
                    str(kpis.get("low_stock_alerts_count", 0)),
                    "Items below reorder level",
                    ft.Icons.WARNING_AMBER_ROUNDED,
                    ft.Colors.RED_700,
                    "#FFEBEE"
                ),
                build_metric_card(
                    "Cash & Bank",
                    f"${float(kpis.get('cash_balance', 0)):,.2f}",
                    "Available liquid balance",
                    ft.Icons.ACCOUNT_BALANCE_WALLET,
                    ft.Colors.BLUE_800,
                    "#E3F2FD"
                ),
            ], alignment=ft.MainAxisAlignment.SPACE_EVENLY)

            # Revenue Trend Visualization (Bar items)
            max_val = max([float(t.get("revenue", 1)) for t in trend] + [1000.0])
            chart_bars = []
            for t in trend:
                val = float(t.get("revenue", 0))
                bar_height = max(10, int((val / max_val) * 120))
                chart_bars.append(
                    ft.Column([
                        ft.Text(f"${val:,.0f}", size=9, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_700),
                        ft.Container(
                            width=32,
                            height=bar_height,
                            bgcolor=ft.Colors.INDIGO_400 if val > 0 else ft.Colors.GREY_300,
                            border_radius=ft.BorderRadius.all(4),
                        ),
                        ft.Text(t.get("date", ""), size=10, color=ft.Colors.GREY_600),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                )

            trend_card = ft.Card(
                elevation=2,
                content=ft.Container(
                    padding=16,
                    content=ft.Column([
                        ft.Row([
                            ft.Text("Revenue Trend (Recent)", size=16, weight=ft.FontWeight.BOLD),
                            ft.Icon(ft.Icons.BAR_CHART, color=ft.Colors.INDIGO_600),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Divider(height=10),
                        ft.Container(
                            height=160,
                            padding=ft.Padding.symmetric(vertical=10),
                            content=ft.Row(
                                chart_bars,
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                scroll=ft.ScrollMode.ADAPTIVE
                            )
                        )
                    ])
                )
            )

            # Top Products List
            top_products_tiles = []
            for idx, p in enumerate(top_products[:4]):
                top_products_tiles.append(
                    ft.ListTile(
                        leading=ft.CircleAvatar(content=ft.Text(str(idx + 1)), bgcolor=ft.Colors.INDIGO_100, color=ft.Colors.INDIGO_900),
                        title=ft.Text(p.get("name", ""), weight=ft.FontWeight.W_500),
                        subtitle=ft.Text(f"SKU: {p.get('sku')} • {float(p.get('units_sold', 0)):,.0f} units sold"),
                        trailing=ft.Text(f"${float(p.get('total_revenue', 0)):,.2f}", weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_800)
                    )
                )

            top_products_card = ft.Card(
                elevation=2,
                content=ft.Container(
                    padding=16,
                    content=ft.Column([
                        ft.Row([
                            ft.Text("Top Selling Products", size=16, weight=ft.FontWeight.BOLD),
                            ft.Icon(ft.Icons.STAR_RATE, color=ft.Colors.AMBER_700),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Divider(height=10),
                        ft.Column(top_products_tiles if top_products_tiles else [ft.Text("No sales data available.", color=ft.Colors.GREY_500)])
                    ])
                )
            )

            # Rebuild content area
            content_area.controls.clear()
            content_area.controls.extend([
                ft.Container(
                    padding=16,
                    content=ft.Column([
                        ft.Row([
                            ft.Text("Operational Overview", size=20, weight=ft.FontWeight.BOLD),
                            ft.Row([filter_dropdown, refresh_btn]),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Divider(height=8, color="transparent"),
                        cards_row_1,
                        ft.Container(height=8),
                        cards_row_2,
                        ft.Container(height=16),
                        trend_card,
                        ft.Container(height=16),
                        top_products_card,
                        ft.Container(height=40),
                    ])
                )
            ])
        except Exception as ex:
            content_area.controls.clear()
            content_area.controls.append(
                ft.Container(
                    padding=20,
                    content=ft.Text(f"Notice: Start backend API to view live analytics ({str(ex)})", color=ft.Colors.GREY_700)
                )
            )

        if page:
            page.update()

    # Initial load
    load_dashboard_data("this_month")
    return content_area
