import logging
import os
import sys
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ChatJoinRequestHandler,
    ChatMemberHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from aiohttp import web

# ✅ Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# ✅ Load environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
RENDER_EXTERNAL_URL = "https://ranjanbot.onrender.com"  # Render injects this for web service
WEBHOOK_PATH = "/telegram"  # You can customize if needed
WEBHOOK_URL = f"{RENDER_EXTERNAL_URL}{WEBHOOK_PATH}" if RENDER_EXTERNAL_URL else ""

app = None  # Global app reference for webhook processing


# ✅ New function: Handle private messages to the bot
async def handle_private_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    logger.info(f"Received private message from {user.full_name}: {update.message.text}")

    reply_text = """
I am a bot and cannot reply to messages. Please contact the admin. Thank you

@vallyadmin
"""

    keyboard = [
        [InlineKeyboardButton("👨‍💼 Contact Admin", url="https://t.me/vallyadmin")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await update.message.reply_text(
            text=reply_text,
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
        logger.info(f"Sent auto-reply to {user.full_name}")
    except Exception as e:
        logger.warning(f"Couldn't send auto-reply to {user.full_name}: {e}")


# ✅ Function to approve join requests and send welcome DM
async def approve_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.chat_join_request.from_user
    chat = update.chat_join_request.chat
    logger.info(f"Join request from {user.full_name} in {chat.title}")

    await update.chat_join_request.approve()

    welcome_text = f"""
👋 Hi {user.first_name}!

Welcome to 👑 *{chat.title}* 👑 

TRIED MANY OTHER VIP CHANNELS AND STILL LOSING YOUR HARD EARN MONEY? 

BECAUSE THEY DON'T CARE ABOUT YOUR HARD EARN MONEY

But Vally takes care of every penny of yours because I know how that money is earned 🥹

🔹 JOIN TRADE WITH VALLY VVIP & GET :

◾ 7 – 12 DIRECT WINS SIGNALS DAILY 👇

( MY SIGNALS ACCURACY ABOVE 89% ) 

◾ SIGNALS POWERED BY MY PURE 5 YEARS OF EXPERIENCE IN BINARY TRADING 📊

◾ CALL SUPPORT + GUIDANCE + EXCLUSIVE STRATEGY 

REGISTER FROM THIS LINK 👇

👉 GLOBAL AUDIENCE
https://broker-qx.pro/sign-up/?lid=507502

👉 BANGLADESH + PAKISTAN AUDIENCE
https://market-qx.pro/sign-up/?lid=507502

◾ DEPOSIT MINIMUM $30 OR ABOVE

🔴 MESSAGE ME NOW – @VALLYADMIN
"""

    keyboard = [
        [InlineKeyboardButton("👨‍💼 Admin", url="https://t.me/vallyadmin?text=Hello%F0%9F%91%8B%20Vally%20Trader%2C%20I%20want%20to%20Join%20your%20VVIP")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await context.bot.send_message(
            chat_id=user.id,
            text=welcome_text,
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
        logger.info(f"Sent welcome message to {user.full_name}")
    except Exception as e:
        logger.warning(f"Couldn't send DM to {user.full_name}: {e}")

# ✅ Function to detect when user leaves/kicked & send farewell DM
async def handle_member_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_member = update.chat_member
    user = chat_member.from_user
    status = chat_member.new_chat_member.status

    if chat_member.chat.id != CHANNEL_ID:
        return

    if status in ['left', 'kicked']:
        logger.info(f"{user.full_name} left or was kicked from the channel.")
        try:
            await context.bot.send_message(
                chat_id=user.id,
                text=f"Goodbye {user.first_name}! 👋\nSorry to see you leave *{chat_member.chat.title}*.",
                parse_mode="Markdown"
            )
            logger.info(f"Sent farewell message to {user.full_name}")
        except Exception as e:
            logger.warning(f"Couldn't send farewell DM to {user.full_name}: {e}")

# --- New webhook-related aiohttp code and main ---

# Health check endpoint for Render or uptime
async def handle_health(request):
    return web.Response(text="Bot is alive and running! 🚀")

# Webhook POST endpoint
async def handle_webhook(request):
    try:
        data = await request.json()
        update = Update.de_json(data, app.bot)
        await app.process_update(update)
    except Exception as e:
        logger.error(f"Failed to process update: {e}")
    return web.Response(text="OK")

async def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    web_app = web.Application()
    web_app.router.add_get('/', handle_health)
    web_app.router.add_post(WEBHOOK_PATH, handle_webhook)
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logger.info(f"HTTP server running on port {port}")

# Keep-alive ping for Render or uptime services
async def keep_alive_ping(url: str, interval: int = 30):
    import aiohttp
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    logger.info(f"[PING] Keep-alive ping to {url} — Status: {resp.status}")
        except Exception as e:
            logger.warning(f"[PING ERROR] {e}")
        await asyncio.sleep(interval)


# ✅ Main function
async def main():
    global app
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # ✅ Register handlers
    app.add_handler(ChatJoinRequestHandler(approve_join_request))
    app.add_handler(ChatMemberHandler(handle_member_status, ChatMemberHandler.CHAT_MEMBER))
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE, handle_private_message))

    logger.info("Starting bot and setting webhook...")

    await app.initialize()
    await app.bot.set_webhook(WEBHOOK_URL)
    await app.start()

    # ✅ Start web server to receive webhook updates
    await run_web_server()

        # Start keep-alive pinger if URL provided
    if RENDER_EXTERNAL_URL:
        asyncio.create_task(keep_alive_ping(RENDER_EXTERNAL_URL))

    # ✅ Keep running
    stop_event = asyncio.Event()
    await stop_event.wait()

    # ✅ Graceful shutdown
    await app.stop()
    await app.shutdown()

# ✅ Entry point
if __name__ == "__main__":
    if sys.platform.startswith('win') and sys.version_info[:2] >= (3, 8):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
