"""
回测入口 - 运行回测并生成图表
"""
import sys
import os

# 确保项目根目录在 Python 路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_fetcher import fetch_all_stocks
from strategy import run_backtest
from chart_generator import generate_chart_with_signals, generate_summary_image
from telegram_sender import TelegramSender
from config import STOCK_CODES


def main():
    print("=" * 60)
    print("量化回测系统 - 均线交叉策略")
    print("=" * 60)

    # 1. 获取数据
    print("\n[Step 1] 获取股票数据...")
    all_data = fetch_all_stocks()

    if not all_data:
        print("未能获取任何股票数据，退出")
        return

    # 2. 遍历每只股票进行回测
    results = []
    for symbol, df in all_data.items():
        print(f"\n[Step 2] 回测 {symbol} ...")

        # 运行回测
        result = run_backtest(symbol, df)
        if result is None:
            continue

        results.append(result)

        # 3. 生成K线图
        print(f"\n[Step 3] 生成 {symbol} K线图...")
        if result["signals"]:
            chart_path = generate_chart_with_signals(
                df=df,
                symbol=symbol,
                signals=result["signals"],
                short_ma=5,
                long_ma=20
            )
            result["chart_path"] = chart_path
        else:
            # 没有信号也生成无标注的K线图
            chart_path = generate_chart_with_signals(
                df=df,
                symbol=symbol,
                signals=None,
                short_ma=5,
                long_ma=20
            )
            result["chart_path"] = chart_path

        # 4. 生成汇总图
        summary_path = generate_summary_image(
            results=result["metrics"],
            symbol=symbol
        )
        result["summary_path"] = summary_path

        print(f"\n[Step 4] {symbol} 回测完成!")
        print(f"  - 信号数: {len(result['signals'])}")
        print(f"  - 总收益: {result['metrics'].get('total_return', 0):.2%}")
        print(f"  - K线图: {result['chart_path']}")

    # 5. 推送到 Telegram
    print(f"\n[Step 5] 准备推送 Telegram...")

    sender = TelegramSender()
    token_valid = sender.bot is not None

    if not token_valid:
        print("⚠️ Telegram Token 未配置或无效，跳过推送")
        print("请在 config.py 中设置 TG_BOT_TOKEN 和 TG_CHAT_ID")
    else:
        print("Telegram 已配置，准备发送...")
        for result in results:
            try:
                sender.send_chart_with_signals(
                    chart_path=result.get("chart_path"),
                    symbol=result["symbol"],
                    metrics=result["metrics"],
                    signals=result["signals"]
                )
                print(f"✅ {result['symbol']} 推送完成")
            except Exception as e:
                print(f"❌ {result['symbol']} 推送失败: {e}")

    print("\n" + "=" * 60)
    print("回测全部完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()