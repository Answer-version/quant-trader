# 量化交易系统

> 股票量化回测 + 30分钟K线图表 + Telegram 信号推送

## 功能

- 📊 **回测引擎**: Backtrader，支持均线交叉等多种策略
- 📈 **K线图表**: 30分钟K线，MA5/MA20 均线叠加，买卖信号标注在图上
- 🔔 **信号推送**: 新浪股票数据，检测到交易信号自动通过 Telegram 推送
- 🖼️ **图表推送**: K线图 + 信号标记图片直接发到 TG

## 技术栈

| 模块 | 工具 |
|------|------|
| 回测 | Backtrader |
| 行情 | 新浪股票 API（akshare 封装） |
| 图表 | Matplotlib + mplfinance |
| 推送 | python-telegram-bot |

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置

编辑 `config.py`:

```python
# Telegram 配置
TG_BOT_TOKEN = "your_bot_token_from_botfather"
TG_CHAT_ID = "your_telegram_user_id"  # 发消息给 @userinfobot 获取

# 股票代码
STOCK_CODES = ["sh600000", "sz000858"]  # 支持多只
```

### 3. 运行回测

```bash
python backtest.py
```

运行后：
- 自动获取最近2个月30分钟K线
- 执行 MA5 × MA20 均线交叉策略回测
- 生成带信号标注的K线图
- 通过 Telegram 推送报告

### 4. 定时监控

```bash
# 单次检查信号
python monitor.py --once

# 持续定时监控（每30分钟检查信号）
python monitor.py
```

## 策略说明

**MA5 × MA20 均线交叉**
- 📈 MA5 上穿 MA20 → 买入信号
- 📉 MA5 下穿 MA20 → 卖出信号

## 图表示例

K线图上会标注：
- 🟢 绿色箭头 ↑ = 买入信号（在K线下方）
- 🔴 红色箭头 ↓ = 卖出信号（在K线上方）
- 蓝色线 = MA5
- 红色线 = MA20

## 文件结构

```
quant-trader/
├── config.py          # 配置文件
├── data_fetcher.py    # 新浪行情获取
├── strategy.py        # Backtrader 策略
├── chart_generator.py # K线图生成
├── telegram_sender.py # TG 推送
├── backtest.py        # 回测入口
├── monitor.py         # 定时监控
├── requirements.txt
└── data/              # 数据缓存目录
```

## 免责声明

本工具仅供学习和研究使用，不构成投资建议。量化交易有风险，决策请自负。