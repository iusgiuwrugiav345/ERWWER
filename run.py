import uvicorn
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "smm_site"))

from app.main import app

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=5000, reload=True)
