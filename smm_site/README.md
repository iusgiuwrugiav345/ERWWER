# SMM Site — Deploy to Render

Краткие инструкции для деплоя этого проекта на Render.

## Рекомендуемая команда старта
- Используется модуль `app` как пакет приложения.

Start command (в Render Service Settings или в `render.yaml`):

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Альтернатива (если хотите использовать путь `smm_site.app.main:app`):

```bash
uvicorn smm_site.app.main:app --host 0.0.0.0 --port $PORT
```

Я добавил совместимость для `smm_site` в репозитории, так что оба варианта работают.

## Зависимости
- В корне проекта есть `requirements.txt` — Render установит зависимости в процессе сборки.
- Если вы используете другой файл, укажите `pip install -r <file>` в `buildCommand`.

## Пример `render.yaml`
- В репо уже есть `render.yaml` с примерной конфигурацией. Если вы хотите изменить имя сервиса или регион — отредактируйте файл.

## Локальная проверка перед деплоем
1. Создайте виртуальное окружение и установите зависимости:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Запустите сервер локально:

```powershell
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

3. Быстрая проверка импорта (без запуска сервера):

```powershell
.venv\Scripts\python -c "import importlib; importlib.import_module('smm_site.app.main'); print('IMPORT_OK')"
```

## Переменные окружения
- Если вам нужны ключи API или другие секреты — добавьте их в Render → Environment → Variables.

## Git команды для отправки изменений

```bash
git add requirements.txt render.yaml smm_site/ README.md
git commit -m "Prepare for Render: add render config and README"
git push
```

Если нужно — могу добавить больше инструкций (например, about migrations, DB, или CI).
