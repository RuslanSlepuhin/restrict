from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ChatPermissions
from aiogram.utils.callback_data import CallbackData
from dotenv import load_dotenv
import os
import logging

# Включаем логирование
from subscribers_ids import get_all_member_ids

logging.basicConfig(level=logging.INFO)

# Загрузка переменных окружения из файла .env
load_dotenv()

# Токен бота
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))
TELEGRAM_API_ID = os.getenv("TELEGRAM_API_ID")
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH")
GROUP_USERNAME = os.getenv("GROUP_USERNAME")

if not BOT_TOKEN or not TELEGRAM_API_ID or not TELEGRAM_API_HASH or not GROUP_USERNAME:
    raise ValueError("Проверьте файл .env. Некоторые переменные окружения отсутствуют.")

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# Callback data для кнопок
admin_cb = CallbackData("admin", "action")

# Создание клавиатуры для админов
admin_keyboard = InlineKeyboardMarkup(row_width=2)
admin_keyboard.add(
    InlineKeyboardButton("\u26D4 Запретить писать", callback_data=admin_cb.new(action="restrict")),
    InlineKeyboardButton("\u2705 Разрешить писать", callback_data=admin_cb.new(action="allow"))
)

# Проверка прав пользователя
async def is_user_admin(chat_id, user_id):
    try:
        member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
        return member.is_chat_admin()
    except Exception as e:
        logging.error(f"Ошибка при проверке прав пользователя {user_id} в чате {chat_id}: {e}")
        return False

# Обработчик команды /start
@dp.message_handler(commands=["start"])
async def start_command(message: types.Message):
    user_id = message.from_user.id

    # Проверяем, является ли пользователь администратором в указанной группе
    if await is_user_admin(GROUP_ID, user_id):
        await message.reply("Панель управления для группы:", reply_markup=admin_keyboard)
    else:
        await message.reply("\u26A0 У вас недостаточно прав для управления этой группой.")

# Обработчик нажатия кнопок
@dp.callback_query_handler(admin_cb.filter())
async def admin_buttons_handler(query: types.CallbackQuery, callback_data: dict):
    user_id = query.from_user.id

    # Проверяем, является ли пользователь администратором в указанной группе
    if not await is_user_admin(GROUP_ID, user_id):
        await query.answer("\u26A0 У вас недостаточно прав.", show_alert=True)
        return

    action = callback_data["action"]

    if action == "restrict":
        await restrict_all_members(GROUP_ID)
        await query.message.edit_text("\u26D4 Все участники теперь не могут писать.", reply_markup=admin_keyboard)
    elif action == "allow":
        await allow_all_members(GROUP_ID)
        await query.message.edit_text("\u2705 Все участники теперь могут писать.", reply_markup=admin_keyboard)

# Функция для запрета писать всем участникам
async def restrict_all_members(chat_id: int):
    members = await bot.get_chat_administrators(chat_id)
    member_ids = [member.user.id for member in members if not member.user.is_bot]

    # Получаем список всех участников чата
    all_member_ids = await get_all_member_ids(TELEGRAM_API_ID, TELEGRAM_API_HASH, GROUP_USERNAME)

    for member_id in all_member_ids:
        if member_id not in member_ids:
            try:
                await bot.restrict_chat_member(
                    chat_id,
                    member_id,
                    permissions=ChatPermissions(can_send_messages=False)
                )
            except Exception as e:
                logging.error(f"Ошибка при ограничении участника {member_id}: {e}")

# Функция для разрешения писать всем участникам
async def allow_all_members(chat_id: int):
    members = await bot.get_chat_administrators(chat_id)
    member_ids = [member.user.id for member in members if not member.user.is_bot]

    # Получаем список всех участников чата
    all_member_ids = await get_all_member_ids(TELEGRAM_API_ID, TELEGRAM_API_HASH, GROUP_USERNAME)

    for member_id in all_member_ids:
        if member_id not in member_ids:
            try:
                await bot.restrict_chat_member(
                    chat_id,
                    member_id,
                    permissions=ChatPermissions(
                        can_send_messages=True,
                        can_send_media_messages=True,
                        can_send_other_messages=True,
                        can_add_web_page_previews=True
                    )
                )
            except Exception as e:
                logging.error(f"Ошибка при разрешении участника {member_id}: {e}")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)

