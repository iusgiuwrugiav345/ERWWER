# ...existing code...
from fastapi import FastAPI, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI
from .site import router   # ← ВОТ КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ

app = FastAPI()
app.include_router(router)

# ...existing code...
app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok"}

# Статика для CSS/JS
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.head("/")
async def root_head():
    return Response(status_code=200)

@app.get("/favicon.ico")
async def favicon():
    return FileResponse("app/static/favicon.ico")

# Подключаем маршруты
# ...existing code...
app.include_router(site.router)
# ...existing code...


