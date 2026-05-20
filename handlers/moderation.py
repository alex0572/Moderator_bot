import logging

from aiogram import Bot, F, Router
from aiogram.enums import ChatType
from aiogram.exceptions import TelegramAPIError
from aiogram.types import Message

from filters.profanity import contains_profanity
from utils.database import ActionType, Database
from utils.warnings import send_profanity_warning

router = Router(name="moderation")
logger = logging.getLogger("moderation_bot.handlers")


def _user_id(message: Message) -> int:
    if message.from_user:
        return message.from_user.id
    return 0


@router.message(F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}))
async def moderate_group_message(message: Message, bot: Bot, db: Database) -> None:
    if message.from_user and message.from_user.is_bot:
        return

    user_id = _user_id(message)
    chat_id = message.chat.id
    preview = (message.text or message.caption or "")[:500]

    await db.log_action(
        user_id=user_id,
        chat_id=chat_id,
        action=f"chat={chat_id} msg_id={message.message_id} text={preview!r}",
        action_type=ActionType.INCOMING_MESSAGE,
    )
    logger.info(
        "Incoming message: chat_id=%s user_id=%s message_id=%s",
        chat_id,
        user_id,
        message.message_id,
    )

    text = message.text or message.caption
    if not contains_profanity(text):
        return

    try:
        await bot.delete_message(chat_id=chat_id, message_id=message.message_id)
    except TelegramAPIError as exc:
        err = f"Delete failed chat={chat_id} msg={message.message_id}: {exc}"
        logger.error(err)
        await db.log_action(
            user_id=user_id,
            chat_id=chat_id,
            action=err,
            action_type=ActionType.ERROR,
        )
        return

    action = f"Deleted profanity message_id={message.message_id} text={preview!r}"
    await db.log_action(
        user_id=user_id,
        chat_id=chat_id,
        action=action,
        action_type=ActionType.MESSAGE_DELETED,
    )
    logger.warning(
        "Message deleted: chat_id=%s user_id=%s message_id=%s",
        chat_id,
        user_id,
        message.message_id,
    )

    if message.from_user:
        await send_profanity_warning(
            bot,
            db,
            chat_id=chat_id,
            user=message.from_user,
            deleted_message_id=message.message_id,
        )
