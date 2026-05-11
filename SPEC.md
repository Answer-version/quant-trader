# 量化交易系统 - 技术规格

## 1. 项目概述

- **名称**: quant-trader
- **功能**: 股票量化回测 + 30分钟K线图表 + 交易信号提醒
- **推送渠道**: Telegram

---

## 2. 技术栈

| 模块 | 工具 |
|------|------|
| 回测引擎 | Backtrader |
| 行情数据 | 新浪股票 API（akshare 封装） |
| 图表 | Matplotlib + mplfinance |
| 图表标注 | 买入/卖出信号标记在K线图上 |
| Telegram 推送 | python-telegram-bot |
| 数据存储 | SQLite（记录持仓/交易信号） |

---

## 3. 策略方向（示例）

**均线交叉策略（可扩展）**
- 短期MA5 上穿 长期MA20 → 买入信号 📈
- 短期MA5 下穿 长期MA20 → 卖出信号 📉
- 30分钟K线，回测最近2个月

---

## 4. 文件结构

```
quant-trader/
├── SPEC.md
├── README.md
├── requirements.txt
├── config.py          # 配置（TG Token、股票代码等）
├── data_fetcher.py    # 新浪行情获取
├── strategy.py        # 交易策略（Backtrader）
├── chart_generator.py # K线图 + 信号标注生成
├── telegram_sender.py # TG 推送
├── backtest.py        # 回测入口
├── monitor.py         # 监控+定时推送脚本
└── data/              # 数据缓存目录
```

---

## 5. 图表规范

- **K线类型**: 30分钟K线
- **时间范围**: 最近2个月（约1000根30分钟K线）
- **标注**: 
  - 🟢 买入箭头（↑）标记在K线下方
  - 🔴 卖出箭头（↓）标记在K线上方
  - MA5 / MA20 均线叠加
- **图片格式**: PNG，通过 TG 发送

---

## 6. 新浪股票数据接口

```python
# 30分钟K线（复权）
http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData

?symbol=sh600000    # 股票代码（sh=上证, sz=深证）
&scale=30           # 30分钟K线
&ma=5               # 均线条数
&datalen=1000       # 数据长度（~2个月）
```

---

## 7. Telegram 配置

```python
TG_BOT_TOKEN=xxx
TG_CHAT_ID=xxx       # 你的 Telegram User ID
```

---

## 8. 使用方式

```bash
# 安装依赖
pip install backtrader akshare matplotlib mplfinance python-telegram-bot pandas

# 快速回测
python backtest.py

# 监控+推送（定时任务）
python monitor.py
```