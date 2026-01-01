
from fastapi import FastAPI, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# Импортируем роутер из правильного места
from app.routes.site import router as site_router


app = FastAPI()


@app.get("/health")
def health():
    return {"status": "ok"}


# Статика для CSS/JS
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.head("/health")
async def health_head():
    return Response(status_code=200)


@app.get("/favicon.ico")
async def favicon():
    return FileResponse("app/static/favicon.ico")


# Подключаем маршруты
app.include_router(site_router)


