import aiosqlite
import os
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.path = DATABASE_PATH
        os.makedirs(os.path.dirname(self.path), exist_ok=True)

    async def connect(self):
        return await aiosqlite.connect(self.path)

    async def init(self):
        async with self.connect() as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    kaspa_address TEXT,
                    krc20_ticker TEXT,
                    last_kas_txid TEXT,
                    last_krc20_ts INTEGER
                )
            """)
            await db.commit()
        logger.info("Database initialized")

    async def get_user(self, user_id: int):
        async with self.connect() as db:
            cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            return await cursor.fetchone()

    async def get_all_users_with_address(self):
        async with self.connect() as db:
            cursor = await db.execute("SELECT * FROM users WHERE kaspa_address IS NOT NULL")
            return await cursor.fetchall()

    async def update_user_address(self, user_id: int, address: str | None):
        async with self.connect() as db:
            if address is None:
                await db.execute("UPDATE users SET kaspa_address = NULL, last_kas_txid = NULL WHERE user_id = ?", (user_id,))
            else:
                await db.execute("""
                    INSERT OR REPLACE INTO users (user_id, kaspa_address)
                    VALUES (?, ?)
                """, (user_id, address))
            await db.commit()

    async def update_user_krc20_ticker(self, user_id: int, ticker: str | None):
        async with self.connect() as db:
            if ticker is None:
                await db.execute("UPDATE users SET krc20_ticker = NULL, last_krc20_ts = NULL WHERE user_id = ?", (user_id,))
            else:
                await db.execute("UPDATE users SET krc20_ticker = ? WHERE user_id = ?", (ticker, user_id))
            await db.commit()

    async def update_last_kas_txid(self, user_id: int, txid: str):
        async with self.connect() as db:
            await db.execute("UPDATE users SET last_kas_txid = ? WHERE user_id = ?", (txid, user_id))
            await db.commit()

    async def update_last_krc20_ts(self, user_id: int, ts: int):
        async with self.connect() as db:
            await db.execute("UPDATE users SET last_krc20_ts = ? WHERE user_id = ?", (ts, user_id))
            await db.commit()
