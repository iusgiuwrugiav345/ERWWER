from flask import Flask, jsonify, request, send_from_directory, Response
from urllib.parse import quote
from urllib.parse import unquote
import requests
from database import db
import config


app = Flask(__name__, static_folder="webapp", static_url_path="/webapp")


def _build_direct_download_url(raw_url):
    """Resolves a download URL for Mini App direct downloads."""
    if not isinstance(raw_url, str):
        return None
    raw_url = raw_url.strip()
    if not raw_url:
        return None
    if raw_url.startswith("http://") or raw_url.startswith("https://"):
        return raw_url

    # r2://key or r2://bucket/key -> https://<public-base>/<key>
    if raw_url.startswith("r2://"):
        base = str(getattr(config, "R2_PUBLIC_BASE_URL", "") or "").strip().rstrip("/")
        if not base:
            return None
        path = raw_url[5:].strip("/")
        if not path:
            return None
        bucket = str(getattr(config, "R2_BUCKET", "") or "").strip()
        if bucket and path.startswith(f"{bucket}/"):
            path = path[len(bucket) + 1:]
        if not path:
            return None
        encoded_path = "/".join(quote(part) for part in path.split("/"))
        return f"{base}/{encoded_path}"
    return None


def _item_from_row(row):
    item_id, name, url, content_type, category, version, updated, genre, developer, size = row
    avg_rating, rating_count = db.get_game_rating_stats(name)
    direct_url = _build_direct_download_url(url)
    raw_shots = db.get_screenshots(item_id, limit=10) if item_id else []
    screenshots = []
    for shot in raw_shots:
        if isinstance(shot, str) and (shot.startswith("http://") or shot.startswith("https://")):
            screenshots.append(shot)
        elif isinstance(shot, str) and shot.strip():
            screenshots.append(f"/api/media/telegram/{quote(shot.strip(), safe='')}")
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
        "download_url": direct_url,
        "download_source": "url_or_r2" if direct_url else "telegram_or_local",
        "icon_url": None,
        "description": "",
        "rating_avg": round(avg_rating, 1) if avg_rating else 0.0,
        "rating_count": rating_count or 0,
        "screenshots": screenshots,
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

    rows = db.get_all_games_with_id()
    items = []
    for row in rows:
        item_id, name, url, row_type, row_category, version, updated, genre, developer, size = row
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
    game_row = db.get_game_by_id(item_id)
    if not game_row:
        return jsonify({"error": "not_found"}), 404
    row = (item_id, *game_row)
    return jsonify(_item_from_row(row))


@app.get("/api/items/<int:item_id>/download")
def item_download(item_id):
    game_row = db.get_game_by_id(item_id)
    if not game_row:
        return jsonify({"error": "not_found"}), 404

    name, raw_url, *_ = game_row
    direct_url = _build_direct_download_url(raw_url)
    if direct_url:
        return jsonify({"mode": "direct", "url": direct_url})

    bot_username = str(getattr(config, "BOT_USERNAME", "") or "").strip().lstrip("@")
    if not bot_username:
        bot_username = "icorevault_bot"
    return jsonify({
        "mode": "bot",
        "url": f"https://t.me/{bot_username}?start=dl_{item_id}",
        "reason": "telegram_file_id_or_local_path"
    })


@app.get("/api/media/telegram/<path:file_id_encoded>")
def telegram_media_proxy(file_id_encoded):
    file_id = unquote(file_id_encoded or "").strip()
    token = str(getattr(config, "TOKEN", "") or "").strip()
    if not file_id or not token:
        return jsonify({"error": "bad_request"}), 400

    try:
        meta = requests.get(
            f"https://api.telegram.org/bot{token}/getFile",
            params={"file_id": file_id},
            timeout=10
        )
        meta_data = meta.json() if meta.ok else {}
        file_path = ((meta_data.get("result") or {}).get("file_path") or "").strip()
        if not file_path:
            return jsonify({"error": "not_found"}), 404

        media = requests.get(
            f"https://api.telegram.org/file/bot{token}/{file_path}",
            timeout=20
        )
        if not media.ok:
            return jsonify({"error": "download_failed"}), 502

        mime = media.headers.get("Content-Type", "image/jpeg")
        return Response(
            media.content,
            mimetype=mime,
            headers={"Cache-Control": "public, max-age=3600"}
        )
    except Exception:
        return jsonify({"error": "proxy_failed"}), 500


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
