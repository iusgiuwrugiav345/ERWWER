import os
import requests
import logging

logger = logging.getLogger("cryptobot")

# Prefer environment configuration; fallback to previous defaults if not set
CRYPTOBOT_TOKEN = os.getenv("CRYPTOBOT_TOKEN", "425072:AANyYdRDRlsxJCqScskRRCIvL91wLmX4B7")
BASE_URL = os.getenv("CRYPTOBOT_BASE_URL", "https://pay.crypt.bot/api")


def create_invoice(amount: float, description: str) -> dict:
    """Create invoice via Cryptobot API and return normalized response.

    Returns a dict containing at least the keys:
      - "raw": original parsed JSON
      - "status_code": HTTP status
      - optionally "pay_url" when available
      - or "error" on failure
    """

    headers = {
        "Crypto-Pay-API-Token": CRYPTOBOT_TOKEN,
        "Content-Type": "application/json",
    }

    payload = {
        "asset": "USDT",
        "amount": round(amount, 2),
        "description": description,
        "allow_comments": False,
        "allow_anonymous": False,
    }

    try:
        resp = requests.post(f"{BASE_URL}/createInvoice", headers=headers, json=payload, timeout=10)
    except requests.RequestException as exc:
        logger.exception("Cryptobot request failed")
        return {"error": str(exc)}

    status = resp.status_code
    try:
        data = resp.json()
    except ValueError:
        logger.error("Cryptobot returned non-JSON response: %s", resp.text)
        return {"error": "non-json response", "raw_text": resp.text, "status_code": status}

    # Try common keys for payment URL
    pay_url = None
    if isinstance(data, dict):
        pay_url = data.get("pay_url") or data.get("payment_url") or data.get("url") or data.get("invoice_url")
        # sometimes returned inside 'result' or 'data'
        if not pay_url:
            for key in ("result", "data", "invoice"):
                nested = data.get(key)
                if isinstance(nested, dict):
                    pay_url = nested.get("pay_url") or nested.get("payment_url") or nested.get("url") or nested.get("invoice_url")
                    if pay_url:
                        break

    result = {"raw": data, "status_code": status}
    if pay_url:
        result["pay_url"] = pay_url

    return result

