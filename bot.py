import asyncio
import base64
import logging
import os
from datetime import datetime
from aiogram.types import CallbackQuery
import aiohttp
import requests
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import (InlineKeyboardMarkup, InlineKeyboardButton,
                           ReplyKeyboardMarkup, KeyboardButton, InputMediaPhoto,
                           LabeledPrice)
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import config
from database import db
from keep_alive import keep_alive

keep_alive()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=config.TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

class SuggestionStates(StatesGroup):
    waiting_for_suggestion = State()

class ReportStates(StatesGroup):
    waiting_for_comment = State()

class AddPhotosState(StatesGroup):
    waiting_photos = State()

class AddIpaState(StatesGroup):
    waiting_file = State()
    waiting_meta = State()

CRYPTOBOT_API_URL = "https://pay.crypt.bot/api/"


def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[
            KeyboardButton(text="💎 Купить подписку"),
            KeyboardButton(text="👤 Мой профиль")
        ],
                  [
                      KeyboardButton(text="📜 История скачиваний"),
                      KeyboardButton(text="❣️ Помощь")
                  ],
                  [
                      KeyboardButton(text="№️ О Нас"),
                      KeyboardButton(text="💡 Предложить игру")
                  ]],
        resize_keyboard=True,
        input_field_placeholder="Введите название игры...")
    return keyboard

def get_catalog_webapp_keyboard():
    url = getattr(config, "MINI_APP_URL", "").strip()
    if not url or "example.com" in url:
        return None
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Открыть каталог", web_app=types.WebAppInfo(url=url))]
    ])


def parse_suggestion_text(text: str):
    name = text.strip()
    url = ""

    if "|" in text:
        parts = [part.strip() for part in text.split("|", 1)]
        name = parts[0] or name
        url = parts[1] if len(parts) > 1 else ""
    else:
        http_idx = text.find("http://")
        https_idx = text.find("https://")
        indices = [idx for idx in [http_idx, https_idx] if idx != -1]
        if indices:
            idx = min(indices)
            name = text[:idx].strip(" -\\n") or name
            url = text[idx:].strip()

    return name, url


def _encode_game_token(name: str) -> str:
    token = base64.urlsafe_b64encode(name.lower().encode("utf-8")).decode("ascii")
    return token.rstrip("=")


def _decode_game_token(token: str) -> str:
    padding = "=" * (-len(token) % 4)
    return base64.urlsafe_b64decode(token + padding).decode("utf-8")


def _rating_buttons(game_name: str):
    token = _encode_game_token(game_name)
    return [InlineKeyboardButton(text=f"{i}⭐", callback_data=f"rate|{i}|{token}") for i in range(1, 6)]


def get_game_keyboard(game_name: str, item_id: int | None = None) -> InlineKeyboardMarkup:
    token = _encode_game_token(game_name)
    photos_id = item_id if item_id is not None else 0
    return InlineKeyboardMarkup(inline_keyboard=[
        _rating_buttons(game_name),
        [InlineKeyboardButton(text="📸 Скриншоты", callback_data=f"photos:{photos_id}")],
        [InlineKeyboardButton(text="⋯ Ещё", callback_data=f"more|{token}")]
    ])


def get_more_keyboard(game_name: str) -> InlineKeyboardMarkup:
    token = _encode_game_token(game_name)
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚠️ Сообщить о проблеме", callback_data=f"report|{token}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data=f"back|{token}")]
    ])


def get_report_type_keyboard(game_name: str) -> InlineKeyboardMarkup:
    token = _encode_game_token(game_name)
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Не запускается", callback_data=f"report_type|not_start|{token}")],
        [InlineKeyboardButton(text="🔗 Битая ссылка", callback_data=f"report_type|bad_link|{token}")],
        [InlineKeyboardButton(text="📦 Не та версия", callback_data=f"report_type|wrong_ver|{token}")],
        [InlineKeyboardButton(text="🦠 Подозрение на вирус", callback_data=f"report_type|virus|{token}")],
        [InlineKeyboardButton(text="✍️ Другая проблема", callback_data=f"report_type|other|{token}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data=f"back|{token}")]
    ])


def format_rating_line(game_name: str) -> str:
    avg_rating, count = db.get_game_rating_stats(game_name)
    virtual_avg, virtual_count = db.get_virtual_rating(game_name)
    real_count = count or 0
    real_avg = avg_rating or 0.0
    total_count = real_count + virtual_count
    if total_count <= 0:
        return "⭐ Рейтинг: нет оценок"
    total_sum = (real_avg * real_count) + (virtual_avg * virtual_count)
    total_avg = total_sum / total_count
    return f"⭐ Рейтинг: {total_avg:.1f} из 5 ({total_count})"



def _get_admin_chat_id():
    if hasattr(config, "ADMIN_CHAT_ID"):
        return config.ADMIN_CHAT_ID
    admins = getattr(config, "ADMINS", [])
    return admins[0] if admins else None


def _get_game_meta(game_name: str):
    game = db.get_game_by_name(game_name)
    if not game:
        return "game", "N/A"
    content_type = game[2] if len(game) > 2 else "game"
    version = game[4] if len(game) > 4 else "N/A"
    return content_type, version


def _report_type_label(code: str) -> str:
    mapping = {
        "not_start": "Не запускается",
        "bad_link": "Битая ссылка",
        "wrong_ver": "Не та версия",
        "virus": "Подозрение на вирус",
        "other": "Другая проблема",
    }
    return mapping.get(code, code)

