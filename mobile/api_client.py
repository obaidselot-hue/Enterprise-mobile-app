import requests
from typing import Optional, Dict, Any
from config import API_BASE_URL

class APIClient:
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.user_profile: Optional[Dict[str, Any]] = None

    def _get_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers

    def set_tokens(self, access_token: str, refresh_token: str, user: Dict[str, Any]):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.user_profile = user

    def clear_tokens(self):
        self.access_token = None
        self.refresh_token = None
        self.user_profile = None

    def request_otp(self, phone_number: str) -> Dict[str, Any]:
        url = f"{self.base_url}/auth/request-otp"
        res = requests.post(url, json={"phone_number": phone_number}, timeout=10)
        if not res.ok:
            error_msg = res.json().get("detail", "Failed to dispatch OTP.")
            raise Exception(error_msg)
        return res.json()

    def verify_otp(self, phone_number: str, otp_code: str) -> Dict[str, Any]:
        url = f"{self.base_url}/auth/verify-otp"
        res = requests.post(url, json={"phone_number": phone_number, "otp_code": otp_code}, timeout=10)
        if not res.ok:
            error_msg = res.json().get("detail", "Failed to verify OTP.")
            raise Exception(error_msg)
        data = res.json()
        self.set_tokens(data["access_token"], data["refresh_token"], data["user"])
        return data

    def get_dashboard_summary(self, range_filter: str = "this_month") -> Dict[str, Any]:
        url = f"{self.base_url}/dashboard/summary"
        res = requests.get(url, params={"range_filter": range_filter}, headers=self._get_headers(), timeout=10)
        if not res.ok:
            raise Exception(res.json().get("detail", "Unable to load dashboard."))
        return res.json()

    def get_parties(self, party_type: Optional[str] = None, search: Optional[str] = None) -> list:
        url = f"{self.base_url}/masters/parties"
        params = {}
        if party_type:
            params["party_type"] = party_type
        if search:
            params["search"] = search
        res = requests.get(url, params=params, headers=self._get_headers(), timeout=10)
        if not res.ok:
            raise Exception(res.json().get("detail", "Failed to load parties."))
        return res.json()

    def create_party(self, payload: dict) -> dict:
        url = f"{self.base_url}/masters/parties"
        res = requests.post(url, json=payload, headers=self._get_headers(), timeout=10)
        if not res.ok:
            raise Exception(res.json().get("detail", "Failed to create party entity."))
        return res.json()

    def get_products(self, low_stock_only: bool = False, search: Optional[str] = None) -> list:
        url = f"{self.base_url}/masters/products"
        params = {"low_stock_only": low_stock_only}
        if search:
            params["search"] = search
        res = requests.get(url, params=params, headers=self._get_headers(), timeout=10)
        if not res.ok:
            raise Exception(res.json().get("detail", "Failed to load products."))
        return res.json()

    def create_product(self, payload: dict) -> dict:
        url = f"{self.base_url}/masters/products"
        res = requests.post(url, json=payload, headers=self._get_headers(), timeout=10)
        if not res.ok:
            raise Exception(res.json().get("detail", "Failed to create product."))
        return res.json()

    def get_transactions(self, tx_type: Optional[str] = None) -> list:
        url = f"{self.base_url}/transactions"
        params = {}
        if tx_type:
            params["transaction_type"] = tx_type
        res = requests.get(url, params=params, headers=self._get_headers(), timeout=10)
        if not res.ok:
            raise Exception(res.json().get("detail", "Failed to load transactions."))
        return res.json()

    def create_transaction(self, payload: dict) -> dict:
        url = f"{self.base_url}/transactions"
        res = requests.post(url, json=payload, headers=self._get_headers(), timeout=10)
        if not res.ok:
            raise Exception(res.json().get("detail", "Failed to create transaction."))
        return res.json()

    def get_sales_register(self) -> dict:
        url = f"{self.base_url}/registers/sales"
        res = requests.get(url, headers=self._get_headers(), timeout=10)
        if not res.ok:
            raise Exception(res.json().get("detail", "Failed to load sales register."))
        return res.json()

    def get_purchase_register(self) -> dict:
        url = f"{self.base_url}/registers/purchases"
        res = requests.get(url, headers=self._get_headers(), timeout=10)
        if not res.ok:
            raise Exception(res.json().get("detail", "Failed to load purchase register."))
        return res.json()

    def get_stock_register(self) -> dict:
        url = f"{self.base_url}/registers/stock"
        res = requests.get(url, headers=self._get_headers(), timeout=10)
        if not res.ok:
            raise Exception(res.json().get("detail", "Failed to load stock movements."))
        return res.json()

    def get_pl_statement(self) -> dict:
        url = f"{self.base_url}/reports/pl-statement"
        res = requests.get(url, headers=self._get_headers(), timeout=10)
        if not res.ok:
            raise Exception(res.json().get("detail", "Failed to load P&L statement."))
        return res.json()

    def get_aging_analysis(self) -> dict:
        url = f"{self.base_url}/reports/aging-analysis"
        res = requests.get(url, headers=self._get_headers(), timeout=10)
        if not res.ok:
            raise Exception(res.json().get("detail", "Failed to load aging report."))
        return res.json()

    def get_tax_summary(self) -> dict:
        url = f"{self.base_url}/reports/tax-summary"
        res = requests.get(url, headers=self._get_headers(), timeout=10)
        if not res.ok:
            raise Exception(res.json().get("detail", "Failed to load tax summary."))
        return res.json()

api_client = APIClient()
