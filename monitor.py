"""
定时监控脚本 - 定期获取最新数据并推送K线图到 Telegram
"""
import sys
import os
import time
import schedule
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_fetcher import fetch_all_stocks, fetch_sina_kline
from chart_generator import generate_chart_with_signals
from telegram_sender import TelegramSender
from config import STOCK_CODES, KLINE_SIZE, DATA_DIR
import pandas as pd


def job_morning():
    """
    早盘推送 - 9:30 前发送当日市场概况
    """
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 执行早盘推送...")

    sender = TelegramSender()
    if not sender.bot:
        print("Telegram 未配置，跳过")
        return

    # 获取最新数据
    all_data = fetch_all_stocks()

    for symbol, df in all_data.items():
        if df.empty:
            continue

        # 生成当日K线图（最近5天数据）
        recent_df = df[df["datetime"] >= (pd.Timestamp.now() - pd.Timedelta(days=5))]

        chart_path = os.path.join(DATA_DIR, f"{symbol}_morning.png")
        generate_chart_with_signals(
            df=recent_df,
            symbol=symbol,
            signals=None,  # 早盘不标注信号
            short_ma=5,
            long_ma=20,
            save_path=chart_path
        )

        caption = f"📊 {symbol} 早盘K线 ({datetime.now().strftime('%Y-%m-%d')})"
        sender.send_photo(chart_path, caption=caption)
        time.sleep(1)


def job_signals():
    """
    信号检查 - 检查最新交易信号并推送
    """
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 检查交易信号...")

    sender = TelegramSender()
    if not sender.bot:
        print("Telegram 未配置，跳过")
        return

    # 这里需要结合策略逻辑检测最新信号
    # 简化版本：直接推送最近的数据K线图
    for symbol in STOCK_CODES:
        df = fetch_sina_kline(symbol, scale=KLINE_SIZE, datalen=100)
        if df.empty:
            continue

        # 获取最近一根K线
        latest = df.iloc[-1]
        latest_time = latest["datetime"].strftime("%Y-%m-%d %H:%M")
        latest_price = latest["close"]

        # 简单均线判断
        if len(df) >= 20:
            ma5 = df["close"].tail(5).mean()
            ma20 = df["close"].tail(20).mean()
            prev_ma5 = df["close"].tail(6).iloc[:-1].mean()
            prev_ma20 = df["close"].tail(21).iloc[:-1].mean()

            signal = None
            signal_type = ""

            # 金叉
            if prev_ma5 <= prev_ma20 and ma5 > ma20:
                signal = "📈 买入信号"
                signal_type = "BUY"
            # 死叉
            elif prev_ma5 >= prev_ma20 and ma5 < ma20:
                signal = "📉 卖出信号"
                signal_type = "SELL"

            if signal:
                chart_path = os.path.join(DATA_DIR, f"{symbol}_signal.png")
                generate_chart_with_signals(
                    df=df.tail(100),  # 最近100根K线
                    symbol=symbol,
                    signals=[{
                        "datetime": latest["datetime"],
                        "type": signal_type.lower(),
                        "price": latest_price
                    }],
                    short_ma=5,
                    long_ma=20,
                    save_path=chart_path
                )

                msg = f"""
🔔 *交易信号提醒*

股票: *{symbol}*
时间: {latest_time}
价格: ¥{latest_price:.2f}

{signal}
"""
                sender.send_text(msg)
                sender.send_photo(chart_path, caption=f"{symbol} 最新信号")

                print(f"✅ {symbol} 信号已推送: {signal}")
            else:
                print(f"⏳ {symbol} 无新信号 (MA5={ma5:.2f}, MA20={ma20:.2f})")


def job_night():
    """
    收盘推送 - 发送当日收盘分析
    """
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 执行收盘推送...")

    sender = TelegramSender()
    if not sender.bot:
        print("Telegram 未配置，跳过")
        return

    all_data = fetch_all_stocks()

    for symbol, df in all_data.items():
        if df.empty:
            continue

        # 获取最近2天数据
        recent_df = df[df["datetime"] >= (pd.Timestamp.now() - pd.Timedelta(days=2))]

        chart_path = os.path.join(DATA_DIR, f"{symbol}_night.png")
        generate_chart_with_signals(
            df=recent_df,
            symbol=symbol,
            signals=None,
            short_ma=5,
            long_ma=20,
            save_path=chart_path
        )

        # 计算涨跌
        if len(df) >= 2:
            latest_close = df.iloc[-1]["close"]
            prev_close = df.iloc[-2]["close"]
            change = (latest_close - prev_close) / prev_close * 100
            emoji = "📈" if change > 0 else "📉"
        else:
            change = 0
            emoji = "➡️"

        caption = f"{emoji} {symbol} 收盘 | ¥{latest_close:.2f} ({change:+.2f}%)"
        sender.send_photo(chart_path, caption=caption)
        time.sleep(1)


def run_scheduler():
    """
    运行定时任务调度器
    """
    print("=" * 60)
    print("量化监控定时任务已启动")
    print("=" * 60)
    print("定时任务:")
    print("  09:00 - 早盘K线推送")
    print("  10:00 - 信号检查（每30分钟）")
    print("  15:30 - 收盘推送")
    print("  19:00 - 晚间复盘推送")
    print("=" * 60)

    # 设置定时任务
    schedule.every().day.at("09:00").do(job_morning)
    schedule.every().day.at("15:30").do(job_night)

    # 每30分钟检查信号（工作日）
    schedule.every(30).minutes.do(job_signals)

    # 立即运行一次
    print("\n立即运行一次...")
    job_signals()

    # 持续运行
    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="量化监控定时任务")
    parser.add_argument("--once", action="store_true", help="只运行一次，不持续调度")
    args = parser.parse_args()

    if args.once:
        print("单次运行模式...")
        job_signals()
    else:
        run_scheduler()