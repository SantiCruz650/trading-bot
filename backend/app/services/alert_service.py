"""
Alert Service - Telegram notifications for trading events
"""
import os
import logging
from typing import Optional
import asyncio

try:
    from telegram import Bot
    from telegram.error import TelegramError
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    Bot = None
    TelegramError = Exception

logger = logging.getLogger(__name__)


class AlertService:
    """Send trading alerts via Telegram"""
    
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.bot = None
        self.enabled = False
        
        if TELEGRAM_AVAILABLE and self.bot_token and self.chat_id:
            try:
                self.bot = Bot(token=self.bot_token)
                self.enabled = True
                logger.info("✅ Telegram alerts enabled")
            except Exception as e:
                logger.warning(f"Failed to initialize Telegram bot: {e}")
        else:
            logger.info("Telegram alerts disabled (no credentials or library not installed)")
    
    async def send_trade_alert(
        self,
        symbol: str,
        side: str,
        amount: float,
        price: float,
        value: float,
        success: bool = True
    ):
        """Send alert for executed trade"""
        if not self.enabled:
            return
        
        emoji = "✅" if success else "❌"
        action_emoji = "🟢" if side == "buy" else "🔴"
        
        message = f"""
{emoji} **TRADE EXECUTED** {action_emoji}

**Action:** {side.upper()}
**Symbol:** {symbol}
**Amount:** {amount:.6f}
**Price:** ${price:,.2f}
**Value:** ${value:,.2f}

**Time:** {self._get_timestamp()}
        """.strip()
        
        await self._send_message(message)
    
    async def send_stop_loss_alert(
        self,
        symbol: str,
        entry_price: float,
        exit_price: float,
        loss_pct: float,
        loss_usd: float
    ):
        """Send alert when stop-loss is triggered"""
        if not self.enabled:
            return
        
        message = f"""
⚠️ **STOP-LOSS TRIGGERED** ⚠️

**Symbol:** {symbol}
**Entry Price:** ${entry_price:,.2f}
**Exit Price:** ${exit_price:,.2f}
**Loss:** {loss_pct:.2f}% (${loss_usd:,.2f})

**Time:** {self._get_timestamp()}
        """.strip()
        
        await self._send_message(message)
    
    async def send_daily_summary(
        self,
        trades_count: int,
        pnl: float,
        win_rate: float,
        balance: float
    ):
        """Send daily trading summary"""
        if not self.enabled:
            return
        
        pnl_emoji = "📈" if pnl >= 0 else "📉"
        
        message = f"""
📊 **DAILY SUMMARY** {pnl_emoji}

**Trades:** {trades_count}
**P&L:** ${pnl:,.2f} ({'+' if pnl >= 0 else ''}{pnl:.2f})
**Win Rate:** {win_rate:.1f}%
**Balance:** ${balance:,.2f}

**Date:** {self._get_timestamp()}
        """.strip()
        
        await self._send_message(message)
    
    async def send_circuit_breaker_alert(self, reason: str):
        """Send alert when circuit breaker activates"""
        if not self.enabled:
            return
        
        message = f"""
🚨 **CIRCUIT BREAKER ACTIVATED** 🚨

**Reason:** {reason}

**ALL TRADING STOPPED**
Manual reset required.

**Time:** {self._get_timestamp()}
        """.strip()
        
        await self._send_message(message)
    
    async def send_error_alert(self, error_type: str, details: str):
        """Send alert for system errors"""
        if not self.enabled:
            return
        
        message = f"""
❌ **SYSTEM ERROR** ❌

**Type:** {error_type}
**Details:** {details}

**Time:** {self._get_timestamp()}
        """.strip()
        
        await self._send_message(message)
    
    async def _send_message(self, text: str):
        """Internal method to send message"""
        if not self.enabled or not self.bot:
            return
        
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=text,
                parse_mode='Markdown'
            )
            logger.info("✅ Telegram alert sent")
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
    
    def _get_timestamp(self):
        """Get current timestamp string"""
        from datetime import datetime
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')


# Singleton instance
_alert_service = None

def get_alert_service() -> AlertService:
    """Get or create alert service instance"""
    global _alert_service
    if _alert_service is None:
        _alert_service = AlertService()
    return _alert_service
