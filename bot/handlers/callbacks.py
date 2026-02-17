from aiogram import Router
from aiogram.types import CallbackQuery

from bot.database import Database

router = Router()
db = Database()

@router.callback_query(lambda c: c.data == "set_address")
async def cb_set_address(query: CallbackQuery):
    await query.answer()
    await query.message.answer("To set your Kaspa address, use:\n/setaddress <kaspa:address>")

@router.callback_query(lambda c: c.data == "set_krc20")
async def cb_set_krc20(query: CallbackQuery):
    await query.answer()
    await query.message.answer("To set your KRC20 ticker, use:\n/setkrc20 <TICKER>")

@router.callback_query(lambda c: c.data == "my_status")
async def cb_my_status(query: CallbackQuery):
    await query.answer()
    user = await db.get_user(query.from_user.id)
    if not user:
        await query.message.answer("No settings found. Use /setaddress to start.")
        return
    _, address, ticker, last_txid, last_ts = user
    status = "Your Status:\n"
    status += f"Kaspa Address: {address if address else 'Not set'}\n"
    status += f"KRC20 Ticker: {ticker if ticker else 'Not set'}\n"
    status += f"Last seen KAS TxID: {last_txid if last_txid else 'None'}\n"
    status += f"Last seen KRC20 transfer time: {last_ts if last_ts else 'None'}\n"
    await query.message.answer(status)

@router.callback_query(lambda c: c.data == "help")
async def cb_help(query: CallbackQuery):
    await query.answer()
    help_text = """
Kaspa Alert Bot Commands:
/start - Show welcome message and menu
/setaddress <kaspa:address> - Set your Kaspa address
/setkrc20 <TICKER> - Set KRC20 token ticker to monitor (uppercase)
/mystatus - Show your current settings and last seen data
/removeaddress - Remove Kaspa address
/removekrc20 - Remove KRC20 ticker
/help - Show this help message

The bot checks for new transactions every 5 minutes (configurable).
"""
    await query.message.answer(help_text)
