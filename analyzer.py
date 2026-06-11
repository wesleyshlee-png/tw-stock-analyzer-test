import pandas as pd
import yfinance as yf
import pandas_ta_classic as ta

def fetch_tw_stock_data(symbol: str, period: str = "1y") -> pd.DataFrame:
    """
    獲取台灣股市的歷史股價數據，自動支援上市 (.TW) 與上櫃 (.TWO) 股票。
    """
    clean_symbol = symbol.strip()
    
    # 若已指定後綴，直接獲取
    if clean_symbol.endswith(".TW") or clean_symbol.endswith(".TWO"):
        print(f"正在從 Yahoo Finance 下載 {clean_symbol} 的數據...")
        ticker = yf.Ticker(clean_symbol)
        df = ticker.history(period=period)
        if df.empty:
            raise ValueError(f"找不到代碼為 {clean_symbol} 的數據。")
        return df

    # 否則，先嘗試上市 (.TW)
    ticker_symbol = f"{clean_symbol}.TW"
    print(f"正在從 Yahoo Finance 下載 {ticker_symbol} 的數據...")
    ticker = yf.Ticker(ticker_symbol)
    try:
        df = ticker.history(period=period)
    except Exception:
        df = pd.DataFrame()

    # 若上市數據為空，嘗試上櫃 (.TWO)
    if df.empty:
        ticker_symbol = f"{clean_symbol}.TWO"
        print(f"上市代碼找不到，正在嘗試下載上櫃 {ticker_symbol} 的數據...")
        ticker = yf.Ticker(ticker_symbol)
        try:
            df = ticker.history(period=period)
        except Exception:
            df = pd.DataFrame()

    if df.empty:
        raise ValueError(f"找不到代碼為 {clean_symbol} 的上市 (.TW) 或上櫃 (.TWO) 數據，請檢查代碼。")
        
    return df

def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    計算技術指標 (MA, RSI, MACD)。
    """
    # 確保 DataFrame 不為空
    if df.empty:
        return df

    # 複製一份以防修改原始數據
    df_indicators = df.copy()

    # 計算移動平均線 (MA)
    df_indicators['MA5'] = ta.sma(df_indicators['Close'], length=5)
    df_indicators['MA20'] = ta.sma(df_indicators['Close'], length=20)
    df_indicators['MA60'] = ta.sma(df_indicators['Close'], length=60)

    # 計算相對強弱指標 (RSI)
    df_indicators['RSI14'] = ta.rsi(df_indicators['Close'], length=14)

    # 計算 MACD
    macd_df = ta.macd(df_indicators['Close'], fast=12, slow=26, signal=9)
    if macd_df is not None:
        df_indicators = pd.concat([df_indicators, macd_df], axis=1)

    # 計算布林通道 (Bollinger Bands)
    bb_df = ta.bbands(df_indicators['Close'], length=20, std=2)
    if bb_df is not None:
        df_indicators = pd.concat([df_indicators, bb_df], axis=1)

    return df_indicators

def evaluate_signals(df_indicators: pd.DataFrame) -> dict:
    """
    根據技術指標評估綜合多空訊號。
    """
    if df_indicators.empty or len(df_indicators) < 60:
        return {"signal": "資料不足", "color": "gray", "desc": "歷史數據不足，無法評估訊號。"}
        
    latest = df_indicators.iloc[-1]
    
    close = latest['Close']
    ma5 = latest['MA5']
    ma20 = latest['MA20']
    ma60 = latest['MA60']
    rsi = latest['RSI14']
    
    score = 0
    reasons = []
    
    # 均線多空評估
    if close > ma20:
        score += 1
        reasons.append("股價站於月線 (20MA) 之上")
    else:
        score -= 1
        reasons.append("股價落於月線 (20MA) 之下")
        
    if close > ma60:
        score += 1
        reasons.append("股價站於季線 (60MA) 之上")
    else:
        score -= 1
        reasons.append("股價落於季線 (60MA) 之下")
        
    if ma5 > ma20:
        score += 1
        reasons.append("5日均線高於月線，呈多頭排列")
    else:
        score -= 1
        reasons.append("5日均線低於月線，呈空頭排列")
        
    # RSI 強弱評估
    if rsi > 70:
        reasons.append("RSI 指標大於 70，進入超買區（留意高檔拉回風險）")
    elif rsi < 30:
        score += 0.5  # 超跌反彈機會
        reasons.append("RSI 指標低於 30，進入超賣區（留意短線反彈契機）")
        
    # 決定綜合訊號
    if score >= 2:
        signal = "偏多 (Bullish)"
        color = "green"
        desc = "。".join(reasons) + "，短期趨勢偏強。"
    elif score <= -2:
        signal = "偏空 (Bearish)"
        color = "red"
        desc = "。".join(reasons) + "，短期趨勢偏弱。"
    else:
        signal = "中立 (Neutral)"
        color = "orange"
        desc = "。".join(reasons) + "，股價呈現區間震盪。"
        
    return {
        "signal": signal,
        "color": color,
        "desc": desc
    }

if __name__ == "__main__":
    # 測試程式碼
    try:
        df = fetch_tw_stock_data("2330", period="3mo")
        df_with_indicators = calculate_indicators(df)
        print("數據獲取與指標計算成功！數據前五行：")
        print(df_with_indicators[['Close', 'MA5', 'MA20', 'RSI14']].tail())
    except Exception as e:
        print(f"錯誤: {e}")
