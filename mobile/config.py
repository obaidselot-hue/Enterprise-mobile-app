import os

API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = os.getenv("API_PORT", "8000")
API_BASE_URL = f"http://{API_HOST}:{API_PORT}/api/v1"

# Visual Theme Constants
PRIMARY_COLOR = "#3F51B5"      # Indigo
SECONDARY_COLOR = "#009688"    # Teal
BACKGROUND_COLOR = "#F4F6F9"   # Soft Gray
ACCENT_GREEN = "#2E7D32"
ACCENT_RED = "#C62828"
ACCENT_AMBER = "#EF6C00"
