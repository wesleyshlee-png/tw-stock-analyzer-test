import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from analyzer import fetch_tw_stock_data, calculate_indicators, evaluate_signals
from cfa_analyzer import generate_cfa_report
import json
import pandas as pd

# 設定網頁標題與排版
st.set_page_config(page_title="台股技術分析儀表板", layout="wide")

st.title("📈 台灣股市智慧分析儀表板")
st.write("結合即時技術面 K 線與 CFA 等級的基本面 AI 深度報告。")

# 1. 初始化 Session State
if 'analyzed_symbol' not in st.session_state:
    st.session_state.analyzed_symbol = None
    st.session_state.df_indicators = None
    st.session_state.signal_info = None
    st.session_state.cfa_report = None
    st.session_state.latest_close = None
    st.session_state.change = None
    st.session_state.change_pct = None
    st.session_state.resistance_price = None
    st.session_state.support_price = None

# 2. 注入自訂 CSS (特別強化 section-card 內的文字可讀性)
st.markdown("""
<style>
.glow-badge-green {
    background-color: #1b5e20;
    color: #69f0ae;
    padding: 10px 20px;
    border-radius: 20px;
    font-weight: bold;
    display: inline-block;
    box-shadow: 0 0 10px #1b5e20;
    text-align: center;
    width: 100%;
}
.glow-badge-red {
    background-color: #b71c1c;
    color: #ff5252;
    padding: 10px 20px;
    border-radius: 20px;
    font-weight: bold;
    display: inline-block;
    box-shadow: 0 0 10px #b71c1c;
    text-align: center;
    width: 100%;
}
.glow-badge-orange {
    background-color: #e65100;
    color: #ffd740;
    padding: 10px 20px;
    border-radius: 20px;
    font-weight: bold;
    display: inline-block;
    box-shadow: 0 0 10px #e65100;
    text-align: center;
    width: 100%;
}
.section-card {
    background-color: #161b22 !important;
    padding: 22px;
    border-radius: 8px;
    border: 1px solid #30363d;
    margin-bottom: 15px;
}
/* 強制設定 section-card 內所有層級文字為清晰亮白 */
.section-card, 
.section-card h4, 
.section-card h3, 
.section-card h5, 
.section-card p, 
.section-card li, 
.section-card div,
.section-card span {
    color: #f0f6fc !important;
}
.section-card p {
    font-size: 15px;
    line-height: 1.6;
}
</style>
""", unsafe_allow_html=True)

# 3. 頂部輸入區塊
st.subheader("🔍 步驟一：輸入股票與自訂資訊")
col_in1, col_in2 = st.columns([1, 2])
with col_in1:
    symbol_input = st.text_input("輸入股票代碼 (例: 2330 或 2454)", value="2330").strip()
    api_key_input = st.text_input("輸入 Gemini API 金鑰 (留空則使用系統環境變數)", type="password", help="可在 Google AI Studio 獲取免費的 API Key")
with col_in2:
    extra_news = st.text_area("輸入近期新聞、財報數據或法說會重點 (選填)", height=95, placeholder="在此貼上該股票的最新新聞、法說會資訊或自訂財報數據，以利生成更精準的報告...")

# 側邊欄設定 (只放置圖表繪製的微調設定)
st.sidebar.header("📊 圖表微調參數")
period_options = {
    "1 個月": "1mo",
    "3 個月": "3mo",
    "6 個月": "6mo",
    "1 年": "1y",
    "2 年": "2y",
    "5 年": "5y",
    "歷史最大": "max"
}
period_label = st.sidebar.selectbox("選擇時間範圍", list(period_options.keys()), index=3) # 預設 1 年
period = period_options[period_label]

st.sidebar.subheader("技術分析顯示")
show_ma5 = st.sidebar.checkbox("5日均線 (MA5)", value=True)
show_ma20 = st.sidebar.checkbox("20日均線 (MA20)", value=True)
show_ma60 = st.sidebar.checkbox("60日均線 (MA60)", value=True)
show_rsi = st.sidebar.checkbox("RSI (14)", value=True)
show_macd = st.sidebar.checkbox("MACD", value=False)
show_bb = st.sidebar.checkbox("布林通道 (BBands)", value=True)

# 開始分析大按鈕
start_analysis = st.button("🚀 開始分析並生成全套報告", type="primary", use_container_width=True)

