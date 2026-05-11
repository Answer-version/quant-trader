"""
图表生成模块 - 30分钟K线 + 交易信号标注
"""
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle, FancyArrowPatch
import mplfinance as mpf
import pandas as pd
import numpy as np
from datetime import datetime
import os
from config import DATA_DIR

# 中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False


def generate_chart_with_signals(df, symbol, signals=None, short_ma=5, long_ma=20, save_path=None):
    """
    生成带交易信号的30分钟K线图

    Args:
        df: DataFrame，含 datetime/open/high/low/close/volume 列
        symbol: 股票代码
        signals: list of dict，如 [{"datetime": "2026-03-15 10:00", "type": "buy", "price": 10.5}]
        short_ma: 短期均线周期
        long_ma: 长期均线周期
        save_path: 保存路径
    Returns:
        保存的图片路径
    """
    if df is None or df.empty:
        print("数据为空，跳过制图")
        return None

    # 复制避免修改原数据
    df = df.copy()
    df.set_index("datetime", inplace=True)

    # 计算均线
    df["ma5"] = df["close"].rolling(window=short_ma).mean()
    df["ma20"] = df["close"].rolling(window=long_ma).mean()

    # 分离买卖信号
    buy_signals = []
    sell_signals = []

    if signals:
        for sig in signals:
            sig_dt = pd.to_datetime(sig["datetime"])
            sig_price = sig["price"]
            if sig["type"] == "buy":
                buy_signals.append({"datetime": sig_dt, "price": sig_price})
            else:
                sell_signals.append({"datetime": sig_dt, "price": sig_price})

    # ========== 方式1: mplfinance 快速绘图 ==========
    # 添加自定义均线
    add_plots = [
        mpf.make_addplot(df["ma5"], color="blue", width=0.8, label=f"MA{short_ma}"),
        mpf.make_addplot(df["ma20"], color="red", width=0.8, label=f"MA{long_ma}"),
    ]

    # 添加买卖信号标记
    buy_scatter_x = []
    buy_scatter_y = []
    sell_scatter_x = []
    sell_scatter_y = []

    if buy_signals:
        for sig in buy_signals:
            if sig["datetime"] in df.index:
                idx = df.index.get_loc(sig["datetime"])
                buy_scatter_x.append(idx)
                buy_scatter_y.append(sig["price"] * 0.995)  # 标记在K线下方

    if sell_signals:
        for sig in sell_signals:
            if sig["datetime"] in df.index:
                idx = df.index.get_loc(sig["datetime"])
                sell_scatter_x.append(idx)
                sell_scatter_y.append(sig["price"] * 1.005)  # 标记在K线上方

    # 自定义样式
    style = mpf.make_mpf_style(
        base_mpf_style="charles",
        marketcolors=mpf.make_marketcolors(
            up="#ff1234", down="#00cc44",  # 红涨绿跌（A股习惯）
            edge="inherit",
            wick="inherit",
            volume="in"
        ),
        gridstyle="--",
        gridcolor="#cccccc",
        facecolor="white",
        figcolor="white",
        y_on_right=True
    )

    fig, axes = mpf.plot(
        df,
        type="candle",
        style=style,
        title=f"\n{symbol} 30分钟K线 (MA{short_ma}/{long_ma})",
        ylabel="价格",
        volume=True,
        addplot=add_plots,
        figsize=(16, 10),
        panel_ratios=(4, 1),
        returnfig=True,
        tight_layout=True
    )

    # 在主图上标注买卖信号
    ax_main = axes[0]
    ax_volume = axes[2]

    if buy_signals:
        ax_main.scatter(
            buy_scatter_x, buy_scatter_y,
            marker="^", s=150, color="green", edgecolors="darkgreen",
            linewidths=1.5, zorder=10, label="买入信号"
        )
        # 添加文字标签
        for i, (x, y) in enumerate(zip(buy_scatter_x, buy_scatter_y)):
            ax_main.annotate(
                "买入", (x, y), xytext=(x, y - 0.02 * df["close"].mean()),
                fontsize=8, color="green", fontweight="bold",
                ha="center", va="top"
            )

    if sell_signals:
        ax_main.scatter(
            sell_scatter_x, sell_scatter_y,
            marker="v", s=150, color="red", edgecolors="darkred",
            linewidths=1.5, zorder=10, label="卖出信号"
        )
        for i, (x, y) in enumerate(zip(sell_scatter_x, sell_scatter_y)):
            ax_main.annotate(
                "卖出", (x, y), xytext=(x, y + 0.02 * df["close"].mean()),
                fontsize=8, color="red", fontweight="bold",
                ha="center", va="bottom"
            )

    ax_main.legend(loc="upper left", fontsize=9)

    # 保存
    if save_path is None:
        save_path = os.path.join(DATA_DIR, f"{symbol}_kline_with_signals.png")

    fig.savefig(save_path, dpi=120, bbox_inches="tight", facecolor="white")
    print(f"图表已保存: {save_path}")
    plt.close(fig)

    return save_path


