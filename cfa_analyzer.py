import os
import yfinance as yf
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List

# 載入同目錄下的 .env 檔案中的環境變數
env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                try:
                    key, val = line.strip().split("=", 1)
                    os.environ[key] = val.strip().strip('"').strip("'")
                except ValueError:
                    pass

class CFAStockReport(BaseModel):
    company_name_zh: str = Field(description="公司中文官方名稱，例如：台積電、聯發科")
    company_summary: str = Field(description="公司簡介與主營業務說明（繁體中文）")
    product_mix: str = Field(description="主要產品線與營業額營收佔比說明（繁體中文）")
    supply_chain_position: str = Field(description="在半導體或電子產業供應鏈中的位置（例如：上游晶圓代工、中游封裝、下游系統組裝）")
    key_competitors: List[str] = Field(description="國內或國外主要競爭對手列表")
    
    revenue_margins_analysis: str = Field(description="月營收表現 (MoM/YoY)、毛利率、營業利益率、稅後純益率等獲利趨勢分析")
    valuation_assessment: str = Field(description="目前的本益比 (P/E)、股價淨值比 (P/B)、股東權益報酬率 (ROE) 評估合理性與定位")
    dividend_assessment: str = Field(description="歷年配息穩定度與預估殖利率分析")
    
    chips_indicators: List[str] = Field(description="分析這檔股票近期應特別留意的關鍵籌碼指標（例如：外資/投信連買、融資融券變化、分點動向）")
    technical_indicators: List[str] = Field(description="目前應關注的技術面關鍵（例如：關鍵均線支撐與壓力、量價關係、指標黃金交叉/死亡交叉等）")
    
    catalysts: List[str] = Field(description="利多與潛在催化劑列表（如新廠產能開出、拿下大客戶訂單、產業進入旺季等）")
    risks: List[str] = Field(description="利空與潛在風險列表（如匯損風險、庫存過高、競爭者削價、終端需求疲軟等）")
    
    investment_verdict: str = Field(description="用3~5句話總結這檔股票目前的投資價值與定位（例如：高成長股、穩定價值定存股、高波動景氣循環股等）")
    key_events_to_watch: List[str] = Field(description="未來 1~3 個月投資人必須緊盯的關鍵事件（如：法說會、某項產品出貨數據、特定總經指標）")

