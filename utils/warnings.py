import asyncio
import logging

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.types import Message, User

from config.settings import settings
from utils.database import ActionType, Database

logger = logging.getLogger("moderation_bot.warnings")


def _user_mention(user: User) -> str:
    name = user.full_name or user.username or "участник"
    return f'<a href="tg://user?id={user.id}">{name}</a>'


async def _delete_message_later(bot: Bot, chat_id: int, message_id: int, delay: int) -> None:
    await asyncio.sleep(delay)
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except TelegramAPIError as exc:
        logger.debug("Could not delete warning message %s: %s", message_id, exc)


async def send_profanity_warning(
    bot: Bot,
    db: Database,
    *,
    chat_id: int,
    user: User,
    deleted_message_id: int,
) -> None:
    if not settings.warning_enabled:
        return

    mention = _user_mention(user)
    text = settings.warning_message.format(user=mention)

    try:
        warning = await bot.send_message(chat_id=chat_id, text=text)
    except TelegramAPIError as exc:
        err = f"Warning send failed chat={chat_id} user={user.id}: {exc}"
        logger.error(err)
        await db.log_action(
            user_id=user.id,
            chat_id=chat_id,
            action=err,
            action_type=ActionType.ERROR,
        )
        return

    await db.log_action(
        user_id=user.id,
        chat_id=chat_id,
        action=f"Warning sent for deleted msg_id={deleted_message_id} warning_id={warning.message_id}",
        action_type=ActionType.WARNING_SENT,
    )
    logger.warning(
        "Warning sent: chat_id=%s user_id=%s warning_id=%s",
        chat_id,
        user.id,
        warning.message_id,
    )

    if settings.warning_ttl_seconds > 0:
        asyncio.create_task(
            _delete_message_later(
                bot,
                chat_id,
                warning.message_id,
                settings.warning_ttl_seconds,
            )
        )
