from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
import random
import string
import re

API_ID = 21552265
API_HASH = "1c971ae7e62cc416ca977e040e700d09"
BOT_TOKEN = "8344548094:AAE3kiGxrX06fLIFsOweDgVBbDuDjdCpCcg"

app = Client("temp_mail_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

user_emails = {}

def create_account():
    domain = requests.get("https://api.mail.tm/domains").json()["hydra:member"][0]["domain"]
    username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    password = "Password123"
    email = f"{username}@{domain}"

    requests.post("https://api.mail.tm/accounts", json={
        "address": email,
        "password": password
    })

    token = requests.post("https://api.mail.tm/token", json={
        "address": email,
        "password": password
    }).json()["token"]

    return email, token

def get_messages(token):
    headers = {"Authorization": f"Bearer {token}"}
    messages = requests.get("https://api.mail.tm/messages", headers=headers).json()
    return messages.get("hydra:member", [])

@app.on_message(filters.command("start"))
async def start(client, message):
    email, token = create_account()
    user_emails[message.from_user.id] = {"email": email, "token": token}

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📥 Check Inbox", callback_data="check")],
        [InlineKeyboardButton("🔄 Refresh", callback_data="refresh")]
    ])

    await message.reply(
        f"📧 **Your Temporary Email:**\n\n`{email}`\n\nUse this for verification.",
        reply_markup=keyboard
    )

@app.on_callback_query()
async def callback(client, callback_query):
    user_id = callback_query.from_user.id

    if user_id not in user_emails:
        await callback_query.answer("Start first!", show_alert=True)
        return

    token = user_emails[user_id]["token"]
    messages = get_messages(token)

    if not messages:
        await callback_query.answer("No messages yet!", show_alert=True)
        return

    text = ""
    for msg in messages:
        otp = re.findall(r"\b\d{6}\b", msg.get("subject", "") + msg.get("intro", ""))
        if otp:
            text += f"🔢 OTP: {otp[0]}\n"

    if text == "":
        text = "📩 Message received but no OTP found."

    await callback_query.message.reply(text)
    await callback_query.answer()

app.run()
