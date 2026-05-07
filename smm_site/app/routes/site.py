import os
from fastapi import APIRouter, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.services.vingboost import get_services, create_order
from app.services.crystalpay import (
    create_invoice as crystalpay_create_invoice,
    check_invoice_status as crystalpay_check_status,
)
from app.services.cryptobot import (
    create_invoice as cryptobot_create_invoice,
    check_invoice_status as cryptobot_check_status,
)
from app.database.db import (
    get_db, get_user, create_user, get_balance, update_balance, add_balance,
    create_invoice_record, get_invoice, mark_invoice_paid,
)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# ---------------- Constants ----------------
MARKUP_PERCENT = 30
MIN_PRICE_RUB = 1.0
RUB_PER_USDT = float(os.getenv("RUB_PER_USDT", "90"))
CURRENCY = "₽"


# ---------------- Helpers ----------------
def _username(request: Request) -> str:
    return request.cookies.get("username") or "guest"


def _balance_obj(db: Session, username: str) -> dict:
    """Always return a dict so templates can do balance.balance / balance.currency."""
    user = get_user(db, username) or create_user(db, username)
    return {"balance": round(user.balance or 0.0, 1), "currency": CURRENCY}


def _public_base_url(request: Request) -> str:
    """Best-effort public URL for callbacks/redirects."""
    env_url = os.getenv("PUBLIC_BASE_URL") or os.getenv("REPLIT_DEV_DOMAIN")
    if env_url:
        if not env_url.startswith("http"):
            env_url = "https://" + env_url
        return env_url.rstrip("/")
    return str(request.base_url).rstrip("/")


# ---------------- Home ----------------
@router.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    username = _username(request)
    balance = _balance_obj(db, username)
    services = get_services()
    for s in services:
        base_rate = s.get("rate", 0)
        s["rate"] = round(float(base_rate) * (1 + MARKUP_PERCENT / 100), 2)
        s["currency"] = CURRENCY
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "services": services, "balance": balance}
    )


# ---------------- Live balance API ----------------
@router.get("/api/balance")
async def api_balance(request: Request, db: Session = Depends(get_db)):
    return JSONResponse(_balance_obj(db, _username(request)))


# ---------------- Create order (uses balance) ----------------
@router.post("/create_order", response_class=HTMLResponse)
async def order_created(
    request: Request,
    service_id: str = Form(...),
    link: str = Form(...),
    quantity: int = Form(...),
    db: Session = Depends(get_db),
):
    username = _username(request)
    user_balance = get_balance(db, username)

    services = get_services()
    service = next((s for s in services if str(s.get("service")) == str(service_id)
                    or str(s.get("id")) == str(service_id)), None)
    if not service:
        return HTMLResponse("Услуга не найдена", status_code=404)

    rate = float(service.get("rate", 0)) * (1 + MARKUP_PERCENT / 100)
    order_cost = round((rate / 1000) * quantity, 2)

    if user_balance < order_cost:
        return HTMLResponse("Недостаточно средств. Пополните баланс.", status_code=400)

    update_balance(db, username, user_balance - order_cost)
    api_order = create_order(service_id, link, quantity)

    order = {
        "order": api_order.get("order"),
        "total": order_cost,
        "quantity": quantity,
        "type": service.get("name", "Услуга"),
        "link": link,
    }
    balance = _balance_obj(db, username)
    return templates.TemplateResponse(
        "order_created.html",
        {"request": request, "order": order, "balance": balance}
    )


