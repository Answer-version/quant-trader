"""
数据获取模块 - 新浪股票30分钟K线
"""
import requests
import pandas as pd
import json
import time
from datetime import datetime, timedelta
from config import STOCK_CODES, KLINE_SIZE, START_DATE, END_DATE, DATA_DIR
import os


def fetch_sina_kline(symbol, scale=30, datalen=1000):
    """
    从新浪获取30分钟K线数据

    Args:
        symbol: 股票代码，如 sh600000
        scale: K线周期（分钟），默认30
        datalen: 获取数据条数，默认1000条
    Returns:
        DataFrame: 包含 datetime, open, high, low, close, volume
    """
    url = "http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData"

    params = {
        "symbol": symbol,
        "scale": scale,
        "ma": "no",  # 不带均线，我们自己算
        "datalen": datalen
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "http://finance.sina.com.cn/"
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        data = response.json()

        if not data:
            print(f"[{symbol}] 未获取到数据")
            return pd.DataFrame()

        df = pd.DataFrame(data)
        df = df.rename(columns={
            "day": "datetime",
            "open": "open",
            "high": "high",
            "low": "low",
            "close": "close",
            "volume": "volume"
        })

        # 转换类型
        df["open"] = df["open"].astype(float)
        df["high"] = df["high"].astype(float)
        df["low"] = df["low"].astype(float)
        df["close"] = df["close"].astype(float)
        df["volume"] = df["volume"].astype(float)
        df["datetime"] = pd.to_datetime(df["datetime"])

        # 按时间排序
        df = df.sort_values("datetime").reset_index(drop=True)

        # 过滤日期范围
        start_dt = pd.to_datetime(START_DATE)
        end_dt = pd.to_datetime(END_DATE)
        df = df[(df["datetime"] >= start_dt) & (df["datetime"] <= end_dt)]

        print(f"[{symbol}] 获取到 {len(df)} 条 {scale}分钟K线")
        return df

    except Exception as e:
        print(f"[{symbol}] 获取数据失败: {e}")
        return pd.DataFrame()


def fetch_all_stocks():
    """
    获取配置中所有股票的数据
    """
    all_data = {}
    for code in STOCK_CODES:
        print(f"\n正在获取 {code} ...")
        df = fetch_sina_kline(code, scale=KLINE_SIZE, datalen=1000)
        if not df.empty:
            # 缓存到本地
            cache_path = os.path.join(DATA_DIR, f"{code}_{KLINE_SIZE}m.parquet")
            df.to_parquet(cache_path)
            print(f"[{code}] 缓存已保存: {cache_path}")
            all_data[code] = df
        else:
            print(f"[{code}] 数据为空，跳过")
        time.sleep(0.5)  # 避免请求过快

    return all_data


def load_cached_data(symbol):
    """
    加载本地缓存数据
    """
    cache_path = os.path.join(DATA_DIR, f"{symbol}_{KLINE_SIZE}m.parquet")
    if os.path.exists(cache_path):
        return pd.read_parquet(cache_path)
    return None


if __name__ == "__main__":
    # 测试数据获取
    data = fetch_all_stocks()
    for code, df in data.items():
        print(f"\n{code} 最新数据:")
        print(df.tail(5))