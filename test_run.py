"""快速测试脚本"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_fetcher import fetch_sina_kline
from strategy import run_backtest
from chart_generator import generate_chart_with_signals

print("=== 量化系统测试 ===")

# 1. 获取数据
df = fetch_sina_kline("sh600000", scale=30, datalen=100)
print(f"数据: {len(df)} 条")

# 2. 回测
result = run_backtest("sh600000", df)
if result:
    print(f"信号数: {len(result['signals'])}")
    print(f"收益率: {result['metrics'].get('total_return', 0):.2%}")

    # 3. 生成图表
    if result["signals"]:
        chart_path = generate_chart_with_signals(df, "sh600000", result["signals"], 5, 20)
        print(f"图表: {chart_path}")
        print(f"文件存在: {os.path.exists(chart_path)}")
    else:
        chart_path = generate_chart_with_signals(df, "sh600000", None, 5, 20)
        print(f"无信号图表: {chart_path}")
else:
    print("回测失败")

print("=== 测试完成 ===")