def add_signal_to_chart(ax, df, signal_type, price, datetime_idx):
    """
    在已有axes上添加单个信号标记（用于组合图）
    """
    if signal_type == "buy":
        color, marker = "green", "^"
        offset = -0.02 * df["close"].mean()
    else:
        color, marker = "red", "v"
        offset = 0.02 * df["close"].mean()

    ax.scatter(
        datetime_idx, price + offset,
        marker=marker, s=120, color=color, edgecolors=color,
        linewidths=1, zorder=10
    )


def generate_summary_image(results, symbol, save_path=None):
    """
    生成回测结果汇总图
    - 累计收益曲线
    - 回撤图
    - 收益分布
    """
    if not results or " equity" not in results:
        return None

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(f"{symbol} 回测结果汇总", fontsize=14, fontweight="bold")

    # 1. 净值曲线
    equity = results["equity"]
    dates = range(len(equity))
    axes[0, 0].plot(dates, equity, color="blue", linewidth=1.5)
    axes[0, 0].set_title("累计净值")
    axes[0, 0].set_ylabel("净值")
    axes[0, 0].grid(True, alpha=0.3)
    axes[0, 0].axhline(y=1.0, color="gray", linestyle="--", alpha=0.5)

    # 2. 回撤
    if "drawdown" in results:
        drawdown = results["drawdown"]
        axes[0, 1].fill_between(range(len(drawdown)), drawdown, 0, color="red", alpha=0.3)
        axes[0, 1].set_title("回撤")
        axes[0, 1].set_ylabel("回撤率")
        axes[0, 1].grid(True, alpha=0.3)

    # 3. 月收益柱状图
    if "monthly_returns" in results:
        monthly = results["monthly_returns"]
        colors = ["green" if v > 0 else "red" for v in monthly.values()]
        axes[1, 0].bar(monthly.keys(), monthly.values(), color=colors, alpha=0.7)
        axes[1, 0].set_title("月收益")
        axes[1, 0].set_ylabel("收益率")
        axes[1, 0].axhline(y=0, color="black", linewidth=0.5)
        axes[1, 0].grid(True, alpha=0.3, axis="y")
        axes[1, 0].tick_params(axis="x", rotation=45)

    # 4. 关键指标文字
    metrics_text = ""
    if "total_return" in results:
        metrics_text += f"总收益率: {results['total_return']:.2%}\n"
    if "sharpe" in results:
        metrics_text += f"夏普比率: {results['sharpe']:.2f}\n"
    if "max_drawdown" in results:
        metrics_text += f"最大回撤: {results['max_drawdown']:.2%}\n"
    if "win_rate" in results:
        metrics_text += f"胜率: {results['win_rate']:.2%}\n"
    if "trade_count" in results:
        metrics_text += f"交易次数: {results['trade_count']}\n"

    axes[1, 1].text(0.1, 0.5, metrics_text, fontsize=12,
                    family="monospace", verticalalignment="center",
                    bbox=dict(boxstyle="round", facecolor="lightgray", alpha=0.5))
    axes[1, 1].axis("off")

    plt.tight_layout()

    if save_path is None:
        save_path = os.path.join(DATA_DIR, f"{symbol}_summary.png")

    fig.savefig(save_path, dpi=120, bbox_inches="tight", facecolor="white")
    print(f"汇总图已保存: {save_path}")
    plt.close(fig)

    return save_path