@dp.message_handler(commands=['start'], state="*")
async def start(message: types.Message, state: FSMContext):
    await state.finish()
    args = message.get_args().strip()
    if args.startswith("dl_") and args[3:].isdigit():
        item_id = int(args[3:])
        game = db.get_game_by_id(item_id)
        if not game:
            return await message.answer("❌ Игра не найдена")

        name, url, content_type, category, version, updated, genre, developer, size = game
        rating_line = format_rating_line(name)
        details_text = (
            f"🎮 Игра: {name}\n"
            f"📦 Версия: {version}\n"
            f"🗓 Обновлено: {updated}\n"
            f"🎮 Жанр: {genre}\n"
            f"👤 Разработчик: {developer}\n"
            f"⚖️ Размер: {size}\n\n"
            f"{rating_line}"
        )
        if isinstance(url, str) and url.startswith("http"):
            try:
                return await message.answer_document(url.strip(), caption=details_text)
            except Exception:
                return await message.answer(
                    f"{details_text}\nDownload: {url}",
                    disable_web_page_preview=True
                )
        if isinstance(url, str) and os.path.exists(url):
            file = types.InputFile(url)
            return await message.answer_document(file, caption=details_text)
        if isinstance(url, str) and url.strip():
            try:
                return await message.answer_document(url.strip(), caption=details_text)
            except Exception:
                pass
        return await message.answer("❌ Файл недоступен")

    try:
        photo = types.InputFile("attached_assets/IMG_3677.jpg")
        catalog_markup = get_catalog_webapp_keyboard()
        await message.answer_photo(
            photo=photo,
            caption=("👋 Привет! Я бот для скачивания .IPA файлов\n\n"
                     "🎮 Отправь название игры, чтобы найти её\n"
                     "👤 /profile - посмотреть профиль\n"
                     "💳 /buy - купить премиум-подписку\n"
                     "🛍 /catalog - открыть Mini App каталог\n"
                     "💻 @iCoreapp - наш канал"
                    ),
            reply_markup=catalog_markup or get_main_keyboard())
    except Exception as e:
        logger.error(f"Start command error: {e}")
        await message.answer(
            "👋 Привет! Я бот для скачивания .IPA файлов\n\n"
            "🎮 Отправь название игры, чтобы найти её\n"
            "👤 /profile - посмотреть профиль\n"
            "💳 /buy - купить премиум-подписку\n",
            reply_markup=get_main_keyboard())

@dp.message_handler(commands=['catalog'], state="*")
async def open_catalog(message: types.Message, state: FSMContext):
    await state.finish()
    markup = get_catalog_webapp_keyboard()
    if not markup:
        return await message.answer("Mini App URL не настроен в config.MINI_APP_URL")
    await message.answer("Открой каталог:", reply_markup=markup)

@dp.message_handler(commands=['profile'], state="*")
async def show_profile(message: types.Message, state: FSMContext):
    await state.finish()
    try:
        user = db.get_user(message.from_user.id)
        if not user:
            db.create_user(message.from_user.id)
            user = db.get_user(message.from_user.id)

        status = "🌟 Premium" if user[2] else "👤 Обычный"
        downloads = "♾️ Безлимит" if user[2] else f"📥 {user[1]} загрузок осталось"
        last_active = user[3].split('.')[0] if '.' in user[3] else user[3]

        profile_text = (f"👤 Имя: {message.from_user.first_name}\n"
                        f"🆔 ID: {user[0]}\n"
                        f"📊 Статус: {status}\n"
                        f"{downloads}\n"
                        f"📅 Последняя активность: {last_active}")

        try:
            photo = types.InputFile("attached_assets/4163666.jpg")
            await message.answer_photo(photo=photo, caption=profile_text)
        except Exception:
            await message.answer(profile_text)
    except Exception as e:
        logger.error(f"Profile error: {e}")
        await message.answer("❌ Ошибка при получении профиля")

@dp.message_handler(commands=['history'], state="*")
async def show_history(message: types.Message, state: FSMContext):
    await state.finish()
    downloads = db.get_user_downloads(message.from_user.id)

    if not downloads:
        await message.answer("❌ Вы еще ничего не скачивали")
        return

    history_text = "📜 Ваша история скачиваний (последние 5)\n\n"
    for i, (game, date, url) in enumerate(downloads[-5:], 1):
        formatted_date = date.split('.')[0] if '.' in date else date
        history_text += (f"{i}️⃣ {game}\n"
                         f"📅 Дата: {formatted_date}\n"
                         f"📥 Ссылка: {url}\n\n")

    await message.answer(history_text)

async def create_invoice(user_id: int, amount: float = 1.0, currency: str = "USDT"):
    async with aiohttp.ClientSession() as session:
        async with session.post(
                CRYPTOBOT_API_URL + "createInvoice",
                headers={"Crypto-Pay-API-Token": config.CRYPTOBOT_API},
                json={
                    "amount": amount,
                    "asset": currency,
                    "description": f"Subscription purchase for user {user_id}",
                    "hidden_message": "Thanks for Premium purchase!",
                    "paid_btn_name": "callback",
                    "paid_btn_url": "https://t.me/yourbotusername"
                }) as resp:
            data = await resp.json()
            return data["result"]["pay_url"] if data.get("ok") else None