def generate_cfa_report(symbol: str, extra_news: str = "", api_key: str = None) -> str:
    """
    獲取台灣股市的財務與基本面數據，並呼叫 Gemini API 生成專業的 CFA 報告。
    """
    clean_symbol = symbol.strip()
    info = None
    ticker_symbol = clean_symbol

    # 1. 獲取 yfinance 數據
    if clean_symbol.endswith(".TW") or clean_symbol.endswith(".TWO"):
        try:
            ticker = yf.Ticker(clean_symbol)
            info = ticker.info
            if not info or 'longName' not in info:
                raise ValueError("無有效公司名稱")
        except Exception as e:
            return f"錯誤：無法獲取股票 {clean_symbol} 的數據。請確認代碼是否正確。原錯誤訊息：{e}"
    else:
        # 先嘗試上市 (.TW)
        ticker_symbol = f"{clean_symbol}.TW"
        try:
            ticker = yf.Ticker(ticker_symbol)
            info = ticker.info
            if not info or 'longName' not in info:
                raise ValueError("無有效公司名稱")
        except Exception:
            # 失敗則嘗試上櫃 (.TWO)
            ticker_symbol = f"{clean_symbol}.TWO"
            try:
                ticker = yf.Ticker(ticker_symbol)
                info = ticker.info
                if not info or 'longName' not in info:
                    raise ValueError("無有效公司名稱")
            except Exception as e:
                return f"錯誤：無法獲取股票 {clean_symbol} 的上市 (.TW) 或上櫃 (.TWO) 數據。請確認代碼是否正確。"

    # 提取基本財務指標
    stock_name = info.get('longName', '未知')
    industry = info.get('industry', '未知')
    sector = info.get('sector', '未知')
    business_summary = info.get('longBusinessSummary', '無資料')
    
    pe = info.get('trailingPE', '無資料')
    pb = info.get('priceToBook', '無資料')
    roe = info.get('returnOnEquity', '無資料')
    if isinstance(roe, (int, float)):
        roe = f"{roe * 100:.2f}%"
        
    div_yield = info.get('dividendYield', '無資料')
    if isinstance(div_yield, (int, float)):
        div_yield = f"{div_yield * 100:.2f}%"

    # 獲取利潤率與營收增長
    profit_margins = info.get('profitMargins', '無資料')
    if isinstance(profit_margins, (int, float)):
        profit_margins = f"{profit_margins * 100:.2f}%"
        
    operating_margins = info.get('operatingMargins', '無資料')
    if isinstance(operating_margins, (int, float)):
        operating_margins = f"{operating_margins * 100:.2f}%"
        
    gross_margins = info.get('grossMargins', '無資料')
    if isinstance(gross_margins, (int, float)):
        gross_margins = f"{gross_margins * 100:.2f}%"

    revenue_growth = info.get('revenueGrowth', '無資料')
    if isinstance(revenue_growth, (int, float)):
        revenue_growth = f"{revenue_growth * 100:.2f}%"

    # 彙整硬數據
    financial_data_summary = f"""
【基本資料與最新數據】
- 股票代碼與名稱: {ticker_symbol} ({stock_name})
- 產業類別: {sector} / {industry}
- 本益比 (P/E): {pe}
- 股價淨值比 (P/B): {pb}
- 股東權益報酬率 (ROE): {roe}
- 預估股息殖利率: {div_yield}
- 毛利率 (Gross Margin): {gross_margins}
- 營業利益率 (Operating Margin): {operating_margins}
- 稅後純益率 (Profit Margin): {profit_margins}
- 營收年增率 (Revenue Growth YoY): {revenue_growth}
- 公司業務簡介 (英文): {business_summary[:600]}...
"""

    # 2. 構建 Gemini Prompt
    system_instruction = """
你是一位頂尖的「台股特許金融分析師（CFA）」與「資深產業研究員」。你擁有強大的財報解讀能力、籌碼分析經驗，並對台灣的電子鏈、傳產、金融等產業生態瞭若指掌。
請嚴格遵循以下分析維度與原則：
1. 本土化語境：使用台灣股市慣用術語（如：三大法人、融資融券、月營收 MoM/YoY、三率三升/降、除權息、殖利率、護城河等）。
2. 客觀中立：不提供直接的買賣建議，而是提供「風險提示」與「觀察重點」。
3. 結構化輸出：請使用 Markdown 格式（標題、清單、表格）讓排版易讀。
"""

    prompt = f"""
請針對以下股票數據與額外資訊，撰寫一份結構化、客觀且具備深度的「台股公司分析報告」。

{financial_data_summary}

【使用者提供的額外資訊與近期新聞/財報數據】
{extra_news if extra_news.strip() else "無額外輸入"}

---
【報告輸出格式要求】
請完全依照以下 Markdown 結構輸出：

## 📊 一、 公司速寫與產業地位
* 公司簡介：主要業務與產品佔比（請結合你對該公司的了解，將英文簡介轉化為繁體中文，並說明其主營產品）。
* 產業地位：在供應鏈中的位置（上/中/下游），以及主要的競爭對手。

## 📈 二、 基本面診斷 (Fundamental)
* 營收與獲利：結合給出的毛利率、營業利益率、稅後純益率與營收年增率，分析近期表現。
* 估值與報酬：評估本益比 (P/E)、股價淨值比 (P/B)、股東權益報酬率 (ROE) 是否合理。
* 股息政策：分析歷年配息穩定度與預估殖利率。

## 🕵️ 三、 籌碼與技術面觀察重點 (Chips & Technical)
* 籌碼動向：提示針對這檔股票，近期應特別留意的籌碼指標（例如：外資/投信連買連賣、主力券商動向）。
* 技術型態：提示目前應關注的技術面關鍵（例如：關鍵均線支撐/壓力、量價關係）。
*(註：若無最新即時盤中數據，請提供「分析該檔股票時通常要看哪幾個關鍵指標」的建議)*

## 💡 四、 催化劑與風險提示 (Pros & Cons)
* 🟢 利多與潛在催化劑 (Catalysts)：例如新廠產能開出、拿下大客戶訂單、產業進入旺季等。
* 🔴 利空與潛在風險 (Risks)：例如匯損風險、庫存過高、競爭者削價、終端需求疲軟等。

## 🎯 五、 總結與觀察建議
* 用 3~5 句話總結這檔股票目前的投資價值與定位（如：成長股、價值定存股、景氣循環股）。
* 列出未來 1~3 個月投資人必須緊盯的「關鍵事件」（如：法說會、某項產品出貨數據、特定總經指標）。

---
免責聲明提醒：在報告最末加上一句標準的投資風險警語。
"""

    # 3. 呼叫 Gemini API
    # 支援手動傳入 API Key，否則使用預設環境變數
    if api_key:
        client = genai.Client(api_key=api_key)
    else:
        # 如果環境變數中沒有，則提示錯誤
        if not os.environ.get("GEMINI_API_KEY"):
            return "錯誤：找不到 GEMINI_API_KEY。請在 Streamlit 設定或環境變數中提供您的 API 金鑰。"
        client = genai.Client()

    try:
        response = client.models.generate_content(
            model='gemini-3.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.3, # 低溫以維持客觀與穩定度
                response_mime_type="application/json",
                response_schema=CFAStockReport,
            )
        )
        return response.text
    except Exception as e:
        return f"錯誤：呼叫 Gemini API 時發生異常。原錯誤訊息：{e}"
