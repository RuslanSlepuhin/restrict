import asyncio
import os

from dotenv import load_dotenv
from telethon.sync import TelegramClient
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsSearch
from telethon.tl.functions.contacts import ResolveUsernameRequest
from telethon.tl.types import InputPeerChannel
from telethon.tl.types import InputPeerUser
from telethon.tl.functions.channels import GetFullChannelRequest

# Функция для получения списка идентификаторов участников группы
async def get_all_member_ids(api_id, api_hash, group_username):
    client = TelegramClient('session_name', api_id, api_hash)
    await client.start()

    # Получаем информацию о группе
    result = await client(ResolveUsernameRequest(group_username))
    channel = result.peer
    if isinstance(channel, InputPeerChannel):
        channel_full = await client(GetFullChannelRequest(channel))
        channel_id = channel_full.full_chat.id
    else:
        raise ValueError("Группа не найдена")

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
    await client.disconnect()
    return member_ids

if __name__=='__main__':
    load_dotenv()

    # Токен бота
    TELEGRAM_API_ID = os.getenv("TELEGRAM_API_ID")
    TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH")
    GROUP_USERNAME = os.getenv("GROUP_USERNAME")

    asyncio.run(get_all_member_ids(TELEGRAM_API_ID, TELEGRAM_API_HASH, GROUP_USERNAME))