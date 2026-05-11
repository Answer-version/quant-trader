"""
配置 - 请修改以下参数
"""
import os

# ============ Telegram 配置 ============
# 从 @BotFather 获取你的 Bot Token
TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
# 你的 Telegram User ID（发消息给 @userinfobot 获取）
TG_CHAT_ID = os.getenv("TG_CHAT_ID", "YOUR_CHAT_ID_HERE")

# ============ 股票代码配置 ============
# 支持多只股票，用逗号分隔
# 格式：sh=上证，sz=深证
# 示例：["sh600000", "sz000858", "sh601318"]
STOCK_CODES = ["sh600000"]  # 浦发银行（示例）

# ============ 策略参数 ============
SHORT_MA = 5    # 短期均线周期
LONG_MA = 20    # 长期均线周期
KLINE_SIZE = 30  # K线周期（分钟）

# ============ 回测参数 ============
START_DATE = "2026-03-11"  # 回测开始日期（2个月前）
END_DATE = "2026-05-11"    # 回测结束日期
INITIAL_CASH = 100000      # 初始资金

# ============ 数据缓存目录 ============
DATA_DIR = "./data"
os.makedirs(DATA_DIR, exist_ok=True)