"""
Telegram 推送模块 - 使用 requests 直接调用 Telegram Bot API
（无需安装 python-telegram-bot）
"""
import os
import requests
from config import TG_BOT_TOKEN, TG_CHAT_ID
import pandas as pd


class TelegramSender:
    def __init__(self, token=None, chat_id=None):
        self.token = token or TG_BOT_TOKEN
        self.chat_id = chat_id or TG_CHAT_ID
        self.api_url = f"https://api.telegram.org/bot{self.token}" if self.token and self.token != "YOUR_BOT_TOKEN_HERE" else None

        if self.api_url:
            print(f"Telegram Bot 已配置 (Chat ID: {self.chat_id})")
        else:
            print("⚠️ Telegram Token 未配置，跳过实际发送")

    def _send_request(self, method, data=None, files=None):
        """发送 Telegram API 请求"""
        if not self.api_url:
            print(f"[TG模拟] {method}: {data}")
            return None

        url = f"{self.api_url}/{method}"
        try:
            response = requests.post(url, data=data, files=files, timeout=30)
            result = response.json()
            if result.get("ok"):
                return result
            else:
                print(f"[TG] API错误: {result}")
                return None
        except Exception as e:
            print(f"[TG] 请求失败: {e}")
            return None

    def send_text(self, message, parse_mode="Markdown"):
        """
        发送文本消息
        """
        data = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": parse_mode
        }
        return self._send_request("sendMessage", data=data)

    def send_photo(self, image_path, caption=None):
        """
        发送图片（K线图）
        """
        if not os.path.exists(image_path):
            print(f"图片不存在: {image_path}")
            return False

        if not self.api_url:
            print(f"[TG模拟] 发送图片: {image_path}")
            return True

        with open(image_path, "rb") as photo:
            files = {"photo": photo}
            data = {
                "chat_id": self.chat_id,
                "caption": caption or ""
            }
            return self._send_request("sendPhoto", data=data, files=files)

    def send_chart_with_signals(self, chart_path, symbol, metrics, signals):
        """
        发送带信号的K线图 + 交易信号摘要
        """
        # 1. 发送文字摘要
        signal_count = len(signals) if signals else 0
        buy_count = sum(1 for s in signals if s["type"] == "buy") if signals else 0
        sell_count = sum(1 for s in signals if s["type"] == "sell") if signals else 0

        total_return_str = f"{metrics.get('total_return', 0):.2%}"
        final_value_str = f"{metrics.get('final_value', 0):.2f}"
        shapr_str = str(metrics.get('sharpe', 'N/A'))
        max_dd_str = f"{metrics.get('max_drawdown', 0):.2%}"
        win_rate_str = f"{metrics.get('win_rate', 0):.2%}"

        summary = f"""📊 **{symbol} 量化回测报告**

📈 策略: MA5 × MA20 均线交叉
⏱️ 周期: 30分钟K线
🔢 周期: 近2个月

📉 *收益指标*
总收益率: `{total_return_str}`
最终净值: `{final_value_str}`
夏普比率: `{shapr_str}`
最大回撤: `{max_dd_str}`
胜率: `{win_rate_str}`

📌 *交易统计*
信号总数: {signal_count}
买入信号: {buy_count} 📈
卖出信号: {sell_count} 📉

⏰ 生成时间: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}"""

        self.send_text(summary)

        # 2. 发送K线图
        if chart_path and os.path.exists(chart_path):
            chart_caption = f"{symbol} 30分钟K线 (MA5/MA20) + 交易信号"
            self.send_photo(chart_path, caption=chart_caption)

        # 3. 信号详情（最多20条）
        if signals and len(signals) <= 20:
            signal_detail = "📋 *交易信号详情*\n\n"
            for i, sig in enumerate(signals, 1):
                emoji = "📈" if sig["type"] == "buy" else "📉"
                sig_dt = sig["datetime"]
                if hasattr(sig_dt, "strftime"):
                    sig_dt = sig_dt.strftime("%Y-%m-%d %H:%M")
                signal_detail += f"{i}. {emoji} **{sig['type'].upper()}** | {sig_dt} | ¥{sig['price']:.2f}\n"

            self.send_text(signal_detail)


def test_telegram():
    """测试 Telegram 推送"""
    sender = TelegramSender()
    sender.send_text("🧪 *量化交易系统测试*\n\n这是一条来自量化系统的测试消息。")
    print("Telegram 推送测试完成")


if __name__ == "__main__":
    test_telegram()