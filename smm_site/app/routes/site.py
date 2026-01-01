from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.services.vingboost import get_services, get_balance, create_order
from app.services.crystalpay import create_invoice as crystalpay_create_invoice
from app.services.cryptobot import create_invoice as cryptobot_create_invoice
from fastapi.responses import RedirectResponse
from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from app import site

app.include_router(site.router)
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


# ---------------- Главная ----------------
@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    services = get_services()
    balance = get_balance()
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
        "total": round(quantity * 0.05, 1),  # пример
        "quantity": quantity,
        "type": "Просмотры",
        "link": link
    }

    balance = get_balance()

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

    return templates.TemplateResponse(
        "statistics.html",  # ← ВАЖНО: ТОЧНО statistics.html
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
    # ВРЕМЕННАЯ логика цены (потом подключим реальную)
    price_rub = round(quantity * 0.05, 1)
    price_usdt = round(price_rub / 90, 2)  # пример

    # Choose provider (default: crystalpay). Both adapters return dicts.
    selected = (provider or "crystalpay").lower()
    if selected == "cryptobot":
        invoice = cryptobot_create_invoice(amount=price_usdt, description=f"Boostix заказ | {quantity}")
        other_provider = crystalpay_create_invoice
    else:
        invoice = crystalpay_create_invoice(amount=price_usdt, description=f"Boostix заказ | {quantity}")
        other_provider = cryptobot_create_invoice
    # Простая проверка ответа от провайдера — логируем и безопасно обрабатываем
    print("[create_invoice_route] invoice response:", invoice)

    if not isinstance(invoice, dict):
        raise HTTPException(status_code=502, detail="Invalid invoice response from payment provider")

    # Попробуем несколько возможных ключей с URL оплаты
    pay_url = invoice.get("pay_url") or invoice.get("url") or invoice.get("invoice_url")
    # Иногда сервис возвращает вложенный объект
    if not pay_url and isinstance(invoice.get("result"), dict):
        pay_url = invoice["result"].get("pay_url") or invoice["result"].get("url")

    if not pay_url:
        # Try fallback provider once
        print("[create_invoice_route] primary provider returned no pay_url, trying fallback provider")
        try:
            fallback = other_provider(amount=price_usdt, description=f"Boostix заказ | {quantity}")
        except Exception as e:
            print("[create_invoice_route] fallback provider exception:", e)
            raise HTTPException(status_code=502, detail={"message": "Payment URL not found and fallback failed", "response": invoice})

        print("[create_invoice_route] fallback response:", fallback)
        if isinstance(fallback, dict):
            pay_url = fallback.get("pay_url") or fallback.get("url") or (fallback.get("result") or {}).get("pay_url")

    if not pay_url:
        raise HTTPException(status_code=502, detail={"message": "Payment URL not found in invoice response", "response": invoice})


    return RedirectResponse(pay_url, status_code=302)
