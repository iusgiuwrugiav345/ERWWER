from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.services.vingboost import get_services, get_balance, create_order
from app.services.crystalpay import create_invoice as crystalpay_create_invoice
from app.services.cryptobot import create_invoice as cryptobot_create_invoice
from fastapi import APIRouter, Request, Form, Depends
from sqlalchemy.orm import Session

from app.database.db import get_db, get_user, create_user, get_balance, update_balance
from app.services.vingboost import get_services, create_order

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# ---------------- Константы ----------------
MARKUP_PERCENT = 30  # твоя наценка в процентах
MIN_PRICE_RUB = 1.0  # минимальная цена для платежа

# ---------------- Главная ----------------
@router.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    username = request.cookies.get("username") or "guest"
    user = get_user(db, username)
    if not user:
        user = create_user(db, username)

    balance = round(get_balance(db, username), 1)
    services = get_services()  # получаем услуги с VingBoost API

    for s in services:
        base_rate = s.get("rate", 0)        # цена поставщика
        s["rate"] = round(base_rate * (1 + MARKUP_PERCENT/100), 2)  # цена с твоей наценкой
        s["currency"] = "₽"

    return templates.TemplateResponse(
        "index.html",
        {"request": request, "services": services, "balance": balance}
    )

# ---------------- Создание заказа ----------------
@router.post("/create_order", response_class=HTMLResponse)
async def order_created(
    request: Request,
    service_id: str = Form(...),
    link: str = Form(...),
    quantity: int = Form(...),
    db: Session = Depends(get_db)
):
    username = request.cookies.get("username") or "guest"
    user_balance = get_balance(db, username)

    services = get_services()
    service = next((s for s in services if s["id"] == service_id), None)
    if not service:
        return HTMLResponse("Услуга не найдена", status_code=404)

    # Цена с наценкой
    price_per_unit = service.get("rate", 0)
    order_cost = round(quantity * price_per_unit, 2)

    if user_balance < order_cost:
        return HTMLResponse("Недостаточно средств", status_code=400)

    # списываем баланс
    update_balance(db, username, user_balance - order_cost)

    # создаем заказ через VingBoost
    api_order = create_order(service_id, link, quantity)
    order = {
        "order": api_order.get("order"),
        "total": order_cost,
        "quantity": quantity,
        "type": service.get("name", "Услуга"),
        "link": link
    }

    balance = round(get_balance(db, username), 1)
    return templates.TemplateResponse(
        "order_created.html",
        {"request": request, "order": order, "balance": balance}
    )

# ---------------- ЗАКАЗЫ ----------------
@router.get("/orders", response_class=HTMLResponse)
async def orders_page(request: Request, db: Session = Depends(get_db)):
    username = request.cookies.get("username") or "guest"
    balance = round(get_balance(db, username), 1)
    orders = []  # подключи свои реальные заказы позже
    return templates.TemplateResponse(
        "orders.html", {"request": request, "orders": orders, "balance": balance}
    )


# ---------------- СТАТИСТИКА ----------------
@router.get("/statistics", response_class=HTMLResponse)
async def statistics_page(request: Request, db: Session = Depends(get_db)):
    username = request.cookies.get("username") or "guest"
    balance = round(get_balance(db, username), 1)
    return templates.TemplateResponse(
        "statistics.html", {"request": request, "balance": balance}
    )

# ---------------- ПОДДЕРЖКА ----------------
@router.get("/support", response_class=HTMLResponse)
async def support_page(request: Request, db: Session = Depends(get_db)):
    username = request.cookies.get("username") or "guest"
    balance = round(get_balance(db, username), 1)
    return templates.TemplateResponse(
        "support.html", {"request": request, "balance": balance}
    )

@router.get("/privacy", response_class=HTMLResponse)
async def privacy_page(request: Request):
    balance = get_balance()
    if balance and isinstance(balance.get("balance"), (int, float)):
        balance["balance"] = round(balance["balance"], 1)
        balance["currency"] = "₽"
    return templates.TemplateResponse("privacy.html", {"request": request, "balance": balance})

@router.get("/terms", response_class=HTMLResponse)
async def terms_page(request: Request):
    balance = get_balance()
    if balance and isinstance(balance.get("balance"), (int, float)):
        balance["balance"] = round(balance["balance"], 1)
        balance["currency"] = "₽"
    return templates.TemplateResponse("terms.html", {"request": request, "balance": balance})

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

@router.post("/create_invoice")
async def create_invoice_route(
    service_id: str = Form(...),
    link: str = Form(...),
    quantity: int = Form(...),
    provider: str = Form("crystalpay")
):
    # Берём услугу и считаем цену
    services = get_services()
    service = next((s for s in services if s["id"] == service_id), None)
    if not service:
        raise HTTPException(status_code=404, detail="Услуга не найдена")

    price_per_unit = service.get("rate", 0)
    price_rub_raw = quantity * price_per_unit
    price_rub = max(price_rub_raw, MIN_PRICE_RUB)  # минимум для платежа
    price_usdt = round(price_rub / 90, 2)  # курс рубля к USDT (пример)

    selected = provider.lower()
    if selected == "cryptobot":
        if price_usdt < 0.01:
            price_usdt = 0.01
        invoice = cryptobot_create_invoice(amount=price_usdt, description=f"Boostix заказ | {quantity}")
        fallback_provider = crystalpay_create_invoice
    else:
        invoice = crystalpay_create_invoice(amount=price_usdt, description=f"Boostix заказ | {quantity}")
        fallback_provider = cryptobot_create_invoice

    pay_url = invoice.get("pay_url") or invoice.get("url") or invoice.get("invoice_url")
    if not pay_url:
        # пробуем fallback
        fallback = fallback_provider(amount=price_usdt, description=f"Boostix заказ | {quantity}")
        pay_url = fallback.get("pay_url") or fallback.get("url") or fallback.get("invoice_url")

    if not pay_url:
        raise HTTPException(status_code=502, detail="Ссылка на оплату не найдена")

    return RedirectResponse(pay_url, status_code=302)
