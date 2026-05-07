import os
import requests
import logging

CRYSTALPAY_LOGIN = os.getenv("CRYSTALPAY_LOGIN", "boostixpayment")
CRYSTALPAY_SECRET = os.getenv("CRYSTALPAY_SECRET", "203f44e3b335e616d65d67635555029d07f533cf")
CRYSTALPAY_TYPE = os.getenv("CRYSTALPAY_TYPE", "purchase")
CRYSTALPAY_LIFETIME = int(os.getenv("CRYSTALPAY_LIFETIME", "3600"))

CREATE_URL = os.getenv("CRYSTALPAY_CREATE_URL", "https://api.crystalpay.io/v3/invoice/create/")
INFO_URL = os.getenv("CRYSTALPAY_INFO_URL", "https://api.crystalpay.io/v3/invoice/info/")
METHOD_LIST_URL = "https://api.crystalpay.io/v3/method/list/"

ALLOWED_METHODS = {"USDT", "BTC", "ETH", "CARD"}


def get_available_methods():
    payload = {"auth_login": CRYSTALPAY_LOGIN, "auth_secret": CRYSTALPAY_SECRET}
    try:
        resp = requests.post(METHOD_LIST_URL, json=payload, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        return {"error": str(e)}
    try:
        data = resp.json()
    except ValueError:
        return {"error": "Non-JSON response", "raw_text": resp.text, "status_code": resp.status_code}

    available = []
    for method in data.get("methods", []):
        if method.get("in", {}).get("enabled") and method.get("currency") in ALLOWED_METHODS:
            available.append({
                "method": method.get("method"),
                "name": method.get("name"),
                "currency": method.get("currency"),
            })
    return available


def create_invoice(amount: float, description: str, callback_url: str | None = None,
                   redirect_url: str | None = None, payload_data: str | None = None) -> dict:
    """Create an invoice via CrystalPay. Returns dict with pay_url, external_id, raw."""
    t = (CRYSTALPAY_TYPE or "").strip().lower()
    if t not in ("purchase", "topup"):
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
    if redirect_url:
        payload["redirect_url"] = redirect_url
    if payload_data:
        payload["payload"] = payload_data

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

    pay_url = None
    external_id = None
    if isinstance(data, dict):
        pay_url = data.get("pay_url") or data.get("url")
        external_id = data.get("id") or data.get("invoice_id")
        for key in ("data", "result", "invoice"):
            nested = data.get(key)
            if isinstance(nested, dict):
                pay_url = pay_url or nested.get("pay_url") or nested.get("url")
                external_id = external_id or nested.get("id") or nested.get("invoice_id")

    return {"raw": data, "status_code": status, "pay_url": pay_url, "external_id": external_id}


def check_invoice_status(external_id: str) -> str:
    """Returns 'paid', 'pending', or 'failed'."""
    payload = {
        "auth_login": CRYSTALPAY_LOGIN,
        "auth_secret": CRYSTALPAY_SECRET,
        "id": external_id,
    }
    try:
        resp = requests.post(INFO_URL, json=payload, timeout=10)
        data = resp.json() if resp.content else {}
    except Exception as e:
        logging.warning(f"crystalpay check_invoice_status failed: {e}")
        return "pending"

    state = (data.get("state") or data.get("status") or "").lower()
    nested = data.get("data") or data.get("result") or {}
    if isinstance(nested, dict) and not state:
        state = (nested.get("state") or nested.get("status") or "").lower()

    if state in ("paid", "success", "completed"):
        return "paid"
    if state in ("failed", "cancelled", "canceled", "expired"):
        return "failed"
    return "pending"
