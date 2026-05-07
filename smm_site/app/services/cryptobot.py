import os
import requests
import logging

logger = logging.getLogger("cryptobot")

CRYPTOBOT_TOKEN = os.getenv("CRYPTOBOT_TOKEN", "425072:AANyYdRDRlsxJCqScskRRCIvL91wLmX4B7")
BASE_URL = os.getenv("CRYPTOBOT_BASE_URL", "https://pay.crypt.bot/api")


def create_invoice(amount: float, description: str,
                   payload_data: str | None = None,
                   paid_btn_url: str | None = None) -> dict:
    """Create CryptoBot invoice. Returns dict with pay_url, external_id, raw."""
    headers = {
        "Crypto-Pay-API-Token": CRYPTOBOT_TOKEN,
        "Content-Type": "application/json",
    }
    payload = {
        "asset": "USDT",
        "amount": str(round(amount, 2)),
        "description": description,
        "allow_comments": False,
        "allow_anonymous": False,
    }
    if payload_data:
        payload["payload"] = payload_data
    if paid_btn_url:
        payload["paid_btn_name"] = "callback"
        payload["paid_btn_url"] = paid_btn_url

    try:
        resp = requests.post(f"{BASE_URL}/createInvoice", headers=headers, json=payload, timeout=10)
    except requests.RequestException as exc:
        logger.exception("Cryptobot request failed")
        return {"error": str(exc)}

    status = resp.status_code
    try:
        data = resp.json()
    except ValueError:
        return {"error": "non-json response", "raw_text": resp.text, "status_code": status}

    pay_url = None
    external_id = None
    if isinstance(data, dict):
        result = data.get("result") if isinstance(data.get("result"), dict) else data
        pay_url = result.get("pay_url") or result.get("bot_invoice_url") or result.get("mini_app_invoice_url")
        external_id = result.get("invoice_id") or result.get("id")

    return {"raw": data, "status_code": status, "pay_url": pay_url, "external_id": external_id}


def check_invoice_status(external_id: str) -> str:
    """Returns 'paid', 'pending', or 'failed'."""
    headers = {"Crypto-Pay-API-Token": CRYPTOBOT_TOKEN}
    try:
        resp = requests.get(f"{BASE_URL}/getInvoices",
                            headers=headers,
                            params={"invoice_ids": str(external_id)},
                            timeout=10)
        data = resp.json()
    except Exception as e:
        logger.warning(f"cryptobot check_invoice_status failed: {e}")
        return "pending"

    items = (data.get("result") or {}).get("items") or []
    if not items:
        return "pending"
    status = (items[0].get("status") or "").lower()
    if status in ("paid",):
        return "paid"
    if status in ("expired", "cancelled", "canceled"):
        return "failed"
    return "pending"
