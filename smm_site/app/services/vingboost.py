import requests
from app.config import VINGBOOST_API_KEY

BASE_URL = "https://vingboost.ru/api/v2"

def map_service_to_social(service_name):
    name = service_name.lower()
    if "instagram" in name:
        return "instagram"
    elif "telegram" in name:
        return "telegram"
    elif "twitter" in name:
        return "twitter"
    elif "facebook" in name:
        return "facebook"
    elif "youtube" in name:
        return "youtube"
    elif "tiktok" in name:
        return "tiktok"
    else:
        return "default"


def map_service_to_category(service_name):
    name = service_name.lower()
    if "просмотр" in name or "view" in name or "views" in name:
        return "views"
    if "подпис" in name or "subscrib" in name or "followers" in name:
        return "followers"
    if "лайк" in name or "like" in name:
        return "likes"
    if "репост" in name or "repost" in name or "share" in name:
        return "reposts"
    return "other"

def get_services():
    url = f"{BASE_URL}?action=services&key={VINGBOOST_API_KEY}"
    r = requests.get(url)
    if r.status_code == 200:
        services = r.json()
        # добавляем поле social каждому сервису
        for s in services:
            s["social"] = map_service_to_social(s["name"])
            s["category"] = map_service_to_category(s["name"])
        return services
    return []

def create_order(service_id, link, quantity):
    url = f"{BASE_URL}?action=add&service={service_id}&link={link}&quantity={quantity}&key={VINGBOOST_API_KEY}"
    r = requests.get(url)
    if r.status_code == 200:
        return r.json()
    return {}

def get_balance():
    url = f"{BASE_URL}?action=balance&key={VINGBOOST_API_KEY}"
    r = requests.get(url)
    if r.status_code == 200:
        return r.json()
    return {"balance": 0, "currency": "USD"}
