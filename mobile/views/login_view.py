import flet as ft
from api_client import api_client

def create_login_view(page: ft.Page, on_login_success):
    # Form elements
    phone_input = ft.TextField(
        label="Mobile Number (E.164)",
        value="+14155552671",
        prefix_icon=ft.Icons.PHONE_ANDROID,
        hint_text="+14155552671",
        keyboard_type=ft.KeyboardType.PHONE,
        border_radius=ft.BorderRadius.all(10),
        autofocus=True,
    )

    otp_input = ft.TextField(
        label="6-Digit OTP Code",
        prefix_icon=ft.Icons.PASSWORD,
        hint_text="123456",
        max_length=6,
        keyboard_type=ft.KeyboardType.NUMBER,
        password=True,
        can_reveal_password=True,
        border_radius=ft.BorderRadius.all(10),
        visible=False,
    )

    status_message = ft.Text(value="", size=13, weight=ft.FontWeight.W_500)
    loading_ring = ft.ProgressRing(width=24, height=24, stroke_width=2, visible=False)

    send_otp_btn = ft.FilledButton(
        content="Send Verification Code",
        icon=ft.Icons.SMS,
        bgcolor=ft.Colors.INDIGO_600,
        color=ft.Colors.WHITE,
        height=48,
        width=300,
    )

    verify_otp_btn = ft.FilledButton(
        content="Verify & Sign In",
        icon=ft.Icons.VERIFIED_USER,
        bgcolor=ft.Colors.GREEN_700,
        color=ft.Colors.WHITE,
        height=48,
        width=300,
        visible=False,
    )

    resend_btn = ft.TextButton(
        content="Didn't receive code? Resend OTP",
        visible=False,
    )

    def handle_send_otp(e):
        phone = phone_input.value.strip()
        if not phone.startswith("+") or len(phone) < 10:
            status_message.value = "Please enter a valid international number starting with '+' (e.g. +14155552671)"
            status_message.color = ft.Colors.RED_700
            if page:
                page.update()
            return

        loading_ring.visible = True
        send_otp_btn.disabled = True
        status_message.value = "Requesting verification code..."
        status_message.color = ft.Colors.BLUE_700
        if page:
            page.update()

        try:
            res = api_client.request_otp(phone)
            phone_input.disabled = True
            send_otp_btn.visible = False
            otp_input.visible = True
            verify_otp_btn.visible = True
            resend_btn.visible = True
            loading_ring.visible = False
            status_message.color = ft.Colors.GREEN_700
            status_message.value = "Code dispatched! (In Dev Mode, view code in server terminal log)"
        except Exception as ex:
            loading_ring.visible = False
            send_otp_btn.disabled = False
            status_message.color = ft.Colors.RED_700
            status_message.value = str(ex)

        if page:
            page.update()

    def handle_verify_otp(e):
        code = otp_input.value.strip()
        if len(code) != 6:
            status_message.value = "Please enter the complete 6-digit verification code."
            status_message.color = ft.Colors.RED_700
            if page:
                page.update()
            return

        loading_ring.visible = True
        verify_otp_btn.disabled = True
        if page:
            page.update()

        try:
            data = api_client.verify_otp(phone_input.value.strip(), code)
            status_message.color = ft.Colors.GREEN_700
            status_message.value = "Authentication successful!"
            if page:
                page.update()
            on_login_success(data["user"])
        except Exception as ex:
            loading_ring.visible = False
            verify_otp_btn.disabled = False
            status_message.color = ft.Colors.RED_700
            status_message.value = str(ex)
            if page:
                page.update()

    send_otp_btn.on_click = handle_send_otp
    verify_otp_btn.on_click = handle_verify_otp
    resend_btn.on_click = handle_send_otp

    return ft.Container(
        expand=True,
        alignment=ft.Alignment.CENTER,
        padding=24,
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(height=40),
                ft.Icon(ft.Icons.SECURITY, size=72, color=ft.Colors.INDIGO_600),
                ft.Text("Secure Business Portal", size=24, weight=ft.FontWeight.BOLD),
                ft.Text("Two-Factor Authentication via Mobile OTP", size=14, color=ft.Colors.GREY_600),
                ft.Divider(height=24, color="transparent"),
                ft.Card(
                    elevation=3,
                    content=ft.Container(
                        padding=20,
                        content=ft.Column([
                            phone_input,
                            ft.Container(height=8),
                            otp_input,
                            ft.Container(height=8),
                            ft.Row([loading_ring, status_message], alignment=ft.MainAxisAlignment.CENTER),
                            ft.Container(height=12),
                            send_otp_btn,
                            verify_otp_btn,
                            ft.Container(height=4),
                            resend_btn
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                    )
                ),
                ft.Container(height=20),
                ft.Row([
                    ft.Icon(ft.Icons.LOCK_OUTLINE, size=16, color=ft.Colors.GREY_500),
                    ft.Text("Protected with TLS 1.3 & SHA-256 OTP Verification", size=12, color=ft.Colors.GREY_500)
                ], alignment=ft.MainAxisAlignment.CENTER)
            ]
        )
    )