@dp.message_handler(commands=['buy'], state="*")
async def buy(message: types.Message, state: FSMContext):
    await state.finish()
    pay_url = await create_invoice(message.from_user.id, amount=config.PRICE, currency="USDT")
    stars_price = getattr(config, "STARS_PRICE", 30)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"⭐ Оплатить {stars_price} звёзд", callback_data="buy_stars")],
    ])
    if pay_url:
        keyboard.add(InlineKeyboardButton(text=f"💎 CryptoBot {config.PRICE} USDT", url=pay_url))
        keyboard.add(InlineKeyboardButton(text="✅ Проверить оплату", callback_data="check_payment"))

    try:
        photo = types.InputFile("attached_assets/IMG_3564.jpeg")
        await message.answer_photo(
            photo=photo,
            caption=("🎉 *Премиум-подписка* 🎉\n\n"
                     "🚀 *Преимущества:*\n"
                     "✔ Безлимитное скачивание\n"
                     "✔ Доступ к эксклюзивным приложениям\n"
                     "✔ Приоритетная поддержка\n\n"
                     "💳 *Способы оплаты:*\n"
                     f"⭐ `{stars_price}` звёзд Telegram\n"
                     f"💎 `{config.PRICE} USDT` через CryptoBot\n\n"
                     "👇 *Выберите способ оплаты:*"),
            reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Buy command error: {e}")
        await message.answer("❌ Ошибка при отправке фото")

@dp.callback_query_handler(lambda c: c.data == "check_payment", state="*")
async def check_payment(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    async with aiohttp.ClientSession() as session:
        async with session.get(
                CRYPTOBOT_API_URL + "getInvoices",
                headers={"Crypto-Pay-API-Token": config.CRYPTOBOT_API},
        ) as resp:
            data = await resp.json()
            if not data.get("ok"):
                return await callback_query.message.answer("⚠ Ошибка при проверке оплаты")

            invoices = data["result"]["items"]
            user_invoices = [inv for inv in invoices if str(callback_query.from_user.id) in inv.get("description", "")]

            if any(inv["status"] == "paid" for inv in user_invoices):
                db.set_premium(callback_query.from_user.id, True)
                await callback_query.message.answer("✅ Оплата прошла успешно! Вам активирован Premium 🚀")
            else:
                await callback_query.message.answer("❌ Оплата пока не найдена. Попробуйте позже.")

@dp.callback_query_handler(lambda c: c.data == "buy_stars", state="*")
async def buy_stars(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    stars_price = int(getattr(config, "STARS_PRICE", 30))
    try:
        await bot.send_invoice(
            chat_id=callback_query.from_user.id,
            title="Премиум-подписка",
            description="Безлимитное скачивание и приоритетная поддержка.",
            payload=f"premium_stars:{callback_query.from_user.id}",
            provider_token="",
            currency="XTR",
            prices=[LabeledPrice(label=f"Премиум {stars_price} ⭐", amount=stars_price)],
        )
    except Exception as e:
        logger.error(f"Stars invoice error: {e}")
        await callback_query.message.answer("❌ Не удалось создать счёт в звёздах.")
    await callback_query.answer()

@dp.pre_checkout_query_handler(lambda q: True)
async def pre_checkout(pre_checkout_query: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@dp.message_handler(content_types=types.ContentType.SUCCESSFUL_PAYMENT)
async def successful_stars_payment(message: types.Message):
    payment = message.successful_payment
    if payment.currency != "XTR":
        return
    if not payment.invoice_payload.startswith("premium_stars"):
        return
    db.set_premium(message.from_user.id, True)
    await message.answer("✅ Оплата звёздами прошла успешно! Premium активирован.")

@dp.callback_query_handler(lambda c: c.data.startswith("download_"), state="*")
async def handle_recommendation_download(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    game_name = callback_query.data.replace("download_", "")
    games = db.get_all_games()
    found_game = None

    for game in games:
        if game[0].lower() == game_name.lower():
            found_game = game
            break

    if not found_game:
        await callback_query.answer("❌ Игра не найдена", show_alert=True)
        return

    name, url, content_type = found_game[0], found_game[1], found_game[2]
    rating_line = format_rating_line(name)
    item_id = db.get_game_id_by_name(name)
    
    try:
        download_success = False
        if url.startswith('http'):
            try:
                response = requests.head(url, timeout=5)
                if response.status_code == 200:
                    type_text = "Игра" if content_type == "game" else "Приложение"
                    await callback_query.message.answer(
                        f"{type_text}: {name}\n{rating_line}\n📥 Ссылка для скачивания: {url}",
                        reply_markup=get_game_keyboard(name, item_id)
                    )
                    download_success = True
                else:
                    raise Exception("File not available")
            except Exception:
                await callback_query.message.answer("❌ Извините, файл игры в данный момент недоступен.")
                return
        elif os.path.exists(url):
            file = types.InputFile(url)
            sent_file = await callback_query.message.answer_document(
                file,
                caption=f"🎮 Игра: {name}\n{rating_line}",
                reply_markup=get_game_keyboard(name, item_id)
            )
            await callback_query.message.answer(
                f"🆔 File ID: `{sent_file.document.file_id}`",
                parse_mode="Markdown"
            )
            download_success = True
        elif isinstance(url, str) and url.strip():
            sent_file = await callback_query.message.answer_document(
                url.strip(),
                caption=f"🎮 Игра: {name}\n{rating_line}",
                reply_markup=get_game_keyboard(name, item_id)
            )
            await callback_query.message.answer(
                f"🆔 File ID: `{sent_file.document.file_id}`",
                parse_mode="Markdown"
            )
            download_success = True
        else:
            await callback_query.message.answer("❌ Файл игры не найден.")

        if download_success:
            db.add_download(callback_query.from_user.id, name)
            recommendations = db.get_game_recommendations(name, limit=3)
            if recommendations:
                rec_keyboard = InlineKeyboardMarkup()
                for rec_game in recommendations:
                    rec_keyboard.add(InlineKeyboardButton(text=f"📥 {rec_game.title()}", callback_data=f"download_{rec_game}"))
                await callback_query.message.answer("🎯 *Вам также может понравиться:*", parse_mode="Markdown", reply_markup=rec_keyboard)
    except Exception as e:
        logger.error(f"Download error: {e}")
        await callback_query.message.answer("❌ Ошибка при загрузке файла.")
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data.startswith("rate|"), state="*")
async def handle_rate_game(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    parts = callback_query.data.split("|", 2)
    if len(parts) != 3:
        return await callback_query.answer("Ошибка оценки", show_alert=True)

    rating_text, token = parts[1], parts[2]
    if not rating_text.isdigit():
        return await callback_query.answer("Неверная оценка", show_alert=True)

    rating = int(rating_text)
    if rating < 1 or rating > 5:
        return await callback_query.answer("Неверная оценка", show_alert=True)

    try:
        game_name = _decode_game_token(token)
    except Exception:
        return await callback_query.answer("Ошибка игры", show_alert=True)

    saved = db.add_or_update_rating(callback_query.from_user.id, game_name, rating)
    if not saved:
        return await callback_query.answer("Не удалось сохранить оценку", show_alert=True)

    rating_line = format_rating_line(game_name)
    await callback_query.answer("Спасибо! Оценка сохранена.")
    await callback_query.message.answer(f"⭐ Вы поставили {rating}/5\n{rating_line}")

@dp.callback_query_handler(lambda c: c.data.startswith("more|"), state="*")
async def handle_more_menu(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    try:
        _, token = callback_query.data.split("|", 1)
        game_name = _decode_game_token(token)
        await callback_query.message.edit_reply_markup(reply_markup=get_more_keyboard(game_name))
    except Exception:
        await callback_query.answer("Ошибка меню", show_alert=True)
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data.startswith("back|"), state="*")
async def handle_more_back(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    try:
        _, token = callback_query.data.split("|", 1)
        game_name = _decode_game_token(token)
        item_id = db.get_game_id_by_name(game_name)
        await callback_query.message.edit_reply_markup(reply_markup=get_game_keyboard(game_name, item_id))
    except Exception:
        await callback_query.answer("Ошибка меню", show_alert=True)
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data.startswith("report|"), state="*")
async def handle_report_menu(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    try:
        _, token = callback_query.data.split("|", 1)
        game_name = _decode_game_token(token)
        await callback_query.message.edit_reply_markup(reply_markup=get_report_type_keyboard(game_name))
    except Exception:
        await callback_query.answer("Ошибка репорта", show_alert=True)
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data.startswith("report_type|"), state="*")
async def handle_report_type(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    parts = callback_query.data.split("|", 2)
    if len(parts) != 3:
        return await callback_query.answer("Ошибка репорта", show_alert=True)

    type_code, token = parts[1], parts[2]
    try:
        game_name = _decode_game_token(token)
    except Exception:
        return await callback_query.answer("Ошибка игры", show_alert=True)

    if type_code == "other":
        await state.update_data(game_name=game_name, problem_type=type_code)
        await ReportStates.waiting_for_comment.set()
        await callback_query.message.answer("✍️ Опишите проблему сообщением.")
        return await callback_query.answer()

    content_type, version = _get_game_meta(game_name)
    report_ok = db.add_report(
        callback_query.from_user.id,
        game_name,
        version,
        _report_type_label(type_code),
        ""
    )

    if not report_ok:
        return await callback_query.answer("Вы уже отправляли репорт", show_alert=True)

    admin_chat_id = _get_admin_chat_id()
    if admin_chat_id:
        type_text = "Игра" if content_type == "game" else "Приложение"
        comment = "-"
        time_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        user = callback_query.from_user
        username = f"@{user.username}" if user.username else user.full_name
        report_text = (
            "⚠️ Новый репорт\n"
            f"📦 Тип: {type_text}\n"
            f"🎮 Название: {game_name}\n"
            f"🔢 Версия: {version or '?'}\n"
            f"❗ Проблема: {_report_type_label(type_code)}\n"
            f"📝 Коммент: {comment}\n"
            f"👤 От: {username} (ID: {user.id})\n"
            f"⏰ Время: {time_text}"
        )
        try:
            await bot.send_message(admin_chat_id, report_text)
        except Exception:
            pass

    await callback_query.answer("Репорт отправлен ✅", show_alert=True)

@dp.message_handler(state=ReportStates.waiting_for_comment)
async def handle_report_comment(message: types.Message, state: FSMContext):
    data = await state.get_data()
    game_name = data.get("game_name")
    problem_type = data.get("problem_type", "other")
    comment = message.text.strip() if message.text else ""

    await state.finish()

    if not game_name:
        return await message.answer("Ошибка: игра не найдена.")

    content_type, version = _get_game_meta(game_name)
    report_ok = db.add_report(
        message.from_user.id,
        game_name,
        version,
        _report_type_label(problem_type),
        comment
    )

    if not report_ok:
        return await message.answer("Вы уже отправляли репорт по этой версии.")

    admin_chat_id = _get_admin_chat_id()
    if admin_chat_id:
        type_text = "Игра" if content_type == "game" else "Приложение"
        time_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        username = f"@{message.from_user.username}" if message.from_user.username else message.from_user.full_name
        report_text = (
            "⚠️ Новый репорт\n"
            f"📦 Тип: {type_text}\n"
            f"🎮 Название: {game_name}\n"
            f"🔢 Версия: {version or '?'}\n"
            f"❗ Проблема: {_report_type_label(problem_type)}\n"
            f"📝 Коммент: {comment or '-'}\n"
            f"👤 От: {username} (ID: {message.from_user.id})\n"
            f"⏰ Время: {time_text}"
        )
        try:
            await bot.send_message(admin_chat_id, report_text)
        except Exception:
            pass

    await message.answer("Спасибо! Репорт отправлен ✅")

# ---------------- SCREENSHOTS ----------------
@dp.callback_query_handler(lambda c: c.data.startswith("photos:"), state="*")
async def show_screenshots(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    try:
        _, item_id_text = callback_query.data.split(":", 1)
        if not item_id_text.isdigit():
            return await callback_query.answer("Неверный ID", show_alert=True)

        item_id = int(item_id_text)
        if not db.game_exists_by_id(item_id):
            await callback_query.message.answer("Такой записи нет")
            return await callback_query.answer()

        files = db.get_screenshots(item_id, limit=10)
        if not files:
            await callback_query.message.answer("Скриншотов пока нет")
            return await callback_query.answer()

        if len(files) == 1:
            await callback_query.message.answer_photo(files[0])
        else:
            media = [InputMediaPhoto(file_id) for file_id in files]
            await bot.send_media_group(chat_id=callback_query.message.chat.id, media=media)
    finally:
        await callback_query.answer()


@dp.message_handler(commands=['add_photos'], state="*")
async def add_photos_command(message: types.Message, state: FSMContext):
    await state.finish()
    if message.from_user.id not in config.ADMINS:
        return

    args = message.get_args().strip()
    if not args:
        await AddPhotosState.waiting_photos.set()
        await state.update_data(item_id=None, count=0)
        return await message.answer("Отправь ID записи (item_id).")

    if not args.isdigit():
        return await message.answer("Неверный ID")

    item_id = int(args)
    if not db.game_exists_by_id(item_id):
        return await message.answer("Такой записи нет")

    await AddPhotosState.waiting_photos.set()
    await state.update_data(item_id=item_id, count=0)
    await message.answer("Отправь до 5 фото (скриншоты). Когда закончишь — напиши /done")


@dp.message_handler(commands=['done'], state=AddPhotosState.waiting_photos)
async def add_photos_done(message: types.Message, state: FSMContext):
    if message.from_user.id not in config.ADMINS:
        return
    data = await state.get_data()
    count = data.get("count", 0)
    await state.finish()
    await message.answer(f"Готово! Добавлено {count} фото")


@dp.message_handler(state=AddPhotosState.waiting_photos, content_types=types.ContentTypes.ANY)
async def add_photos_handler(message: types.Message, state: FSMContext):
    if message.from_user.id not in config.ADMINS:
        return

    data = await state.get_data()
    item_id = data.get("item_id")
    count = data.get("count", 0)

    if message.text and message.text.strip().lower() == "/done":
        await add_photos_done(message, state)
        return

    if item_id is None:
        if message.text and message.text.isdigit():
            item_id = int(message.text)
            if not db.game_exists_by_id(item_id):
                return await message.answer("Такой записи нет")
            await state.update_data(item_id=item_id, count=0)
            return await message.answer("Отправь до 5 фото (скриншоты). Когда закончишь — напиши /done")
        return await message.answer("Пришли ID записи (item_id).")

    if not message.photo:
        return await message.answer("Пришли фото")

    if count >= 5:
        return await message.answer("Лимит 5 фото. Напиши /done")

    file_id = message.photo[-1].file_id
    if db.add_screenshot(item_id, file_id):
        count += 1
        await state.update_data(count=count)
        await message.answer(f"Добавлено {count}/5")
    else:
        await message.answer("Ошибка при сохранении фото")

@dp.message_handler(commands=['del_photos'], state="*")
async def delete_photos_command(message: types.Message, state: FSMContext):
    await state.finish()
    if message.from_user.id not in config.ADMINS:
        return

    args = message.get_args().strip()
    if not args:
        return await message.answer("Укажи ID записи. Пример: /del_photos 123")
    if not args.isdigit():
        return await message.answer("Неверный ID")

    item_id = int(args)
    if not db.game_exists_by_id(item_id):
        return await message.answer("Такой записи нет")

    deleted = db.delete_screenshots_by_item(item_id)
    await message.answer(f"Удалено {deleted} фото")

@dp.message_handler(commands=['del_photo'], state="*")
async def delete_photo_command(message: types.Message, state: FSMContext):
    await state.finish()
    if message.from_user.id not in config.ADMINS:
        return

    args = message.get_args().strip()
    if not args:
        return await message.answer("Укажи ID фото. Пример: /del_photo 5")
    if not args.isdigit():
        return await message.answer("Неверный ID")

    photo_id = int(args)
    deleted = db.delete_screenshot_by_id(photo_id)
    if deleted:
        await message.answer("Фото удалено")
    else:
        await message.answer("Фото не найдено")

@dp.message_handler(commands=['set_rating'], state="*")
async def admin_set_rating(message: types.Message, state: FSMContext):
    await state.finish()
    if message.from_user.id not in config.ADMINS:
        return

    args = message.get_args().strip()
    if not args:
        return await message.answer("Пример: /set_rating minecraft 5")
    parts = args.rsplit(" ", 1)
    if len(parts) != 2 or not parts[1].isdigit():
        return await message.answer("Пример: /set_rating minecraft 5")

    game_name = parts[0].strip()
    rating = int(parts[1])
    if rating < 1 or rating > 5:
        return await message.answer("Оценка должна быть от 1 до 5")

    if not db.get_game_by_name(game_name):
        return await message.answer("Такой игры нет")

    if db.add_or_update_rating(message.from_user.id, game_name, rating):
        await message.answer(f"Готово. Поставлено {rating}/5")
    else:
        await message.answer("Ошибка сохранения")

@dp.message_handler(commands=['reset_ratings'], state="*")
async def admin_reset_ratings(message: types.Message, state: FSMContext):
    await state.finish()
    if message.from_user.id not in config.ADMINS:
        return

    game_name = message.get_args().strip()
    if not game_name:
        return await message.answer("Пример: /reset_ratings minecraft")

    if not db.get_game_by_name(game_name):
        return await message.answer("Такой игры нет")

    count = db.delete_ratings_for_game(game_name)
    await message.answer(f"Удалено оценок: {count}")

@dp.message_handler(commands=['del_rating'], state="*")
async def admin_delete_rating(message: types.Message, state: FSMContext):
    await state.finish()
    if message.from_user.id not in config.ADMINS:
        return

    args = message.get_args().strip()
    if not args:
        return await message.answer("Пример: /del_rating 123456 minecraft")
    parts = args.split(" ", 1)
    if len(parts) != 2 or not parts[0].isdigit():
        return await message.answer("Пример: /del_rating 123456 minecraft")

    user_id = int(parts[0])
    game_name = parts[1].strip()
    if not game_name:
        return await message.answer("Пример: /del_rating 123456 minecraft")

    if not db.get_game_by_name(game_name):
        return await message.answer("Такой игры нет")

    deleted = db.delete_rating(user_id, game_name)
    if deleted:
        await message.answer("Оценка удалена")
    else:
        await message.answer("Оценка не найдена")

@dp.message_handler(commands=['boost_rating'], state="*")
async def admin_boost_rating(message: types.Message, state: FSMContext):
    await state.finish()
    if message.from_user.id not in config.ADMINS:
        return

    args = message.get_args().strip()
    if not args:
        return await message.answer("Пример: /boost_rating minecraft 4.8 4524")

    parts = args.rsplit(" ", 2)
    if len(parts) != 3:
        return await message.answer("Пример: /boost_rating minecraft 4.8 4524")

    game_name = parts[0].strip()
    try:
        virtual_avg = float(parts[1].replace(",", "."))
        virtual_count = int(parts[2])
    except ValueError:
        return await message.answer("Пример: /boost_rating minecraft 4.8 4524")

    if virtual_avg < 1 or virtual_avg > 5 or virtual_count < 0:
        return await message.answer("Оценка 1–5, количество >= 0")

    if not db.get_game_by_name(game_name):
        return await message.answer("Такой игры нет")

    if db.set_virtual_rating(game_name, virtual_avg, virtual_count):
        await message.answer(f"Готово. Виртуальные голоса: {virtual_count} со средним {virtual_avg}")
    else:
        await message.answer("Ошибка сохранения")

@dp.message_handler(commands=['clear_boost'], state="*")
async def admin_clear_boost(message: types.Message, state: FSMContext):
    await state.finish()
    if message.from_user.id not in config.ADMINS:
        return

    game_name = message.get_args().strip()
    if not game_name:
        return await message.answer("Пример: /clear_boost minecraft")

    if not db.get_game_by_name(game_name):
        return await message.answer("Такой игры нет")

    deleted = db.clear_virtual_rating(game_name)
    if deleted:
        await message.answer("Виртуальные голоса сброшены")
    else:
        await message.answer("Виртуальных голосов нет")

@dp.message_handler(commands=['add_boost'], state="*")
async def admin_add_boost(message: types.Message, state: FSMContext):
    await state.finish()
    if message.from_user.id not in config.ADMINS:
        return

    args = message.get_args().strip()
    if not args:
        return await message.answer("Пример: /add_boost minecraft 4.7 100")

    parts = args.rsplit(" ", 2)
    if len(parts) != 3:
        return await message.answer("Пример: /add_boost minecraft 4.7 100")

    game_name = parts[0].strip()
    try:
        virtual_avg = float(parts[1].replace(",", "."))
        virtual_count = int(parts[2])
    except ValueError:
        return await message.answer("Пример: /add_boost minecraft 4.7 100")

    if virtual_avg < 1 or virtual_avg > 5 or virtual_count < 0:
        return await message.answer("Оценка 1–5, количество >= 0")

    if not db.get_game_by_name(game_name):
        return await message.answer("Такой игры нет")

    if db.add_virtual_rating(game_name, virtual_avg, virtual_count):
        await message.answer(f"Добавлено {virtual_count} голосов со средним {virtual_avg}")
    else:
        await message.answer("Ошибка сохранения")

about_keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="№️ О Нас", callback_data="about_callback")]])

@dp.message_handler(commands=['about'], state="*")
async def about_command(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("Нажмите на кнопку ниже, чтобы узнать о нас 👇", reply_markup=about_keyboard)

@dp.callback_query_handler(lambda c: c.data == "about_callback", state="*")
async def about_info_callback(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await callback_query.answer()
    text = (
        "👋 Привет! Мы — бот для скачивания .IPA файлов.\n\n"
        "🎮 Здесь вы можете найти игры и приложения для iOS.\n"
        "💡 Проект был придуман ещё в 2024 году.\n"
        "👨‍💻 Разработчик — @hydrauk.\n"
        "🛡️ Файлы безопасны.\n"
        "💎 Подписка открывает премиум-возможности.\n"
        "📧 Связь: matersasm@gmail.com\n"
        "📞 Поддержка всегда готова помочь!"
    )
    photo_path = "attached_assets/IMG_3677.jpg"
    try:
        photo = types.InputFile(photo_path)
        await callback_query.message.answer_photo(photo=photo, caption=text)
    except Exception as e:
        logger.error(f"About error: {e}")
        await callback_query.message.answer(text)

@dp.message_handler(commands=['admin'], state="*")
async def show_admin_stats(message: types.Message, state: FSMContext):
    await state.finish()
    if message.from_user.id not in config.ADMINS:
        return
    stats = db.get_stats()
    if not stats:
        return await message.answer("❌ Ошибка при получении статистики")
    stats_text = (
        "📊 *Статистика бота:*\n\n"
        f"👥 *Всего пользователей:* `{stats['total_users']}`\n"
        f"💎 *Премиум пользователей:* `{stats['premium_users']}`\n"
        f"📥 *Всего загрузок:* `{stats['total_downloads']}`\n"
        f"🎮 *Всего приложений в базе:* `{stats['total_apps']}`"
    )
    await message.answer(stats_text, parse_mode="Markdown")

@dp.message_handler(lambda m: m.text == "💡 Предложить игру", state="*")
async def suggest_game_prompt(message: types.Message, state: FSMContext):
    await state.finish()
    await SuggestionStates.waiting_for_suggestion.set()
    await message.answer(
        "📌 *Предложить игру или приложение*\n\n"
        "Напишите название и, если есть, ссылку на IPA файл.\n"
        "Ваше предложение будет отправлено администратору на рассмотрение! ✨",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_suggestion")]]))

@dp.callback_query_handler(lambda c: c.data == "cancel_suggestion", state="*")
async def cancel_suggestion(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await callback_query.message.edit_text("❌ Предложение отменено.")
    await callback_query.answer()

@dp.message_handler(state=SuggestionStates.waiting_for_suggestion)
async def process_suggestion(message: types.Message, state: FSMContext):
    menu_buttons = ["💎 Купить подписку", "👤 Мой профиль", "📜 История скачиваний", "❣️ Помощь", "№️ О Нас", "💡 Предложить игру"]
    if message.text in menu_buttons or message.text.startswith('/'):
        await state.finish()
        return await handle_game_query(message, state)

    if message.text == "❌ Отмена":
        await state.finish()
        return await message.answer("❌ Предложение отменено.", reply_markup=get_main_keyboard())

    name, url = parse_suggestion_text(message.text)
    suggestion_id = db.add_suggestion(message.from_user.id, name, url or "")

    url_text = url if url else "нет ссылки"
    id_text = f"#{suggestion_id}" if suggestion_id else "N/A"

    for admin_id in config.ADMINS:
        try:
            await bot.send_message(
                admin_id,
                f"🔔 Новое предложение!\n\n"
                f"🆔 ID: `{id_text}`\n"
                f"👤 От: {message.from_user.mention}\n"
                f"🆔 User ID: `{message.from_user.id}`\n"
                f"📝 Игра/Приложение: {name}\n"
                f"🔗 Ссылка: {url_text}",
                parse_mode="Markdown"
            )
        except Exception:
            pass

    await state.finish()
    await message.answer("✅ Спасибо! Ваше предложение отправлено администратору.", reply_markup=get_main_keyboard())

@dp.message_handler(commands=['my_suggestion'], state="*")
async def show_suggestions_admin(message: types.Message, state: FSMContext):
    await state.finish()
    if message.from_user.id not in config.ADMINS:
        return

    suggestions = db.get_pending_suggestions()
    if not suggestions:
        return await message.answer("Нет новых предложений.")

    for suggestion_id, user_id, name, url in suggestions:
        url_text = url if url else "нет ссылки"
        text = (
            "💡 Предложение от пользователя\n\n"
            f"🆔 ID: `{suggestion_id}`\n"
            f"🆔 User ID: `{user_id}`\n"
            f"📝 Игра/Приложение: {name}\n"
            f"🔗 Ссылка: {url_text}"
        )
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="✅ Добавить", callback_data=f"suggest_approve_{suggestion_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"suggest_reject_{suggestion_id}")
        ]])
        await message.answer(text, parse_mode="Markdown", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data.startswith("suggest_approve_") or c.data.startswith("suggest_reject_"), state="*")
async def handle_suggestion_action(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    if callback_query.from_user.id not in config.ADMINS:
        return await callback_query.answer("Недостаточно прав", show_alert=True)

    action, suggestion_id_text = callback_query.data.rsplit("_", 1)
    if not suggestion_id_text.isdigit():
        return await callback_query.answer("Неверный ID", show_alert=True)

    suggestion_id = int(suggestion_id_text)
    suggestion = db.get_suggestion_by_id(suggestion_id)
    if not suggestion:
        return await callback_query.answer("Предложение не найдено", show_alert=True)

    _, user_id, name, url, status = suggestion
    if status != "pending":
        return await callback_query.answer("Предложение уже обработано", show_alert=True)

    if action == "suggest_approve":
        added = True
        if url:
            added = db.add_game(name, url)
        if not added:
            return await callback_query.answer("Ошибка при добавлении игры", show_alert=True)

        db.update_suggestion_status(suggestion_id, "approved")
        try:
            await bot.send_message(user_id, f"✅ Ваше предложение только что добавлено!\n\n📝 {name}")
        except Exception:
            pass

        await callback_query.message.edit_text("✅ Предложение одобрено.")
        return await callback_query.answer()

    db.update_suggestion_status(suggestion_id, "rejected")
    try:
        await bot.send_message(user_id, f"❌ Ваше предложение отклонено.\n\n📝 {name}")
    except Exception:
        pass
    await callback_query.message.edit_text("❌ Предложение отклонено.")
    await callback_query.answer()

@dp.message_handler(commands=['addgame'], state="*")
async def add_game_admin(message: types.Message, state: FSMContext):
    await state.finish()
    if message.from_user.id not in config.ADMINS:
        return

    args = message.get_args().split('|')
    if len(args) < 3:
        return await message.answer(
            "❌ Неверный формат команды\n\n"
            "Использование: `/addgame name | url | type | category | version | updated | genre | developer | size`\n"
            "Пример: `/addgame Morphite | https://link.com | game | action | v1.08 | Feb 3, 2021 | Arcade | Crescent Moon | 1.5 GB`",
            parse_mode="Markdown"
        )

    args = [arg.strip() for arg in args]
    name = args[0]
    url = args[1]
    content_type = args[2]
    category = args[3] if len(args) > 3 else "other"
    version = args[4] if len(args) > 4 else "N/A"
    updated = args[5] if len(args) > 5 else "N/A"
    genre = args[6] if len(args) > 6 else "N/A"
    developer = args[7] if len(args) > 7 else "N/A"
    size = args[8] if len(args) > 8 else "N/A"

    success = db.add_game(name, url, content_type, category, version, updated, genre, developer, size)
    if success:
        await message.answer(f"✅ Игра *{name}* успешно добавлена в базу!", parse_mode="Markdown")
    else:
        await message.answer("❌ Ошибка при добавлении игры в базу данных")

@dp.message_handler(commands=['addipa'], state="*")
async def add_ipa_start(message: types.Message, state: FSMContext):
    await state.finish()
    if message.from_user.id not in config.ADMINS:
        return
    await AddIpaState.waiting_file.set()
    await message.answer(
        "Отправь .ipa файлом (document).\n"
        "После файла бот попросит метаданные."
    )

@dp.message_handler(commands=['cancel_addipa'], state=AddIpaState.waiting_meta)
@dp.message_handler(commands=['cancel_addipa'], state=AddIpaState.waiting_file)
async def add_ipa_cancel(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("Добавление IPA отменено.")

@dp.message_handler(state=AddIpaState.waiting_file, content_types=types.ContentTypes.DOCUMENT)
async def add_ipa_file(message: types.Message, state: FSMContext):
    if message.from_user.id not in config.ADMINS:
        return
    file_id = message.document.file_id
    await state.update_data(file_id=file_id)
    await AddIpaState.waiting_meta.set()
    await message.answer(
        "Теперь отправь метаданные строкой:\n"
        "name | type | category | version | updated | genre | developer | size\n\n"
        "Пример:\n"
        "Minecraft | game | arcade | v1.21.132 | January 26, 2026 | Sandbox | Mojang AB | 577 MB"
    )

@dp.message_handler(state=AddIpaState.waiting_file, content_types=types.ContentTypes.ANY)
async def add_ipa_file_invalid(message: types.Message, state: FSMContext):
    if message.from_user.id not in config.ADMINS:
        return
    await message.answer("Пришли IPA именно файлом (document), не текстом.")

@dp.message_handler(state=AddIpaState.waiting_meta, content_types=['text'])
async def add_ipa_meta(message: types.Message, state: FSMContext):
    if message.from_user.id not in config.ADMINS:
        return

    data = await state.get_data()
    file_id = data.get("file_id")
    if not file_id:
        await state.finish()
        return await message.answer("Ошибка: file_id не найден, начни заново /addipa")

    parts = [p.strip() for p in message.text.split("|")]
    if len(parts) < 1 or not parts[0]:
        return await message.answer("Нужно минимум указать название. Пример: Minecraft | game | arcade | v1.21")

    name = parts[0]
    content_type = parts[1] if len(parts) > 1 and parts[1] else "game"
    category = parts[2] if len(parts) > 2 and parts[2] else "other"
    version = parts[3] if len(parts) > 3 and parts[3] else "N/A"
    updated = parts[4] if len(parts) > 4 and parts[4] else "N/A"
    genre = parts[5] if len(parts) > 5 and parts[5] else "N/A"
    developer = parts[6] if len(parts) > 6 and parts[6] else "N/A"
    size = parts[7] if len(parts) > 7 and parts[7] else "N/A"
    ok = db.add_game(name, file_id, content_type, category, version, updated, genre, developer, size)
    await state.finish()
    if not ok:
        return await message.answer("❌ Ошибка при сохранении IPA в каталог")

    item_id = db.get_game_id_by_name(name)
    text = (
        f"✅ IPA добавлен в каталог\n"
        f"🎮 {name}\n"
        f"🆔 ID: {item_id if item_id else '-'}\n"
        f"📦 Версия: {version}\n"
        f"🗂 Тип: {content_type}"
    )
    await message.answer(text)

@dp.message_handler(commands=['search'], state="*")
async def search_in_group(message: types.Message, state: FSMContext):
    await state.finish()
    if message.chat.type not in ("group", "supergroup"):
        return await message.answer("Команда /search работает в группе.")

    query = message.get_args().strip()
    if not query:
        return await message.answer("Использование: /search <название игры>")

    game_name = query.lower()
    games = db.get_all_games()
    for game in games:
        if game[0].lower() == game_name:
            name, url, content_type, category, version, updated, genre, developer, size = game
            rating_line = format_rating_line(name)
            item_id = db.get_game_id_by_name(name)
            try:
                details_text = (
                    f"🎮 *Игра:* `{name}`\n"
                    f"📦 *Версия:* `{version}`\n"
                    f"🗓 *Обновлено:* `{updated}`\n"
                    f"🎮 *Жанр:* `{genre}`\n"
                    f"👤 *Разработчик:* `{developer}`\n"
                    f"⚖️ *Размер:* `{size}`\n\n"
                    f"{rating_line}\n"
                    f"📥 [Скачать {name}]({url})"
                )
                if message.from_user.id in config.ADMINS and item_id:
                    details_text += f"\n\n🆔 ID: `{item_id}`"
                if url.startswith('http'):
                    await message.answer(details_text, parse_mode="Markdown", disable_web_page_preview=True, reply_markup=get_game_keyboard(name, item_id))
                elif os.path.exists(url):
                    file = types.InputFile(url)
                    await message.answer_document(file, caption=details_text, parse_mode="Markdown", reply_markup=get_game_keyboard(name, item_id))
                elif isinstance(url, str) and url.strip():
                    await message.answer_document(url.strip(), caption=details_text, parse_mode="Markdown", reply_markup=get_game_keyboard(name, item_id))
                return
            except Exception as e:
                logger.error(f"Error sending game info in group search: {e}")
                return await message.answer("❌ Ошибка при отправке карточки игры")

    await message.answer("❌ Игра не найдена")

@dp.message_handler(content_types=['text'], state="*")
async def handle_game_query(message: types.Message, state: FSMContext):
    await state.finish()
    if not message.text:
        return

    if message.text.startswith('/'):
        return

    if message.text == "💎 Купить подписку":
        return await buy(message, state)
    if message.text == "👤 Мой профиль":
        return await show_profile(message, state)
    if message.text == "📜 История скачиваний":
        return await show_history(message, state)
    if message.text == "💡 Предложить игру":
        return await suggest_game_prompt(message, state)
    if message.text == "№️ О Нас":
        return await about_command(message, state)
    if message.text == "❣️ Помощь":
        try:
            photo = types.InputFile("attached_assets/3327752.jpg")
            await message.answer_photo(photo=photo, caption="Привет! 👋 Вы обратились в поддержку.\n\n📋 /popular - популярные\n👤 /profile - профиль\n📜 /history - история\n\n👉 Связь: @Helpicore_bot")
        except Exception:
            await message.answer("Привет! 👋 Вы обратились в поддержку.\n\n👉 Связь: @Helpicore_bot")
        return

    game_name = message.text.lower()
    games = db.get_all_games()
    for game in games:
        if game[0].lower() == game_name:
            name, url, content_type, category, version, updated, genre, developer, size = game
            rating_line = format_rating_line(name)
            item_id = db.get_game_id_by_name(name)
            try:
                details_text = (
                    f"🎮 *Игра:* `{name}`\n"
                    f"📦 *Версия:* `{version}`\n"
                    f"🗓 *Обновлено:* `{updated}`\n"
                    f"🎮 *Жанр:* `{genre}`\n"
                    f"👤 *Разработчик:* `{developer}`\n"
                    f"⚖️ *Размер:* `{size}`\n\n"
                    f"{rating_line}\n"
                    f"📥 [Скачать {name}]({url})"
                )
                if message.from_user.id in config.ADMINS and item_id:
                    details_text += f"\n\n🆔 ID: `{item_id}`"
                if url.startswith('http'):
                    await message.answer(details_text, parse_mode="Markdown", disable_web_page_preview=True, reply_markup=get_game_keyboard(name, item_id))
                    db.add_download(message.from_user.id, name)
                elif os.path.exists(url):
                    file = types.InputFile(url)
                    await message.answer_document(file, caption=details_text, parse_mode="Markdown", reply_markup=get_game_keyboard(name, item_id))
                    db.add_download(message.from_user.id, name)
                elif isinstance(url, str) and url.strip():
                    await message.answer_document(url.strip(), caption=details_text, parse_mode="Markdown", reply_markup=get_game_keyboard(name, item_id))
                    db.add_download(message.from_user.id, name)
                return
            except Exception as e:

                logger.error(f"Error sending game info: {e}")

    await message.answer("❌ Игра не найдена")

@dp.message_handler(commands=['popular'], state="*")
async def show_popular_games(message: types.Message, state: FSMContext):
    await state.finish()
    games = db.get_all_games()
    categories = {}
    for game in games:
        if game[2] == 'game':
            cat = game[3] if len(game) > 3 else 'other'
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(game[0].title())

    text = "🔥 *Популярные игры:*\n\n"
    for cat, items in categories.items():
        if items:
            text += f"📍 *{cat.title()}:* {', '.join(items[:5])}\n\n"
    await message.answer(text, parse_mode="Markdown")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
