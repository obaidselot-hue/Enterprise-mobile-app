import flet as ft
from api_client import api_client

def create_masters_view(page: ft.Page):
    view_column = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)
    list_container = ft.Column()
    search_input = ft.TextField(
        hint_text="Search by name, SKU or Tax ID...",
        prefix_icon=ft.Icons.SEARCH,
        border_radius=ft.BorderRadius.all(8),
        height=44
    )
    current_subtab = "products" # "products" | "customers" | "vendors"

    def refresh_list():
        list_container.controls.clear()
        query = search_input.value.strip() if search_input.value else None

        try:
            if current_subtab == "products":
                products = api_client.get_products(search=query)
                if not products:
                    list_container.controls.append(ft.Text("No products found.", color=ft.Colors.GREY_600))
                for p in products:
                    stock = float(p.get("current_stock", 0))
                    reorder = float(p.get("reorder_level", 0))
                    is_low = stock <= reorder

                    status_chip = ft.Container(
                        content=ft.Text("LOW STOCK" if is_low else "IN STOCK", size=10, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                        bgcolor=ft.Colors.RED_600 if is_low else ft.Colors.GREEN_600,
                        padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                        border_radius=ft.BorderRadius.all(12)
                    )

                    card = ft.Card(
                        elevation=1,
                        content=ft.Container(
                            padding=12,
                            content=ft.Column([
                                ft.Row([
                                    ft.Text(p.get("name", ""), size=15, weight=ft.FontWeight.BOLD),
                                    status_chip
                                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                ft.Text(f"SKU: {p.get('sku')} • Category: {p.get('category')}", size=12, color=ft.Colors.GREY_700),
                                ft.Divider(height=10),
                                ft.Row([
                                    ft.Text(f"Selling Price: ${float(p.get('selling_price', 0)):,.2f}", weight=ft.FontWeight.W_500),
                                    ft.Text(f"Stock: {stock:,.1f} {p.get('unit_of_measure')}", weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_700),
                                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                            ])
                        )
                    )
                    list_container.controls.append(card)

            elif current_subtab in ["customers", "vendors"]:
                party_type = "customer" if current_subtab == "customers" else "vendor"
                parties = api_client.get_parties(party_type=party_type, search=query)
                if not parties:
                    list_container.controls.append(ft.Text(f"No {party_type}s found.", color=ft.Colors.GREY_600))
                for p in parties:
                    card = ft.Card(
                        elevation=1,
                        content=ft.Container(
                            padding=12,
                            content=ft.Column([
                                ft.Row([
                                    ft.Text(p.get("name", ""), size=15, weight=ft.FontWeight.BOLD),
                                    ft.Text(f"Balance: ${float(p.get('current_balance', 0)):,.2f}", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.ORANGE_900)
                                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                ft.Text(f"Tax ID: {p.get('tax_identifier') or 'N/A'} • Phone: {p.get('phone') or 'N/A'}", size=12, color=ft.Colors.GREY_700),
                                ft.Text(f"Email: {p.get('email') or 'N/A'}", size=12, color=ft.Colors.GREY_600),
                            ])
                        )
                    )
                    list_container.controls.append(card)

        except Exception as ex:
            list_container.controls.append(ft.Text(f"Connect to API to load masters ({str(ex)})", color=ft.Colors.GREY_700))

        if page:
            page.update()

    def set_subtab(name: str):
        nonlocal current_subtab
        current_subtab = name
        btn_prods.bgcolor = ft.Colors.INDIGO_600 if name == "products" else ft.Colors.GREY_200
        btn_prods.color = ft.Colors.WHITE if name == "products" else ft.Colors.BLACK
        btn_custs.bgcolor = ft.Colors.INDIGO_600 if name == "customers" else ft.Colors.GREY_200
        btn_custs.color = ft.Colors.WHITE if name == "customers" else ft.Colors.BLACK
        btn_vends.bgcolor = ft.Colors.INDIGO_600 if name == "vendors" else ft.Colors.GREY_200
        btn_vends.color = ft.Colors.WHITE if name == "vendors" else ft.Colors.BLACK
        refresh_list()

    def show_add_modal(e):
        if not page:
            return

        if current_subtab == "products":
            sku_fld = ft.TextField(label="SKU Code", hint_text="PRD-001")
            name_fld = ft.TextField(label="Product Name")
            price_fld = ft.TextField(label="Selling Price ($)", value="100.00")
            stock_fld = ft.TextField(label="Initial Stock", value="50")
            dlg = ft.AlertDialog(
                title=ft.Text("Add New Product"),
                content=ft.Column([sku_fld, name_fld, price_fld, stock_fld], tight=True),
                actions=[
                    ft.TextButton(content="Cancel", on_click=lambda _: page.pop_dialog()),
                    ft.FilledButton(content="Save", on_click=lambda _: save_product(sku_fld.value, name_fld.value, price_fld.value, stock_fld.value))
                ]
            )
            page.show_dialog(dlg)
        else:
            party_type = "customer" if current_subtab == "customers" else "vendor"
            name_fld = ft.TextField(label="Company / Contact Name")
            tax_fld = ft.TextField(label="Tax ID (GSTIN/EIN)")
            phone_fld = ft.TextField(label="Phone Number")
            dlg = ft.AlertDialog(
                title=ft.Text(f"Add New {party_type.title()}"),
                content=ft.Column([name_fld, tax_fld, phone_fld], tight=True),
                actions=[
                    ft.TextButton(content="Cancel", on_click=lambda _: page.pop_dialog()),
                    ft.FilledButton(content="Save", on_click=lambda _: save_party(party_type, name_fld.value, tax_fld.value, phone_fld.value))
                ]
            )
            page.show_dialog(dlg)

    def save_product(sku, name, price, stock):
        try:
            api_client.create_product({
                "sku": sku,
                "name": name,
                "selling_price": float(price),
                "current_stock": float(stock)
            })
            if page:
                page.pop_dialog()
            refresh_list()
        except Exception as ex:
            if page:
                page.pop_dialog()
            refresh_list()

    def save_party(p_type, name, tax, phone):
        try:
            api_client.create_party({
                "party_type": p_type,
                "name": name,
                "tax_identifier": tax,
                "phone": phone
            })
            if page:
                page.pop_dialog()
            refresh_list()
        except Exception as ex:
            if page:
                page.pop_dialog()
            refresh_list()

    btn_prods = ft.FilledButton(content="Products", bgcolor=ft.Colors.INDIGO_600, color=ft.Colors.WHITE, on_click=lambda _: set_subtab("products"))
    btn_custs = ft.FilledButton(content="Customers", bgcolor=ft.Colors.GREY_200, color=ft.Colors.BLACK, on_click=lambda _: set_subtab("customers"))
    btn_vends = ft.FilledButton(content="Vendors", bgcolor=ft.Colors.GREY_200, color=ft.Colors.BLACK, on_click=lambda _: set_subtab("vendors"))
    search_input.on_change = lambda _: refresh_list()

    view_column.controls.extend([
        ft.Container(
            padding=16,
            content=ft.Column([
                ft.Row([
                    ft.Text("Entity Masters", size=20, weight=ft.FontWeight.BOLD),
                    ft.FilledButton(content="Add New", icon=ft.Icons.ADD, bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE, on_click=show_add_modal)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([btn_prods, btn_custs, btn_vends], spacing=8),
                search_input,
                ft.Divider(height=10),
                list_container
            ])
        )
    ])

    refresh_list()
    return view_column