# 觸發運算邏輯
if start_analysis:
    if not symbol_input:
        st.error("請先輸入股票代碼！")
    else:
        try:
            with st.spinner("⏳ 正在獲取股價數據並計算技術指標..."):
                df = fetch_tw_stock_data(symbol_input, period)
                df_indicators = calculate_indicators(df)
                signal_info = evaluate_signals(df_indicators)
                
                latest_close = df_indicators['Close'].iloc[-1]
                prev_close = df_indicators['Close'].iloc[-2]
                change = latest_close - prev_close
                change_pct = (change / prev_close) * 100

                recent_df = df_indicators.tail(20)
                resistance_price = recent_df['High'].max()
                support_price = recent_df['Low'].min()
                
            with st.spinner("⏳ 頂尖 CFA 分析師正在解讀財報與市場消息並生成報告，請稍候..."):
                report_raw = generate_cfa_report(
                    symbol=symbol_input,
                    extra_news=extra_news,
                    api_key=api_key_input if api_key_input else None
                )
                
            # 保存到 session state
            st.session_state.analyzed_symbol = symbol_input
            st.session_state.df_indicators = df_indicators
            st.session_state.signal_info = signal_info
            st.session_state.cfa_report = report_raw
            st.session_state.latest_close = latest_close
            st.session_state.change = change
            st.session_state.change_pct = change_pct
            st.session_state.resistance_price = resistance_price
            st.session_state.support_price = support_price
            
            st.toast("🎉 分析完成！已成功加載與生成報告！")
            
        except Exception as e:
            st.error(f"無法載入股票代碼 '{symbol_input}'。請確認代碼是否正確（例：台積電為 2330）。\n錯誤訊息: {e}")

