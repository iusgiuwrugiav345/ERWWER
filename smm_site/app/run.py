import uvicorn
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "smm_site"))

# Теперь можно импортировать app
from app.main import app

import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8080, reload=True)
