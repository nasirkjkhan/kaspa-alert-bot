# bot/database.py
import aiosqlite
import os
import logging

from bot.config import DATABASE_PATH  # already fixed earlier

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.path = DATABASE_PATH
        os.makedirs(os.path.dirname(self.path), exist_ok=True)

    async def connect(self):
        """Async method to create and return a connection."""
        return await aiosqlite.connect(self.path)

    async def init(self):
        """Initialize the database schema."""
        conn = await self.connect()  # await here to get the connection
        try:
            async with conn:  # now conn supports async context manager
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY,
                        kaspa_address TEXT,
                        krc20_ticker TEXT,
                        last_kas_txid TEXT,
                        last_krc20_ts INTEGER
                    )
                """)
                await conn.commit()
            logger.info("Database initialized")
        finally:
            await conn.close()  # always close the connection

    async def get_user(self, user_id: int):
        conn = await self.connect()
        try:
            cursor = await conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            return await cursor.fetchone()
        finally:
            await conn.close()

    async def get_all_users_with_address(self):
        conn = await self.connect()
        try:
            cursor = await conn.execute("SELECT * FROM users WHERE kaspa_address IS NOT NULL")
            return await cursor.fetchall()
        finally:
            await conn.close()

    async def update_user_address(self, user_id: int, address: str | None):
        conn = await self.connect()
        try:
            if address is None:
                await conn.execute("UPDATE users SET kaspa_address = NULL, last_kas_txid = NULL WHERE user_id = ?", (user_id,))
            else:
                await conn.execute("""
                    INSERT OR REPLACE INTO users (user_id, kaspa_address)
                    VALUES (?, ?)
                """, (user_id, address))
            await conn.commit()
        finally:
            await conn.close()

    async def update_user_krc20_ticker(self, user_id: int, ticker: str | None):
        conn = await self.connect()
        try:
            if ticker is None:
                await conn.execute("UPDATE users SET krc20_ticker = NULL, last_krc20_ts = NULL WHERE user_id = ?", (user_id,))
            else:
                await conn.execute("UPDATE users SET krc20_ticker = ? WHERE user_id = ?", (ticker, user_id))
            await conn.commit()
        finally:
            await conn.close()

    async def update_last_kas_txid(self, user_id: int, txid: str):
        conn = await self.connect()
        try:
            await conn.execute("UPDATE users SET last_kas_txid = ? WHERE user_id = ?", (txid, user_id))
            await conn.commit()
        finally:
            await conn.close()

    async def update_last_krc20_ts(self, user_id: int, ts: int):
        conn = await self.connect()
        try:
            await conn.execute("UPDATE users SET last_krc20_ts = ? WHERE user_id = ?", (ts, user_id))
            await conn.commit()
        finally:
            await conn.close()