# 4. 呈現內容 (如果已分析過，則進行呈現)
if st.session_state.analyzed_symbol is not None:
    # 讀取 cache 資料
    active_symbol = st.session_state.analyzed_symbol
    df_indicators = st.session_state.df_indicators
    signal_info = st.session_state.signal_info
    cfa_report_raw = st.session_state.cfa_report
    latest_close = st.session_state.latest_close
    change = st.session_state.change
    change_pct = st.session_state.change_pct
    resistance_price = st.session_state.resistance_price
    support_price = st.session_state.support_price

    st.markdown("---")
    # 顯示頂部公司概況與多空評忘指標
    st.subheader(f"📊 {active_symbol} 即時概況與技術評估")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            label="最新收盤價", 
            value=f"{latest_close:.2f} 元", 
            delta=f"{change:+.2f} 元 ({change_pct:+.2f}%)"
        )
    with col2:
        st.metric(label="綜合技術訊號", value=signal_info['signal'])
    with col3:
        if "偏多" in signal_info['signal']:
            st.markdown('<div class="glow-badge-green">🟢 趨勢展望：偏多操作</div>', unsafe_allow_html=True)
        elif "偏空" in signal_info['signal']:
            st.markdown('<div class="glow-badge-red">🔴 趨勢展望：偏空保守</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="glow-badge-orange">🟡 趨勢展望：區間震盪</div>', unsafe_allow_html=True)

    st.info(f"💡 **技術面診斷原因**：{signal_info['desc']}")

    # 5. 繪製動態 K 線圖
    rows = 1
    row_heights = [0.7]
    subplot_titles = ["K線與均線 (近期 20 日支撐/壓力標註)"]
    
    if show_rsi:
        rows += 1
        row_heights.append(0.2)
        subplot_titles.append("RSI (14)")
        
    if show_macd:
        rows += 1
        row_heights.append(0.2)
        subplot_titles.append("MACD")

    rows += 1
    row_heights.insert(1, 0.15)
    subplot_titles.insert(1, "成交量")
    
    total_height = sum(row_heights)
    normalized_row_heights = [h / total_height for h in row_heights]

    fig = make_subplots(
        rows=rows, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.04,
        subplot_titles=subplot_titles,
        row_width=normalized_row_heights[::-1]
    )

    current_row = 1

    # K 線與均線
    fig.add_trace(
        go.Candlestick(
            x=df_indicators.index,
            open=df_indicators['Open'],
            high=df_indicators['High'],
            low=df_indicators['Low'],
            close=df_indicators['Close'],
            name="K線"
        ),
        row=current_row, col=1
    )

    fig.add_hline(
        y=resistance_price, 
        line_dash="dash", 
        line_color="#ff5252", 
        annotation_text=f" 20日高點壓力: {resistance_price:.2f}", 
        annotation_position="top left", 
        row=current_row, col=1
    )
    fig.add_hline(
        y=support_price, 
        line_dash="dash", 
        line_color="#69f0ae", 
        annotation_text=f" 20日低點支撐: {support_price:.2f}", 
        annotation_position="bottom left", 
        row=current_row, col=1
    )

    if show_ma5:
        fig.add_trace(
            go.Scatter(x=df_indicators.index, y=df_indicators['MA5'], line=dict(color='orange', width=1.5), name="5MA"),
            row=current_row, col=1
        )
    if show_ma20:
        fig.add_trace(
            go.Scatter(x=df_indicators.index, y=df_indicators['MA20'], line=dict(color='magenta', width=1.5), name="20MA"),
            row=current_row, col=1
        )
    if show_ma60:
        fig.add_trace(
            go.Scatter(x=df_indicators.index, y=df_indicators['MA60'], line=dict(color='blue', width=1.5), name="60MA"),
            row=current_row, col=1
        )
        
    if show_bb:
        bbl_cols = [c for c in df_indicators.columns if c.startswith('BBL_')]
        bbu_cols = [c for c in df_indicators.columns if c.startswith('BBU_')]
        bbm_cols = [c for c in df_indicators.columns if c.startswith('BBM_')]
        
        if bbl_cols and bbu_cols and bbm_cols:
            bbl_col = bbl_cols[0]
            bbu_col = bbu_cols[0]
            bbm_col = bbm_cols[0]
            
            fig.add_trace(
                go.Scatter(x=df_indicators.index, y=df_indicators[bbu_col], line=dict(color='rgba(0, 188, 212, 0.45)', width=1.2, dash='dash'), name="布林上軌", legendgroup="BBands"),
                row=current_row, col=1
            )
            fig.add_trace(
                go.Scatter(x=df_indicators.index, y=df_indicators[bbl_col], line=dict(color='rgba(0, 188, 212, 0.45)', width=1.2, dash='dash'), fill='tonexty', fillcolor='rgba(0, 188, 212, 0.07)', name="布林下軌", legendgroup="BBands"),
                row=current_row, col=1
            )
            fig.add_trace(
                go.Scatter(x=df_indicators.index, y=df_indicators[bbm_col], line=dict(color='rgba(255, 213, 79, 0.4)', width=1.5), name="布林中軌", legendgroup="BBands"),
                row=current_row, col=1
            )
        else:
            st.sidebar.warning("⚠️ 數據不足，無法顯示布林通道")
        
    current_row += 1

    # 成交量
    colors = ['red' if close >= open_val else 'green' for open_val, close in zip(df_indicators['Open'], df_indicators['Close'])]
    fig.add_trace(
        go.Bar(x=df_indicators.index, y=df_indicators['Volume'], marker_color=colors, name="成交量"),
        row=current_row, col=1
    )
    current_row += 1

    # RSI
    if show_rsi:
        fig.add_trace(
            go.Scatter(x=df_indicators.index, y=df_indicators['RSI14'], line=dict(color='purple', width=1.5), name="RSI(14)"),
            row=current_row, col=1
        )
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=current_row, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=current_row, col=1)
        fig.add_hrect(y0=30, y1=70, line_width=0, fillcolor="purple", opacity=0.05, row=current_row, col=1)
        current_row += 1

    # MACD
    if show_macd:
        macd_col = [c for c in df_indicators.columns if c.startswith('MACD_')][0]
        macds_col = [c for c in df_indicators.columns if c.startswith('MACDs_')][0]
        macdh_col = [c for c in df_indicators.columns if c.startswith('MACDh_')][0]
        
        fig.add_trace(
            go.Scatter(x=df_indicators.index, y=df_indicators[macd_col], line=dict(color='white', width=1.5), name="MACD"),
            row=current_row, col=1
        )
        fig.add_trace(
            go.Scatter(x=df_indicators.index, y=df_indicators[macds_col], line=dict(color='yellow', width=1.5), name="Signal"),
            row=current_row, col=1
        )
        hist_colors = ['red' if val >= 0 else 'green' for val in df_indicators[macdh_col]]
        fig.add_trace(
            go.Bar(x=df_indicators.index, y=df_indicators[macdh_col], marker_color=hist_colors, name="Hist"),
            row=current_row, col=1
        )

    # 隱藏假日與未開盤的空缺
    all_dates = pd.date_range(start=df_indicators.index.min(), end=df_indicators.index.max())
    obs_dates = df_indicators.index
    missing_dates = [d.strftime("%Y-%m-%d") for d in all_dates if d not in obs_dates]
    fig.update_xaxes(rangebreaks=[dict(values=missing_dates)])

    fig.update_layout(
        height=300 + (rows * 150),
        template="plotly_dark",
        xaxis_rangeslider_visible=False,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # 6. 下方分頁：CFA 分析報告 與 詳細數據
    tab1, tab2 = st.tabs(["📊 CFA 專業分析報告", "📋 歷史數據細節"])
    
    with tab1:
        st.subheader("📊 CFA & 資深產業研究員 - 台股公司分析報告")
        
        try:
            report_data = json.loads(cfa_report_raw)
            
            # 呈現公司基本資料
            st.subheader(f"📊 一、 公司速寫與產業地位 ({report_data.get('company_name_zh', active_symbol)})")
            
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                st.markdown(f"""
                <div class="section-card" style="border-left: 4px solid #00acc1;">
                    <h4>🏢 公司簡介與產品佔比</h4>
                    <p>{report_data.get('company_summary')}</p>
                    <h4>⛓️ 供應鏈位置</h4>
                    <p>{report_data.get('supply_chain_position')}</p>
                </div>
                """, unsafe_allow_html=True)
            with col_c2:
                st.markdown("<h4>⚔️ 主要競爭對手</h4>", unsafe_allow_html=True)
                for comp in report_data.get('key_competitors', []):
                    st.markdown(f'<div class="section-card" style="padding: 10px; margin-bottom:8px;">👥 {comp}</div>', unsafe_allow_html=True)
                    
            # 二、 基本面診斷
            st.subheader("📈 二、 基本面診斷 (Fundamental)")
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                st.markdown(f"""
                <div class="section-card" style="border-left: 4px solid #4caf50;">
                    <h4>📊 營收與獲利趨勢</h4>
                    <p>{report_data.get('revenue_margins_analysis')}</p>
                </div>
                """, unsafe_allow_html=True)
            with col_f2:
                st.markdown(f"""
                <div class="section-card" style="border-left: 4px solid #ab47bc;">
                    <h4>💰 估值與報酬評估</h4>
                    <p>{report_data.get('valuation_assessment')}</p>
                    <h4>💵 股息政策與殖利率</h4>
                    <p>{report_data.get('dividend_assessment')}</p>
                </div>
                """, unsafe_allow_html=True)
                
            # 三、 籌碼與技術面觀察重點
            st.subheader("🕵️ 三、 籌碼與技術面觀察重點")
            col_t1, col_t2 = st.columns(2)
            with col_t1:
                st.markdown("<h4>🐳 籌碼動向重點</h4>", unsafe_allow_html=True)
                for chip in report_data.get('chips_indicators', []):
                    st.markdown(f'<div class="section-card" style="padding: 12px; margin-bottom: 8px; border-left: 3px solid #ff9800;">🔹 {chip}</div>', unsafe_allow_html=True)
            with col_t2:
                st.markdown("<h4>📊 技術指標關注</h4>", unsafe_allow_html=True)
                for tech in report_data.get('technical_indicators', []):
                    st.markdown(f'<div class="section-card" style="padding: 12px; margin-bottom: 8px; border-left: 3px solid #2196f3;">🔸 {tech}</div>', unsafe_allow_html=True)
                    
            # 四、 催化劑與風險提示
            st.subheader("💡 四、 催化劑與風險提示 (Pros & Cons)")
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                st.markdown("<h4>🟢 利多與潛在催化劑</h4>", unsafe_allow_html=True)
                for cat in report_data.get('catalysts', []):
                    st.success(f"👍 {cat}")
            with col_p2:
                st.markdown("<h4>🔴 利空與潛在風險</h4>", unsafe_allow_html=True)
                for risk in report_data.get('risks', []):
                    st.error(f"👎 {risk}")
                    
            # 五、 總結與觀察建議
            st.subheader("🎯 五、 總結與觀察建議")
            st.markdown(f"""
            <div class="section-card" style="border-left: 5px solid #ffb300; background-color: rgba(255, 179, 0, 0.05);">
                <h4>🎯 核心投資定位</h4>
                <p>{report_data.get('investment_verdict')}</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<h4>📅 未來 1~3 個月緊盯關鍵事件</h4>", unsafe_allow_html=True)
            for ev in report_data.get('key_events_to_watch', []):
                st.info(f"🔔 {ev}")
                
            st.markdown("---")
            st.caption("⚠️ **投資風險警語**：本報告由 AI 財務助理產出，僅供研究參考，非直接買賣建議。投資有風險，操作前請獨立審慎評估。")
            
        except Exception as err:
            st.error(f"解析報告 JSON 時發生錯誤，以下為原始文字：")
            st.markdown(cfa_report_raw)
        
    with tab2:
        st.subheader("📋 歷史股價數據 (最近 10 筆)")
        df_display = df_indicators.copy()
        df_display.index = df_display.index.strftime('%Y-%m-%d')
        st.dataframe(df_display.tail(10)[['Open', 'High', 'Low', 'Close', 'Volume']].iloc[::-1], use_container_width=True)
else:
    st.markdown("---")
    st.info("💡 **使用說明**：請在上方輸入股票代碼（若有新聞/法說會資訊可貼在右側欄位），點擊「開始分析並生成全套報告」即可開始！")
