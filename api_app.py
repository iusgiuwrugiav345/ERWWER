from flask import Flask, jsonify, request, send_from_directory
from database import db
import config


app = Flask(__name__, static_folder="webapp", static_url_path="/webapp")


def _item_from_row(row):
    name, url, content_type, category, version, updated, genre, developer, size = row
    item_id = db.get_game_id_by_name(name)
    avg_rating, rating_count = db.get_game_rating_stats(name)
    return {
        "id": item_id,
        "name": name,
        "type": content_type,
        "category": category,
        "version": version,
        "updated": updated,
        "genre": genre,
        "developer": developer,
        "size": size,
        "download_url": url if isinstance(url, str) and url.startswith("http") else None,
        "download_source": "url" if isinstance(url, str) and url.startswith("http") else "telegram_or_local",
        "icon_url": None,
        "description": "",
        "rating_avg": round(avg_rating, 1) if avg_rating else 0.0,
        "rating_count": rating_count or 0,
        "screenshots": db.get_screenshots(item_id, limit=10) if item_id else [],
    }


def _is_admin_request():
    admin_key = request.headers.get("X-Admin-Key", "")
    return admin_key and admin_key == getattr(config, "ADMIN_API_KEY", "")


@app.get("/api/health")
def health():
    return jsonify({"ok": True})


@app.get("/api/items")
def list_items():
    q = request.args.get("q", "").strip().lower()
    content_type = request.args.get("type", "").strip().lower()
    category = request.args.get("category", "").strip().lower()
    limit = min(max(int(request.args.get("limit", 20)), 1), 100)
    offset = max(int(request.args.get("offset", 0)), 0)

    rows = db.get_all_games()
    items = []
    for row in rows:
        name, url, row_type, row_category, version, updated, genre, developer, size = row
        if q and q not in name.lower():
            continue
        if content_type and row_type.lower() != content_type:
            continue
        if category and row_category.lower() != category:
            continue
        items.append(_item_from_row(row))

    total = len(items)
    items = items[offset:offset + limit]
    return jsonify({"items": items, "total": total, "limit": limit, "offset": offset})


@app.get("/api/items/<int:item_id>")
def item_details(item_id):
    row = db.get_game_by_id(item_id)
    if not row:
        return jsonify({"error": "not_found"}), 404
    return jsonify(_item_from_row(row))


@app.post("/api/admin/items")
def admin_add_item():
    if not _is_admin_request():
        return jsonify({"error": "forbidden"}), 403

    payload = request.get_json(silent=True) or {}
    name = str(payload.get("name", "")).strip()
    url = str(payload.get("url", "")).strip()
    content_type = str(payload.get("type", "game")).strip() or "game"
    category = str(payload.get("category", "other")).strip() or "other"
    version = str(payload.get("version", "N/A")).strip() or "N/A"
    updated = str(payload.get("updated", "N/A")).strip() or "N/A"
    genre = str(payload.get("genre", "N/A")).strip() or "N/A"
    developer = str(payload.get("developer", "N/A")).strip() or "N/A"
    size = str(payload.get("size", "N/A")).strip() or "N/A"

    if not name or not url:
        return jsonify({"error": "name_and_url_required"}), 400

    ok = db.add_game(name, url, content_type, category, version, updated, genre, developer, size)
    if not ok:
        return jsonify({"error": "save_failed"}), 500

    item_id = db.get_game_id_by_name(name)
    return jsonify({"ok": True, "id": item_id})


@app.post("/api/admin/items/<int:item_id>/screenshots")
def admin_add_screenshots(item_id):
    if not _is_admin_request():
        return jsonify({"error": "forbidden"}), 403
    if not db.game_exists_by_id(item_id):
        return jsonify({"error": "not_found"}), 404

    payload = request.get_json(silent=True) or {}
    file_ids = payload.get("file_ids", [])
    if not isinstance(file_ids, list) or not file_ids:
        return jsonify({"error": "file_ids_required"}), 400

    added = 0
    for file_id in file_ids[:20]:
        if isinstance(file_id, str) and file_id.strip():
            if db.add_screenshot(item_id, file_id.strip()):
                added += 1
    return jsonify({"ok": True, "added": added})


@app.get("/webapp")
def webapp_index():
    return send_from_directory("webapp", "index.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)
