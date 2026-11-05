import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import flet as ft
from api_client import api_client
from views.login_view import create_login_view
from views.dashboard_view import create_dashboard_view
from views.masters_view import create_masters_view
from views.transactions_view import create_transactions_view
from views.registers_view import create_registers_view
from views.reports_view import create_reports_view

def main(page: ft.Page):
    page.title = "Enterprise Mobile Application"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0

    def show_login_view():
        api_client.clear_tokens()
        page.views.clear()

        login_content = create_login_view(page, on_login_success=show_main_view)
        login_view = ft.View(
            route="/login",
            padding=0,
            controls=[
                ft.AppBar(
                    title=ft.Text("Secure Sign In", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    bgcolor=ft.Colors.INDIGO_600,
                    center_title=True,
                ),
                login_content
            ]
        )
        page.views.append(login_view)
        page.update()

    def show_main_view(user_profile: dict):
        page.views.clear()

        # Initialize view components
        dashboard_ctrl = create_dashboard_view(page)
        masters_ctrl = create_masters_view(page)
        transactions_ctrl = create_transactions_view(page)
        registers_ctrl = create_registers_view(page)
        reports_ctrl = create_reports_view(page)

        views_list = [
            dashboard_ctrl,
            masters_ctrl,
            transactions_ctrl,
            registers_ctrl,
            reports_ctrl
        ]

        active_content = ft.Container(content=dashboard_ctrl, expand=True)

        def handle_nav_change(e):
            idx = int(e.control.selected_index)
            active_content.content = views_list[idx]
            page.update()

        nav_bar = ft.NavigationBar(
            selected_index=0,
            on_change=handle_nav_change,
            indicator_color=ft.Colors.INDIGO_100,
            destinations=[
                ft.NavigationBarDestination(icon=ft.Icons.DASHBOARD_ROUNDED, label="Dashboard"),
                ft.NavigationBarDestination(icon=ft.Icons.STORAGE_ROUNDED, label="Masters"),
                ft.NavigationBarDestination(icon=ft.Icons.RECEIPT_LONG_ROUNDED, label="Transactions"),
                ft.NavigationBarDestination(icon=ft.Icons.MENU_BOOK_ROUNDED, label="Registers"),
                ft.NavigationBarDestination(icon=ft.Icons.INSERT_CHART_ROUNDED, label="Reports"),
            ]
        )

        user_role_label = user_profile.get("role", "operator").upper()
        user_phone = user_profile.get("phone_number", "")

        main_view = ft.View(
            route="/main",
            padding=0,
            navigation_bar=nav_bar,
            controls=[
                ft.AppBar(
                    leading=ft.Icon(ft.Icons.CORPORATE_FARE, color=ft.Colors.WHITE),
                    title=ft.Column([
                        ft.Text("Enterprise Portal", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                        ft.Text(f"{user_phone} • {user_role_label}", size=11, color=ft.Colors.INDIGO_100),
                    ], spacing=1),
                    bgcolor=ft.Colors.INDIGO_600,
                    actions=[
                        ft.IconButton(
                            icon=ft.Icons.LOGOUT,
                            tooltip="Sign Out",
                            icon_color=ft.Colors.WHITE,
                            on_click=lambda _: show_login_view()
                        )
                    ]
                ),
                active_content
            ]
        )
        page.views.append(main_view)
        page.update()

    # Launch into Login View
    show_login_view()

if __name__ == "__main__":
    if hasattr(ft, "run"):
        ft.run(main)
    elif hasattr(ft, "app"):
        ft.app(target=main)
