import logging
from enum import StrEnum

import asyncpg

from config.settings import settings

logger = logging.getLogger("moderation_bot.db")

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS moderation_actions (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    chat_id BIGINT,
    action TEXT NOT NULL,
    action_type VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_moderation_actions_user_id
    ON moderation_actions (user_id);
CREATE INDEX IF NOT EXISTS idx_moderation_actions_created_at
    ON moderation_actions (created_at DESC);
"""


class ActionType(StrEnum):
    INCOMING_MESSAGE = "incoming_message"
    MESSAGE_DELETED = "message_deleted"
    WARNING_SENT = "warning_sent"
    ERROR = "error"


class Database:
    def __init__(self) -> None:
        self._pool: asyncpg.Pool | None = None

    @property
    def is_connected(self) -> bool:
        return self._pool is not None

    async def connect(self) -> None:
        self._pool = await asyncpg.create_pool(
            host=settings.db_host,
            port=settings.db_port,
            database=settings.db_name,
            user=settings.db_user,
            password=settings.db_password,
            min_size=1,
            max_size=5,
            command_timeout=30,
        )
        async with self._pool.acquire() as conn:
            await conn.execute(CREATE_TABLE_SQL)
        logger.info("Connected to PostgreSQL at %s:%s/%s", settings.db_host, settings.db_port, settings.db_name)

    async def close(self) -> None:
        if self._pool:
            await self._pool.close()
            self._pool = None
            logger.info("Database pool closed")

    async def log_action(
        self,
        *,
        user_id: int,
        chat_id: int | None,
        action: str,
        action_type: ActionType,
    ) -> None:
        if not self._pool:
            raise RuntimeError("Database is not connected")

        try:
            async with self._pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO moderation_actions (user_id, chat_id, action, action_type)
                    VALUES ($1, $2, $3, $4)
                    """,
                    user_id,
                    chat_id,
                    action[:2000],
                    action_type.value,
                )
        except Exception:
            logger.exception("Failed to write action to database: type=%s user_id=%s", action_type, user_id)
            raise
