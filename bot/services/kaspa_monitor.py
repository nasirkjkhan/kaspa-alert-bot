import asyncio
import aiohttp
import logging

from bot.database import Database
from bot.config import CHECK_INTERVAL_SECONDS  # ← FIXED: import added here

from aiogram import Bot

logger = logging.getLogger(__name__)
db = Database()

async def monitor_task(bot: Bot):
    while True:
        try:
            users = await db.get_all_users_with_address()
            async with aiohttp.ClientSession() as session:
                for user in users:
                    user_id, address, ticker, last_kas_txid, last_krc20_ts = user
                    try:
                        # Check KAS transactions
                        resp = await session.get(f"https://api.kaspa.org/addresses/{address}/full-transactions")
                        if resp.status != 200:
                            logger.error(f"Kaspa API error {resp.status} for address {address}")
                            continue
                        data = await resp.json()

                        incoming_txs = []
                        for tx in data:
                            txid = tx.get('transaction_id')
                            block_time = tx.get('block_time')
                            if not txid or not block_time:
                                continue
                            incoming_amount = sum(
                                out.get('amount', 0) for out in tx.get('outputs', [])
                                if out.get('script_public_key_address') == address
                            )
                            if incoming_amount > 0:
                                from_addr = tx.get('inputs', [{}])[0].get('previous_outpoint_address', 'Unknown')
                                incoming_txs.append({
                                    'txid': txid,
                                    'block_time': block_time,
                                    'amount': incoming_amount,
                                    'from': from_addr
                                })

                        incoming_txs.sort(key=lambda x: x['block_time'])

                        start_idx = 0
                        if last_kas_txid:
                            for i, tx in enumerate(incoming_txs):
                                if tx['txid'] == last_kas_txid:
                                    start_idx = i + 1
                                    break
                            else:
                                logger.warning(f"Last KAS txid {last_kas_txid} not found for {address}, skipping alerts")
                                continue

                        new_last_txid = last_kas_txid
                        for tx in incoming_txs[start_idx:]:
                            kas = tx['amount'] / 100_000_000  # sompi → KAS
                            alert = (
                                f"Received {kas:.4f} KAS from {tx['from']}\n"
                                f"TxID: {tx['txid']}\n"
                                f"https://explorer.kaspa.org/transactions/{tx['txid']}"
                            )
                            await bot.send_message(user_id, alert)
                            logger.info(f"Sent KAS alert to user {user_id}")
                            new_last_txid = tx['txid']

                        if new_last_txid != last_kas_txid:
                            await db.update_last_kas_txid(user_id, new_last_txid)

                        await asyncio.sleep(0.5)  # gentle rate limit

                        # KRC20 check
                        if ticker:
                            url = f"https://api.kasplex.org/api/v1/krc20/address/{address}/txs?limit=20"
                            resp = await session.get(url)
                            if resp.status != 200:
                                logger.error(f"Kasplex API error {resp.status} for {address}")
                                continue
                            data = await resp.json()
                            transfers = []
                            for tx in data.get('data', []):
                                ts = tx.get('time')
                                txid = tx.get('txId')
                                if not ts or not txid:
                                    continue
                                for op in tx.get('operations', []):
                                    if (
                                        op.get('op') == 'transfer' and
                                        op.get('to') == address and
                                        op.get('tick', '').upper() == ticker
                                    ):
                                        transfers.append({
                                            'txid': txid,
                                            'ts': ts,
                                            'amt': op.get('amt'),
                                            'from': op.get('from')
                                        })

                            transfers.sort(key=lambda x: x['ts'])

                            last_ts_val = last_krc20_ts if last_krc20_ts else 0
                            new_transfers = [t for t in transfers if t['ts'] > last_ts_val]

                            new_last_ts = last_ts_val
                            for t in new_transfers:
                                alert = (
                                    f"Received {t['amt']} {ticker} from {t['from']}\n"
                                    f"TxID: {t['txid']}\n"
                                    f"https://explorer.kaspa.org/transactions/{t['txid']}"
                                )
                                await bot.send_message(user_id, alert)
                                logger.info(f"Sent KRC20 alert to user {user_id}")
                                new_last_ts = max(new_last_ts, t['ts'])

                            if new_last_ts > last_ts_val:
                                await db.update_last_krc20_ts(user_id, new_last_ts)

                        await asyncio.sleep(1)  # between users

                    except Exception as e:
                        logger.error(f"Error processing user {user_id}: {e}")
                        continue

        except Exception as e:
            logger.error(f"Monitor task outer error: {e}")

        await asyncio.sleep(CHECK_INTERVAL_SECONDS)
