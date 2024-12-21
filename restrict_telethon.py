from telethon import Button
from telethon.sync import TelegramClient, events
from telethon.tl.functions.channels import EditBannedRequest
from telethon.tl.types import ChatBannedRights
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsSearch
from telethon.tl.functions.contacts import ResolveUsernameRequest
from telethon.tl.types import InputPeerChannel
from telethon.tl.types import InputPeerUser
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.functions.messages import GetBotCallbackAnswerRequest
from telethon.tl.types import InputBotInlineMessageID
from telethon.tl.functions.messages import EditMessageRequest
from telethon.tl.types import InputBotInlineResult
from telethon.tl.functions.messages import GetBotCallbackAnswerRequest
from telethon.tl.types import InputBotInlineMessageID
from telethon.tl.functions.messages import EditMessageRequest
from telethon.tl.types import InputBotInlineResult
from dotenv import load_dotenv
import os
import logging

# Включаем логирование
logging.basicConfig(level=logging.INFO)

# Загрузка переменных окружения из файла .env
load_dotenv()

# Токен бота
API_ID = os.getenv("TELEGRAM_API_ID")
API_HASH = os.getenv("TELEGRAM_API_HASH")
GROUP_USERNAME = int(os.getenv("GROUP_ID"))
BOT_TOKEN = os.getenv('BOT_TOKEN')

if not API_ID or not API_HASH or not GROUP_USERNAME:
    raise ValueError("Проверьте файл .env. Некоторые переменные окружения отсутствуют.")

client = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# Функция для получения списка идентификаторов участников группы
async def get_all_member_ids(group_username):
    # Получаем информацию о группе
    channel = await client.get_entity(group_username)
    channel_full = await client(GetFullChannelRequest(channel))
    channel_id = channel_full.full_chat.id

    # Получаем список участников
    offset = 0
    limit = 100
    all_participants = []

    while True:
        participants = await client(GetParticipantsRequest(
            channel,
            ChannelParticipantsSearch(''),
            offset,
            limit,
            0
        ))
        if not participants.users:
            break
        all_participants.extend(participants.users)
        offset += len(participants.users)

    member_ids = [user.id for user in all_participants]
    return member_ids, channel_id

# Функция для запрета писать всем участникам
async def restrict_all_members(channel_id, member_ids):
    for member_id in member_ids:
        # if not await is_user_admin(member_id, channel_id):
            try:
                await client(EditBannedRequest(
                    channel_id,
                    member_id,
                    ChatBannedRights(
                        until_date=None,
                        view_messages=True,
                        send_messages=False,
                        send_media=False,
                        send_stickers=False,
                        send_gifs=False,
                        send_games=False,
                        send_inline=False,
                        embed_links=False
                    )
                ))
            except Exception as e:
                logging.error(f"Ошибка при ограничении участника {member_id}: {e}")

# Функция для разрешения писать всем участникам
async def allow_all_members(channel_id, member_ids):
    for member_id in member_ids:
        # if not await is_user_admin(member_id, channel_id):
            try:
                await client(EditBannedRequest(
                    channel_id,
                    member_id,
                    ChatBannedRights(
                        until_date=None,
                        view_messages=True,
                        send_messages=True,
                        send_media=True,
                        send_stickers=True,
                        send_gifs=True,
                        send_games=True,
                        send_inline=True,
                        embed_links=True
                    )
                ))
            except Exception as e:
                logging.error(f"Ошибка при разрешении участника {member_id}: {e}")

# Обработчик команды /start
@client.on(events.NewMessage(pattern='/start'))
async def start_command(event):
    user_id = event.sender_id
    member_ids, channel_id = await get_all_member_ids(GROUP_USERNAME)

    # Проверяем, является ли пользователь администратором в указанной группе
    if user_id in member_ids:
        buttons = [
            [Button.inline("Запретить писать", b"restrict")],
            [Button.inline("Разрешить писать", b"allow")]
        ]
        await event.reply("Панель управления для группы:", buttons=buttons)
    else:
        await event.reply("\u26A0 У вас недостаточно прав для управления этой группой.")

# Обработчик нажатия кнопок
@client.on(events.CallbackQuery)
async def admin_buttons_handler(event):
    user_id = event.sender_id
    member_ids, channel_id = await get_all_member_ids(GROUP_USERNAME)

    # Проверяем, является ли пользователь администратором в указанной группе
    if user_id not in member_ids:
        await event.answer("\u26A0 У вас недостаточно прав.", alert=True)
        return

    action = event.data.decode('utf-8')

    if action == "restrict":
        await restrict_all_members(channel_id, member_ids)
        await event.edit("\u26D4 Все участники теперь не могут писать.")
    elif action == "allow":
        await allow_all_members(channel_id, member_ids)
        await event.edit("\u2705 Все участники теперь могут писать.")

# Функция для проверки, является ли пользователь администратором
async def is_user_admin(user_id, channel_id):
    try:
        participant = await client(GetParticipantsRequest(
            channel_id,
            ChannelParticipantsSearch(user_id),
            0,
            1,
            0
        ))
        return any(user.participant.admin_rights for user in participant.users)
    except Exception as e:
        logging.error(f"Ошибка при проверке прав пользователя {user_id} в чате {channel_id}: {e}")
        return False


if __name__ == "__main__":
    with client:
        client.start()
        client.run_until_disconnected()
