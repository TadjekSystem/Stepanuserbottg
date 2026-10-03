# -*- coding: utf-8 -*-
"""
Stepan Userbot — юзербот для Telegram на Python (Telethon).

Возможности:
  .menu   — сообщение с командой .menu редактируется и превращается
            в меню юзербота "Stepan Userbot" (с кнопками).
  .help   — показать список команд.
  .ping   — проверить, что бот работает.
  .id     — показать свой id / id чата.

Логин: при первом запуске бот спросит номер телефона, код из Telegram
и (если включена 2FA) пароль. Данные сохранятся в *.session-файл,
повторно вводить их не нужно.

Запуск:
    python stepan_userbot.py
"""

import asyncio
import re
import time

from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError

import config

BOT_NAME = "Stepan Userbot"

MENU_TEXT = (
    f"🤖 **{BOT_NAME}**\n\n"
    "Меню юзербота:\n\n"
    "📌 Основные команды:\n"
    "`{p}ping` — проверка работы\n"
    "`{p}help` — список команд\n"
    "`{p}id` — твой ID\n"
    "`{p}menu` — показать это меню снова\n"
    "`{p}off` — удалить меню\n"
).format(p=config.COMMAND_PREFIX)

MENU_BUTTONS = [
    ["🔄 Обновить", f"{config.COMMAND_PREFIX}menu"],
    ["📋 Помощь", f"{config.COMMAND_PREFIX}help"],
    ["🏓 Пинг", f"{config.COMMAND_PREFIX}ping"],
]


def build_client() -> TelegramClient:
    return TelegramClient(config.SESSION_NAME, config.API_ID, config.API_HASH)


async def login(client: TelegramClient) -> None:
    """Интерактивный вход: номер → код → пароль (2FA)."""
    if await client.is_user_authorized():
        return

    phone = input("Введите номер телефона (например +79991234567): ").strip() or config.PHONE
    await client.send_code_request(phone)

    try:
        code = input("Введите код из Telegram: ").strip()
        await client.sign_in(phone=phone, code=code)
    except SessionPasswordNeededError:
        password = input("Включена 2FA. Введите пароль: ").strip() or config.PASSWORD
        await client.sign_in(password=password)

    print("✅ Успешный вход! Сессия сохранена, повторно логиниться не нужно.")


async def show_menu(event: events.NewMessage.Event) -> None:
    """Превращает сообщение с .menu в меню юзербота."""
    await event.edit(
        message=MENU_TEXT,
        buttons=MENU_BUTTONS,
        parse_mode="markdown",
    )


def register_handlers(client: TelegramClient) -> None:
    p = re.escape(config.COMMAND_PREFIX)

    # .menu — заменяем СВОЁ сообщение на меню
    @client.on(events.NewMessage(pattern=rf"^{p}menu"))
    async def handler_menu(event: events.NewMessage.Event):
        if not event.outgoing:
            return
        if config.MENU_CHAT_ID is not None and event.chat_id != config.MENU_CHAT_ID:
            return
        await show_menu(event)

    @client.on(events.NewMessage(pattern=rf"^{p}ping"))
    async def handler_ping(event: events.NewMessage.Event):
        if not event.outgoing:
            return
        start = time.perf_counter()
        msg = await event.edit("🏓 Пингую...")
        latency = round((time.perf_counter() - start) * 1000)
        await msg.edit(f"🏓 **Pong!** Задержка: `{latency} мс`\n⚡ {BOT_NAME} на связи.")

    @client.on(events.NewMessage(pattern=rf"^{p}help"))
    async def handler_help(event: events.NewMessage.Event):
        if not event.outgoing:
            return
        text = (
            f"📖 **{BOT_NAME} — команды:**\n\n"
            f"`{config.COMMAND_PREFIX}menu` — меню юзербота\n"
            f"`{config.COMMAND_PREFIX}ping` — проверка задержки\n"
            f"`{config.COMMAND_PREFIX}id` — информация об ID\n"
            f"`{config.COMMAND_PREFIX}off` — удалить сообщение\n"
        )
        await event.edit(text, parse_mode="markdown")

    @client.on(events.NewMessage(pattern=rf"^{p}id"))
    async def handler_id(event: events.NewMessage.Event):
        if not event.outgoing:
            return
        me = await client.get_me()
        await event.edit(
            f"🆔 Твой ID: `{me.id}`\nID чата: `{event.chat_id}`",
            parse_mode="markdown",
        )

    @client.on(events.NewMessage(pattern=rf"^{p}off"))
    async def handler_off(event: events.NewMessage.Event):
        if not event.outgoing:
            return
        await event.delete()


async def main() -> None:
    client = build_client()
    await client.connect()
    await login(client)

    register_handlers(client)

    me = await client.get_me()
    print(f"🚀 {BOT_NAME} запущен как @{me.username or me.first_name} (id={me.id})")
    print(f"📝 Напиши в любой чат команду `{config.COMMAND_PREFIX}menu` — она превратится в меню.")

    await client.run_until_disconnected()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, EOFError):
        print("\n👋 Остановка юзербота.")
