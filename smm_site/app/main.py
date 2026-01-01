from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

# Import routes using package path
from app.routes import site

app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok"}
  
# Статика для CSS/JS
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Подключаем маршруты
app.include_router(site.router)

