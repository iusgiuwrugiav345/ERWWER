# SMM Site - Social Media Marketing Panel

## Overview
A web application for social media marketing services built with FastAPI (Python). Users can purchase social media services like views, likes, and followers through various payment providers.

## Current State
- Project successfully imported and running on Replit
- FastAPI server running on port 5000
- All dependencies installed

## Project Structure
```
smm_site/
├── app/
│   ├── main.py         # FastAPI application entry point
│   ├── config.py       # Configuration (API keys)
│   ├── database.py     # Database utilities
│   ├── models/         # Data models
│   │   └── order.py    # Order model
│   ├── routes/         # API endpoints
│   │   ├── api.py      # API routes
│   │   └── site.py     # Website routes
│   ├── services/       # External service integrations
│   │   ├── vingboost.py    # VingBoost SMM provider
│   │   ├── crystalpay.py   # CrystalPay payment
│   │   └── cryptobot.py    # CryptoBot payment
│   ├── static/         # CSS, JS, images
│   └── templates/      # Jinja2 HTML templates
└── requirements.txt
```

## How to Run
The application runs automatically via the configured workflow:
```
cd smm_site && python -c "import uvicorn; uvicorn.run('app.main:app', host='0.0.0.0', port=5000, reload=True)"
```

## Technologies
- **Framework**: FastAPI
- **Template Engine**: Jinja2
- **Server**: Uvicorn
- **Language**: Python 3.11

## Key Endpoints
- `/` - Homepage with services
- `/orders` - Order management
- `/statistics` - Statistics page
- `/create_order` - Create new order (POST)
- `/create_invoice` - Create payment invoice (POST)
- `/health` - Health check endpoint

## Recent Changes
- 2026-01-02: Initial import to Replit, configured for port 5000
- 2026-04-30: Spring redesign — sakura petals replace snow, pink/lavender gradient brand,
  prettier burger button, restyled brand-link with logo + "SMM PANEL" tagline.
  Real top-up system added (CrystalPay + CryptoBot) with invoices table, success page and
  webhook endpoints. Premium purchase modal with calculator. Live-balance refresh via
  /api/balance every 15s + on focus/visibility, displayed everywhere via [data-balance-value].
- 2026-05-01: Mobile navigation redesigned:
  - Sticky top bar: brand logo + "Boostix" + balance pill (clickable → opens topup modal) + burger (☰)
  - Burger opens slide-in drawer from the right with all nav links (Главная, Заказы, Статистика, etc.) + theme toggle
  - Removed "Пополнить баланс" button from mobile — clicking balance pill opens the topup modal
  - Service cards no longer show min/max/price-per-1000 in the list (shown only in the purchase modal)
  - html { background: var(--bg-1) } + background-attachment: fixed to prevent white bars on mobile
  - `openTopupBtn` is now the balance pill button (mobile); `openTopupBtnSidebar` is desktop sidebar

## User Preferences
- Currency displayed as ₽
- Spring season: sakura petals animation, pink/purple palette
- Pagination strict (5 services initially, "Показать ещё" loads 5 more)
- Real (non-demo) top-up flow expected
