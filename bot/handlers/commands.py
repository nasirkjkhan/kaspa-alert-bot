from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.database import Database

router = Router()
db = Database()

@router.message(Command("start"))
async def cmd_start(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Set Kaspa Address", callback_data="set_address")],
        [InlineKeyboardButton(text="Set KRC20 Token (optional)", callback_data="set_krc20")],
        [InlineKeyboardButton(text="My Status", callback_data="my_status")],
        [InlineKeyboardButton(text="Help", callback_data="help")],
    ])
    await message.answer("Welcome to the Kaspa Alert Bot! Get alerts for incoming KAS and KRC20 transfers.", reply_markup=keyboard)

@router.message(Command("setaddress"))
async def cmd_setaddress(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Usage: /setaddress <kaspa:address>")
        return
    address = args[1].strip()
    if not address.startswith("kaspa:") or not (65 <= len(address) <= 85):
        await message.answer("Invalid Kaspa address. It must start with 'kaspa:' and be between 65 and 85 characters long.")
        return
    await db.update_user_address(message.from_user.id, address)
    await message.answer(f"Kaspa address set to: {address}")

@router.message(Command("setkrc20"))
async def cmd_setkrc20(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Usage: /setkrc20 <TICKER>")
        return
    ticker = args[1].strip().upper()
    await db.update_user_krc20_ticker(message.from_user.id, ticker)
    await message.answer(f"KRC20 ticker set to: {ticker}")

@router.message(Command("mystatus"))
async def cmd_mystatus(message: Message):
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("No settings found. Use /setaddress to start.")
        return
    _, address, ticker, last_txid, last_ts = user
    status = "Your Status:\n"
    status += f"Kaspa Address: {address if address else 'Not set'}\n"
    status += f"KRC20 Ticker: {ticker if ticker else 'Not set'}\n"
    status += f"Last seen KAS TxID: {last_txid if last_txid else 'None'}\n"
    status += f"Last seen KRC20 transfer time: {last_ts if last_ts else 'None'}\n"
    await message.answer(status)

@router.message(Command("removeaddress"))
async def cmd_removeaddress(message: Message):
    await db.update_user_address(message.from_user.id, None)
    await message.answer("Kaspa address and related data removed.")

@router.message(Command("removekrc20"))
async def cmd_removekrc20(message: Message):
    await db.update_user_krc20_ticker(message.from_user.id, None)
    await message.answer("KRC20 ticker monitoring removed.")

@router.message(Command("help"))
async def cmd_help(message: Message):
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
    await message.answer(help_text)
