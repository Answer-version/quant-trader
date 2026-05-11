"""
交易策略 - 均线交叉策略（Backtrader）
"""
import backtrader as bt
import pandas as pd
from datetime import datetime
from config import SHORT_MA, LONG_MA, INITIAL_CASH


class MaCrossStrategy(bt.Strategy):
    """
    简单均线交叉策略
    - MA5 上穿 MA20 → 买入
    - MA5 下穿 MA20 → 卖出
    """
    params = (
        ("short_ma", SHORT_MA),
        ("long_ma", LONG_MA),
    )

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.order = None
        self.buyprice = None
        self.buycomm = None

        # 添加均线指标
        self.sma_short = bt.indicators.SimpleMovingAverage(
            self.datas[0], period=self.params.short_ma
        )
        self.sma_long = bt.indicators.SimpleMovingAverage(
            self.datas[0], period=self.params.long_ma
        )

        # 交叉信号
        self.crossover = bt.indicators.CrossOver(self.sma_short, self.sma_long)

        # 记录交易信号
        self.signals = []

    def log(self, txt, dt=None):
        """日志"""
        dt = dt or self.datas[0].datetime.date(0)
        print(f"[{dt.isoformat()}] {txt}")

    def notify_order(self, order):
        """订单通知"""
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f"买入执行 @ {order.executed.price:.2f}")
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:
                self.log(f"卖出执行 @ {order.executed.price:.2f}")

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log("订单被拒绝/取消")

        self.order = None

    def notify_trade(self, trade):
        """成交通知"""
        if not trade.isclosed:
            return
        self.log(f"交易利润: 毛利润 {trade.pnl:.2f}, 净利润 {trade.pnlcomm:.2f}")

    def next(self):
        """每个K线执行一次"""
        if self.order:
            return

        # 交叉信号
        if self.crossover > 0:  # 金叉 - 买入
            self.log(f"【买入信号】MA{self.params.short_ma} 上穿 MA{self.params.long_ma}, 价格={self.dataclose[0]:.2f}")
            self.order = self.buy()
            # 记录信号
            self.signals.append({
                "datetime": self.datas[0].datetime.date(0),
                "type": "buy",
                "price": self.dataclose[0]
            })

        elif self.crossover < 0:  # 死叉 - 卖出
            if self.position:  # 有持仓才卖
                self.log(f"【卖出信号】MA{self.params.short_ma} 下穿 MA{self.params.long_ma}, 价格={self.dataclose[0]:.2f}")
                self.order = self.sell()
                self.signals.append({
                    "datetime": self.datas[0].datetime.date(0),
                    "type": "sell",
                    "price": self.dataclose[0]
                })


def run_backtest(symbol, df_data):
    """
    运行回测

    Args:
        symbol: 股票代码
        df_data: DataFrame，含 datetime/open/high/low/close/volume 列

    Returns:
        dict: 回测结果，包含 signals、equity、metrics 等
    """
    if df_data is None or df_data.empty:
        print(f"[{symbol}] 数据为空，跳过回测")
        return None

    # 准备数据格式（Backtrader 需要 datetime 为 index）
    df = df_data.copy()
    df.set_index("datetime", inplace=True)
    df.index = pd.to_datetime(df.index)

    # Backtrader 需要特定的列名
    df.columns = [col.lower() for col in df.columns]

    # 转换为 Backtrader 数据格式
    data = bt.feeds.PandasData(
        dataname=df,
        datetime=None,
        open="open",
        high="high",
        low="low",
        close="close",
        volume="volume",
        openinterest=-1
    )

    # 创建 Cerebro 引擎
    cerebro = bt.Cerebro()

    # 添加数据
    cerebro.adddata(data)

    # 添加策略
    cerebro.addstrategy(
        MaCrossStrategy,
        short_ma=SHORT_MA,
        long_ma=LONG_MA
    )

    # 设置初始资金
    cerebro.broker.setcash(INITIAL_CASH)

    # 设置交易佣金（万一之五）
    cerebro.broker.setcommission(commission=0.0005)

    # 添加分析器
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe", riskfreerate=0.02, annualize=True)
    cerebro.addanalyzer(bt.analyzers.Returns, _name="returns")
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="trades")

    # 打印初始资金
    print(f"\n{'='*50}")
    print(f"回测股票: {symbol}")
    print(f"初始资金: {INITIAL_CASH}")
    print(f"策略: MA{SHORT_MA} x MA{LONG_MA} 均线交叉")
    print(f"{'='*50}")

    # 运行回测
    results = cerebro.run()

    # 获取策略实例（最后一个）
    strategy = results[0]

    # 提取分析结果
    final_value = cerebro.broker.getvalue()
    total_return = (final_value - INITIAL_CASH) / INITIAL_CASH

    print(f"\n回测结束")
    print(f"最终净值: {final_value:.2f}")
    print(f"总收益率: {total_return:.2%}")

    # 提取分析指标
    try:
        drawdown_info = strategy.analyzers.drawdown.get_analysis()
        sharpe_info = strategy.analyzers.sharpe.get_analysis()
        returns_info = strategy.analyzers.returns.get_analysis()
        trades_info = strategy.analyzers.trades.get_analysis()

        max_drawdown = drawdown_info.get("max", {}).get("drawdown", 0)
        sharpe_ratio = sharpe_info.get("sharperatio", None)
        if sharpe_ratio and sharpe_ratio != float("inf"):
            sharpe_ratio = round(sharpe_ratio, 2)

        win_rate = 0
        total_trades = 0
        if "total" in trades_info:
            total_trades = trades_info["total"].get("total", 0)
        if "won" in trades_info:
            won_trades = trades_info["won"].get("total", 0)
            if total_trades > 0:
                win_rate = won_trades / total_trades

        metrics = {
            "total_return": total_return,
            "final_value": final_value,
            "max_drawdown": max_drawdown / 100 if max_drawdown else 0,
            "sharpe": sharpe_ratio,
            "win_rate": win_rate,
            "trade_count": total_trades
        }

        print(f"夏普比率: {sharpe_ratio}")
        print(f"最大回撤: {max_drawdown:.2f}%")
        print(f"交易次数: {total_trades}")
        print(f"胜率: {win_rate:.2%}")

    except Exception as e:
        print(f"提取分析指标失败: {e}")
        metrics = {"total_return": total_return, "final_value": final_value}

    # 返回结果
    return {
        "symbol": symbol,
        "signals": strategy.signals,
        "metrics": metrics,
        "initial_cash": INITIAL_CASH,
        "final_value": final_value,
        "strategy": strategy,
        "cerebro": cerebro
    }