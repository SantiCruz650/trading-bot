import logging
from telegram import Bot
from telegram.error import TelegramError
from ..core.config import settings

logger = logging.getLogger(__name__)

class TelegramService:
    def __init__(self):
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.chat_id = settings.TELEGRAM_CHAT_ID
        self.bot = None
        if self.token:
            self.bot = Bot(token=self.token)

    async def send_alert(self, message: str):
        if not self.token or not self.chat_id:
            logger.warning("Telegram bot token or chat ID not configured.")
            return

        try:
            async with Bot(token=self.token) as bot:
                await bot.send_message(chat_id=self.chat_id, text=message)
                logger.info(f"Telegram alert sent: {message}")
        except TelegramError as e:
            logger.error(f"Failed to send Telegram alert: {e}")
        except Exception as e:
            logger.error(f"Unexpected error sending Telegram alert: {e}")

telegram_service = TelegramService()
