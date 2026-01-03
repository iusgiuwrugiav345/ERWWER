import os
import requests
import logging

# Настройки магазина (подставь свои реальные)
CRYSTALPAY_LOGIN = os.getenv("CRYSTALPAY_LOGIN", "boostixpayment")
CRYSTALPAY_SECRET = os.getenv("CRYSTALPAY_SECRET", "203f44e3b335e616d65d67635555029d07f533cf")
# Default endpoint (override with real provider URL via env)
CRYSTALPAY_ENDPOINT = os.getenv("CRYSTALPAY_ENDPOINT", "https://api.crystalpay.io/v1/invoices")
# Payment type (provider requires this field). Allowed values: 'purchase', 'topup'
# Map common synonyms to 'purchase' by default.
CRYSTALPAY_TYPE = os.getenv("CRYSTALPAY_TYPE", "purchase")
# Lifetime for invoice in seconds (provider requires this field)
CRYSTALPAY_LIFETIME = int(os.getenv("CRYSTALPAY_LIFETIME", "3600"))

METHOD_LIST_URL = "https://api.crystalpay.io/v3/method/list/"

# Фильтруем методы только по выбранным валютам
ALLOWED_METHODS = {"USDT", "BTC", "ETH", "CARD"}  # пример

def get_available_methods():
    payload = {
        "auth_login": CRYSTALPAY_LOGIN,
        "auth_secret": CRYSTALPAY_SECRET
    }

    try:
        resp = requests.post(METHOD_LIST_URL, json=payload, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        return {"error": str(e)}

    try:
        data = resp.json()
    except ValueError:
        return {"error": "Non-JSON response", "raw_text": resp.text, "status_code": resp.status_code}

    available_methods = []

    for method in data.get("methods", []):
        # проверяем, что метод включён и разрешённая валюта
        if method.get("in", {}).get("enabled") and method.get("currency") in ALLOWED_METHODS:
            available_methods.append({
                "method": method.get("method"),
                "name": method.get("name"),
                "currency": method.get("currency"),
                "min": method.get("in", {}).get("limits", {}).get("min"),
                "max": method.get("in", {}).get("limits", {}).get("max"),
                "commissions": method.get("in", {}).get("commissions", {})
            })

    return available_methods


def create_invoice(amount: float, description: str, callback_url: str | None = None) -> dict:
    """Create an invoice via CrystalPay API (best-effort generic implementation).

    The function returns a dict with at least `raw` and `status_code` on HTTP responses.
    If a payment URL is found it will also include `pay_url`.
    """

    CREATE_URL = os.getenv("CRYSTALPAY_CREATE_URL", "https://api.crystalpay.io/v3/invoice/create/")

    # Normalize/mapping for provider-accepted `type` values
    t = (CRYSTALPAY_TYPE or "").strip().lower()
    if t not in ("purchase", "topup"):
        # map common synonyms
        if t in ("invoice", "bill", "payment", "card"):
            t = "purchase"
        else:
            t = "purchase"

    payload = {
        "auth_login": CRYSTALPAY_LOGIN,
        "auth_secret": CRYSTALPAY_SECRET,
        "amount": round(amount, 2),
        "currency": "USDT",
        "description": description,
        "type": t,
        "lifetime": CRYSTALPAY_LIFETIME,
    }
    if callback_url:
        payload["callback_url"] = callback_url

    try:
        resp = requests.post(CREATE_URL, json=payload, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as exc:
        return {"error": str(exc)}

    status = resp.status_code
    try:
        data = resp.json()
    except ValueError:
        return {"error": "non-json response", "raw_text": resp.text, "status_code": status}

    # Try to find common payment URL keys
    pay_url = None
    if isinstance(data, dict):
        pay_url = data.get("pay_url") or data.get("payment_url") or data.get("url") or data.get("invoice_url")
        if not pay_url:
            for key in ("data", "result", "invoice"):
                nested = data.get(key)
                if isinstance(nested, dict):
                    pay_url = nested.get("pay_url") or nested.get("payment_url") or nested.get("url")
                    if pay_url:
                        break

    result = {"raw": data, "status_code": status}
    if pay_url:
        result["pay_url"] = pay_url

    return result

if __name__ == "__main__":
    methods = get_available_methods()
    if "error" in methods:
        print("Error:", methods["error"])
    else:
        print("Available payment methods:")
        for m in methods:
            print(m)
