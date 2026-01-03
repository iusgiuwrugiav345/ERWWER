from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.services.vingboost import get_services, get_balance, create_order
from app.services.crystalpay import create_invoice as crystalpay_create_invoice
from app.services.cryptobot import create_invoice as cryptobot_create_invoice

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# ---------------- Главная ----------------
@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    services = get_services()
    balance = get_balance()
    
    # Round balance for display
    if balance and isinstance(balance.get("balance"), (int, float)):
        balance["balance"] = round(balance["balance"], 1)
        
    # Round service rates for display
    for s in services:
        if isinstance(s.get("rate"), (int, float)):
            s["rate"] = round(s["rate"], 1)
            
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "services": services,
            "balance": balance
        }
    )

# ---------------- Создание заказа ----------------
@router.post("/create_order", response_class=HTMLResponse)
async def order_created(
    request: Request,
    service_id: str = Form(...),
    link: str = Form(...),
    quantity: int = Form(...)
):
    api_order = create_order(service_id, link, quantity)

    order = {
        "order": api_order.get("order"),
        "total": round(quantity * 0.05, 1),
        "quantity": quantity,
        "type": "Просмотры",
        "link": link
    }

    balance = get_balance()
    if balance and isinstance(balance.get("balance"), (int, float)):
        balance["balance"] = round(balance["balance"], 1)

    return templates.TemplateResponse(
        "order_created.html",
        {
            "request": request,
            "order": order,
            "balance": balance
        }
    )


# ---------------- ЗАКАЗЫ ----------------
@router.get("/orders", response_class=HTMLResponse)
async def orders_page(request: Request):
    orders = []  # позже сюда подключишь реальные заказы
    balance = get_balance()
    
    if balance and isinstance(balance.get("balance"), (int, float)):
        balance["balance"] = round(balance["balance"], 1)

    return templates.TemplateResponse(
        "orders.html",
        {
            "request": request,
            "orders": orders,
            "balance": balance
        }
    )


# ---------------- СТАТИСТИКА ----------------
@router.get("/statistics", response_class=HTMLResponse)
async def statistics_page(request: Request):
    balance = get_balance()
    
    if balance and isinstance(balance.get("balance"), (int, float)):
        balance["balance"] = round(balance["balance"], 1)

    return templates.TemplateResponse(
        "statistics.html",
        {
            "request": request,
            "balance": balance
        }
    )

# ---------------- ПОДДЕРЖКА ----------------
@router.get("/support", response_class=HTMLResponse)
async def support_page(request: Request):
    balance = get_balance()
    
    if balance and isinstance(balance.get("balance"), (int, float)):
        balance["balance"] = round(balance["balance"], 1)

    return templates.TemplateResponse(
        "support.html",
        {
            "request": request,
            "balance": balance
        }
    )

@router.post("/create_invoice")
async def create_invoice_route(
    service_id: str = Form(...),
    link: str = Form(...),
    quantity: int = Form(...),
    provider: str = Form("crystalpay")
):
    # REAL logic for payment (internal precision)
    price_rub_raw = quantity * 0.05
    
    # CrystalPay works with RUB/USDT. Error says min 1 RUB.
    # We round up to 1 RUB if it's lower.
    price_rub = price_rub_raw
    if price_rub < 1.0:
        price_rub = 1.0
        
    price_usdt = round(price_rub / 90, 2)
    
    # Provider-specific rounding/minimums
    selected = (provider or "crystalpay").lower()
    if selected == "cryptobot":
        # CryptoBot works in USDT. Ensure at least 0.01 USDT
        if price_usdt < 0.01:
            price_usdt = 0.01
        invoice = cryptobot_create_invoice(amount=price_usdt, description=f"Boostix заказ | {quantity}")
        other_provider = crystalpay_create_invoice
    else:
        invoice = crystalpay_create_invoice(amount=price_usdt, description=f"Boostix заказ | {quantity}")
        other_provider = cryptobot_create_invoice
        
    print(f"[create_invoice_route] provider: {selected}, rub: {price_rub}, usdt: {price_usdt}")
    print("[create_invoice_route] invoice response:", invoice)

    if not isinstance(invoice, dict):
        raise HTTPException(status_code=502, detail="Invalid invoice response from payment provider")

    pay_url = invoice.get("pay_url") or invoice.get("url") or invoice.get("invoice_url")
    if not pay_url and isinstance(invoice.get("result"), dict):
        pay_url = invoice["result"].get("pay_url") or invoice["result"].get("url")

    if not pay_url:
        print("[create_invoice_route] primary provider failed, trying fallback")
        try:
            # Re-calculating for fallback if needed
            fallback_usdt = price_usdt
            if other_provider == cryptobot_create_invoice and fallback_usdt < 0.01:
                fallback_usdt = 0.01
            
            fallback = other_provider(amount=fallback_usdt, description=f"Boostix заказ | {quantity}")
        except Exception as e:
            print("[create_invoice_route] fallback exception:", e)
            raise HTTPException(status_code=502, detail={"message": "Payment URL not found and fallback failed", "response": invoice})

        print("[create_invoice_route] fallback response:", fallback)
        if isinstance(fallback, dict):
            pay_url = fallback.get("pay_url") or fallback.get("url") or (fallback.get("result") or {}).get("pay_url")

    if not pay_url:
        raise HTTPException(status_code=502, detail={"message": "Payment URL not found in invoice response", "response": invoice})

    return RedirectResponse(pay_url, status_code=302)