# ---------------- Other static pages ----------------
@router.get("/orders", response_class=HTMLResponse)
async def orders_page(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse(
        "orders.html",
        {"request": request, "orders": [], "balance": _balance_obj(db, _username(request))}
    )


@router.get("/statistics", response_class=HTMLResponse)
async def statistics_page(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse(
        "statistics.html",
        {"request": request, "balance": _balance_obj(db, _username(request))}
    )


@router.get("/support", response_class=HTMLResponse)
async def support_page(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse(
        "support.html",
        {"request": request, "balance": _balance_obj(db, _username(request))}
    )


@router.get("/privacy", response_class=HTMLResponse)
async def privacy_page(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse(
        "privacy.html",
        {"request": request, "balance": _balance_obj(db, _username(request))}
    )


@router.get("/terms", response_class=HTMLResponse)
async def terms_page(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse(
        "terms.html",
        {"request": request, "balance": _balance_obj(db, _username(request))}
    )


# ---------------- TOP-UP (real) ----------------
@router.post("/topup")
async def create_topup(
    request: Request,
    amount: float = Form(...),
    provider: str = Form("crystalpay"),
    db: Session = Depends(get_db),
):
    """Create a real top-up invoice via CrystalPay or CryptoBot, then redirect to payment."""
    username = _username(request)
    get_user(db, username) or create_user(db, username)

    amount_rub = max(float(amount), MIN_PRICE_RUB)
    amount_usdt = round(amount_rub / RUB_PER_USDT, 2)
    if amount_usdt < 0.01:
        amount_usdt = 0.01

    base = _public_base_url(request)
    success_url_template = f"{base}/topup/success?invoice_id={{INVOICE}}"

    selected = (provider or "crystalpay").lower()

    # First insert pending record so we have its id for callbacks/redirect
    inv = create_invoice_record(
        db, username=username, provider=selected,
        amount_rub=amount_rub, amount_usdt=amount_usdt,
        external_id=None, pay_url=None,
    )

    redirect_url = success_url_template.replace("{INVOICE}", str(inv.id))
    callback_url = f"{base}/webhook/{selected}"

    if selected == "cryptobot":
        result = cryptobot_create_invoice(
            amount=amount_usdt,
            description=f"Boostix пополнение #{inv.id}",
            payload_data=str(inv.id),
            paid_btn_url=redirect_url,
        )
    else:
        result = crystalpay_create_invoice(
            amount=amount_usdt,
            description=f"Boostix пополнение #{inv.id}",
            callback_url=callback_url,
            redirect_url=redirect_url,
            payload_data=str(inv.id),
        )

    pay_url = result.get("pay_url") if isinstance(result, dict) else None
    external_id = result.get("external_id") if isinstance(result, dict) else None

    inv.pay_url = pay_url
    inv.external_id = str(external_id) if external_id else None
    db.commit()
    db.refresh(inv)

    if not pay_url:
        return templates.TemplateResponse(
            "topup_error.html",
            {"request": request, "balance": _balance_obj(db, username),
             "error": (result or {}).get("error") or "Платёжный сервис не вернул ссылку для оплаты."}
        )

    return RedirectResponse(pay_url, status_code=302)


@router.get("/topup/success", response_class=HTMLResponse)
async def topup_success(request: Request, invoice_id: int, db: Session = Depends(get_db)):
    """User returns from payment. Verify with provider and credit balance if paid."""
    username = _username(request)
    inv = get_invoice(db, invoice_id)

    paid = False
    if inv and inv.status != "paid" and inv.external_id:
        if inv.provider == "cryptobot":
            status = cryptobot_check_status(inv.external_id)
        else:
            status = crystalpay_check_status(inv.external_id)
        if status == "paid":
            mark_invoice_paid(db, inv.id)
            add_balance(db, inv.username, inv.amount_rub)
            paid = True
    elif inv and inv.status == "paid":
        paid = True

    return templates.TemplateResponse(
        "topup_result.html",
        {
            "request": request,
            "balance": _balance_obj(db, username),
            "invoice": inv,
            "paid": paid,
        }
    )


@router.post("/webhook/crystalpay")
async def webhook_crystalpay(request: Request, db: Session = Depends(get_db)):
    try:
        data = await request.json()
    except Exception:
        data = {}

    payload = str(data.get("payload") or "")
    state = (data.get("state") or data.get("status") or "").lower()
    if payload and state in ("paid", "success", "completed"):
        try:
            inv = get_invoice(db, int(payload))
        except ValueError:
            inv = None
        if inv and inv.status != "paid":
            mark_invoice_paid(db, inv.id)
            add_balance(db, inv.username, inv.amount_rub)
    return {"ok": True}


@router.post("/webhook/cryptobot")
async def webhook_cryptobot(request: Request, db: Session = Depends(get_db)):
    try:
        data = await request.json()
    except Exception:
        data = {}

    payload_obj = data.get("payload") or {}
    update_type = data.get("update_type") or ""
    if update_type == "invoice_paid" and isinstance(payload_obj, dict):
        ref = str(payload_obj.get("payload") or "")
        if ref:
            try:
                inv = get_invoice(db, int(ref))
            except ValueError:
                inv = None
            if inv and inv.status != "paid":
                mark_invoice_paid(db, inv.id)
                add_balance(db, inv.username, inv.amount_rub)
    return {"ok": True}


# ---------------- Purchase invoice (legacy direct pay) ----------------
@router.post("/create_invoice")
async def create_invoice_route(
    request: Request,
    service_id: str = Form(...),
    link: str = Form(...),
    quantity: int = Form(...),
    db: Session = Depends(get_db),
):
    """Pay for a service directly with the user's balance.
    If balance is insufficient, redirect to home with a message.
    """
    username = _username(request)

    services = get_services()
    service = next((s for s in services if str(s.get("service")) == str(service_id)
                    or str(s.get("id")) == str(service_id)), None)
    if not service:
        raise HTTPException(status_code=404, detail="Услуга не найдена")

    rate = float(service.get("rate", 0)) * (1 + MARKUP_PERCENT / 100)
    order_cost = round((rate / 1000) * quantity, 2)
    user_balance = get_balance(db, username)

    if user_balance < order_cost:
        return RedirectResponse(f"/?need_topup={order_cost}", status_code=302)

    update_balance(db, username, user_balance - order_cost)
    api_order = create_order(service_id, link, quantity)
    order = {
        "order": api_order.get("order"),
        "total": order_cost,
        "quantity": quantity,
        "type": service.get("name", "Услуга"),
        "link": link,
    }
    balance = _balance_obj(db, username)
    return templates.TemplateResponse(
        "order_created.html",
        {"request": request, "order": order, "balance": balance}
    )
