import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import datetime
import urllib.request
import json

# ==============================================================================
# 1. 页面基本配置
# ==============================================================================
st.set_page_config(
    page_title="StockVal - 智能股票公道价估值器",
    page_icon="💡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==============================================================================
# 2. 国际化多语言字典 (I18N: 中文 / English)
# ==============================================================================
TEXTS = {
    "zh": {
        "title": "💡 智能股票公道价估值器",
        "subtitle": "小白也能看懂的多维度股票公允价值测算平台 | 支持马来西亚股市 (Bursa) 与美股 (US Equities)",
        "lang_select": "语言 / Language",
        "market_label": "📌 步骤 1：选择市场或输入股票代码",
        "market_my": "🇲🇾 马来西亚股市 (Bursa Malaysia)",
        "market_us": "🇺🇸 美国股市 (US Equities)",
        "market_custom": "🔍 手动输入代码 (Custom Ticker)",
        "choose_stock": "从列表中快速挑选股票：",
        "custom_label": "输入股票代码：",
        "custom_help": "马股请加 .KL (如: 1155.KL)；美股直接输入代码 (如: AAPL, NVDA)",
        "custom_placeholder": "例如: 1155.KL 或 AAPL",
        "quick_tag": "🔥 热门快捷测评：",
        
        # 核心参数
        "param_header": "⚙️ 步骤 2：估值核心参数设定 (可保持默认)",
        "param_terminal_g": "长期永续通胀增长率 (Terminal Growth Rate)",
        "param_terminal_g_help": "指公司成熟稳定后，永久跟随国家经济与通胀的微小增长率。小白保持 2.5% 即可！",
        "param_erp": "股市风险溢价要求 (Equity Risk Premium)",
        "param_erp_help": "投资股票相比于国债所期望的额外回报补偿。通常为 5.5%。",
        
        # 结果与三合一面板
        "result_header": "📊 步骤 3：三大估值模型横向对比与综合结论",
        "curr_price": "当前市场价格",
        "fair_price_rec": "⭐ 系统最推荐公道价",
        "verdict_title": "综合投资诊断",
        "verdict_under": "🟢 明显低估 (划算/打折中)",
        "verdict_over": "🔴 明显高估 (偏贵/溢价中)",
        "verdict_fair": "⚖️ 估值合理 (公道)",
        "upside_prefix": "较当前市价有",
        "downside_prefix": "较公道价溢价",
        
        # 三大模型卡片
        "model_dcf_name": "两阶段现金流贴现 (DCF)",
        "model_ddm_name": "股息分红贴现 (DDM)",
        "model_pe_name": "市盈率倍数估值 (P/E)",
        "badge_recommended": "⭐ 主要推荐",
        "badge_reference": "📌 参考估值",
        "no_data": "暂无有效数据",
        "no_data_dcf": "现金流为负或数据不足",
        "no_data_ddm": "该公司不派发股息",
        "no_data_pe": "公司目前处于净亏损",
        
        # 小白速成词典
        "glossary_header": "📖 小白通俗金融词典：这些数据代表什么？",
        "card_beta_title": "🎯 波动敏感度 (Beta)",
        "card_beta_desc": "衡量这只股票相对于大盘是更活泼还是更稳健。\n- Beta > 1：涨跌比大盘更猛（高弹性）\n- Beta < 1：走势比大盘更抗跌防守",
        "card_growth_title": "🚀 预期增长率 (Growth)",
        "card_growth_desc": "未来 5 年公司经营现金流预计每年递增的比例。增长越快，股票当前公道身价就越高。",
        "card_wacc_title": "🛡️ 投资及格线回报率 (WACC / 折现率)",
        "card_wacc_desc": "你买入这家公司所要求的最低年化回报门槛。风险越高、借钱越多的公司，及格线要求越高。",
        "card_fair_title": "💎 内在公允价值 (Fair Value)",
        "card_fair_desc": "剥离市场的短期情绪狂热与恐慌，根据公司真实资产、欠债与赚钱能力算出的'出厂公道价'。",

        # 动态图表
        "chart_header": "📈 步骤 4：多周期走势图与量化特征图",
        "timeframe_label": "切换股价走势周期：",
        "chart_history_title": "股票价格动态走势图",
        "chart_beta_title": "Beta 收益率特征线散点分布图",
        "chart_beta_exp": "每个点代表过往某一周的收益率联动。红线斜率即为真实 Beta（马股对标 MSCI Malaysia ETF，美股对标 S&P 500）。",
        
        # 华尔街一致预期
        "ws_header": "🏛️ 华尔街专业投行分析师共识 (Wall Street View)",
        "ws_mean": "投行平均目标价",
        "ws_range": "目标价最高/最低区间",
        "ws_rating": "投行综合评级",
        "ws_match": "✅ 你的模型计算与华尔街机构分析师共识高度吻合！",
        
        # 免责声明
        "disclaimer_title": "⚠️ 重要法律与风险免责声明",
        "disclaimer_content": (
            "1. **非投资建议**：本网站所呈现的所有估值结果、公道价格、诊断与图表分析，仅供学术研究、个人学习交流与教学参考，不构成任何投资建议、买卖要约或财务建议。\n"
            "2. **市场风险**：股票市场波动剧烈，历史数据和数学量化模型无法预知未来。公司的实际表现可能受到宏观经济、行业竞争及突发事件的影响。\n"
            "3. **自主决策**：任何投资决策均应由投资者在独立调查或咨询持牌财务顾问的基础上自行做出。开发者与本网站不对依据本系统数据交易所产生的任何盈亏承担连带法律责任。"
        )
    },
    "en": {
        "title": "💡 StockVal - Smart Fair Value Estimator",
        "subtitle": "Beginner-Friendly Multi-Model Valuation Platform | Supports Bursa Malaysia & US Equities",
        "lang_select": "Language / 语言",
        "market_label": "📌 Step 1: Select Market or Input Ticker",
        "market_my": "🇲🇾 Bursa Malaysia",
        "market_us": "🇺🇸 US Equities",
        "market_custom": "🔍 Custom Ticker",
        "choose_stock": "Quick pick a popular stock from the list:",
        "custom_label": "Enter Stock Ticker Symbol:",
        "custom_help": "For Malaysian stocks add .KL (e.g., 1155.KL); for US stocks enter ticker (e.g., AAPL, NVDA)",
        "custom_placeholder": "e.g., 1155.KL or AAPL",
        "quick_tag": "🔥 Quick Suggestions:",
        
        # Parameters
        "param_header": "⚙️ Step 2: Core Valuation Assumptions (Defaults Recommended)",
        "param_terminal_g": "Perpetual / Terminal Growth Rate (g)",
        "param_terminal_g_help": "The long-term perpetual growth rate once the company matures, roughly matching GDP & inflation. 2.5% is standard.",
        "param_erp": "Equity Risk Premium (ERP)",
        "param_erp_help": "The extra return expected for taking stock risk above safe government bond yields. Typically 5.5%.",
        
        # Results & 3-Model Panel
        "result_header": "📊 Step 3: Multi-Model Valuation Matrix & Final Verdict",
        "curr_price": "Current Market Price",
        "fair_price_rec": "⭐ System Recommended Fair Value",
        "verdict_title": "Diagnostic Summary",
        "verdict_under": "🟢 UNDERVALUED (On Sale)",
        "verdict_over": "🔴 OVERVALUED (Expensive)",
        "verdict_fair": "⚖️ FAIRLY VALUED",
        "upside_prefix": "Potential upside from market price: ",
        "downside_prefix": "Trading at a premium of: ",
        
        # 3 Models
        "model_dcf_name": "Two-Stage DCF Model",
        "model_ddm_name": "Dividend Discount Model (DDM)",
        "model_pe_name": "P/E Multiples Valuation",
        "badge_recommended": "⭐ Recommended",
        "badge_reference": "📌 Reference",
        "no_data": "No Valid Data",
        "no_data_dcf": "Negative or Missing Cash Flows",
        "no_data_ddm": "Company pays no dividend",
        "no_data_pe": "Company in net loss",
        
        # Glossary
        "glossary_header": "📖 Beginner's Financial Glossary: What do these numbers mean?",
        "card_beta_title": "🎯 Volatility Sensitivity (Beta)",
        "card_beta_desc": "Measures how violently this stock swings compared to the market index.\n- Beta > 1: Amplified swings (high volatility)\n- Beta < 1: More defensive and stable than the market",
        "card_growth_title": "🚀 Expected Growth Rate",
        "card_growth_desc": "Forecasted annual growth rate in cash generation over the next 5 years. Higher growth justifies a higher fair price.",
        "card_wacc_title": "🛡️ Hurdle Discount Rate (WACC)",
        "card_wacc_desc": "The minimum annual hurdle return required by investors. Higher-risk or highly-leveraged companies demand a higher hurdle.",
        "card_fair_title": "💎 Intrinsic Fair Value",
        "card_fair_desc": "Stripping away short-term market hype and panic, this represents the company's authentic 'factory price' per share.",

        # Dynamic Charts
        "chart_header": "📈 Step 4: Multi-Timeframe Price Trend & Regression Analysis",
        "timeframe_label": "Select Price Timeframe:",
        "chart_history_title": "Interactive Stock Price Trend",
        "chart_beta_title": "Beta Characteristic Line & Scatter Plot",
        "chart_beta_exp": "Each point represents one week of historical returns. The slope of the red line is Beta (vs MSCI Malaysia ETF for Bursa, vs S&P 500 for US).",
        
        # Wall Street
        "ws_header": "🏛️ Wall Street Analyst Consensus (US Equities)",
        "ws_mean": "Analyst Consensus Target Price",
        "ws_range": "Analyst High / Low Range",
        "ws_rating": "Overall Consensus Rating",
        "ws_match": "✅ Your DCF valuation closely aligns with Wall Street institutional price targets!",
        
        # Disclaimer
        "disclaimer_title": "⚠️ Important Legal & Risk Disclaimer",
        "disclaimer_content": (
            "1. **Educational Purposes Only**: All valuation models, fair prices, estimates, and graphical analyses provided on this website are for academic research, learning, and reference purposes only. They do NOT constitute investment, financial, or trading advice.\n"
            "2. **Market Risk**: Equity investments involve substantial capital risk. Historical data and mathematical formulas cannot guarantee future market returns. Actual business performance may deviate significantly due to macroeconomic or industry shifts.\n"
            "3. **Independent Decision**: Investors must exercise their own independent judgement or consult a licensed financial advisor before executing any transactions. The developers and this platform assume no liability for any trading losses incurred."
        )
    }
}

# ==============================================================================
# 3. 页面顶栏：标题与中英文切换
# ==============================================================================
col_title, col_lang = st.columns([4, 1.2])
with col_lang:
    selected_lang = st.selectbox("🌐 Language / 语言", options=["中文", "English"], index=0)
    lang_key = "zh" if selected_lang == "中文" else "en"
    T = TEXTS[lang_key]

with col_title:
    st.title(T["title"])
    st.caption(T["subtitle"])

st.markdown("---")

# ==============================================================================
# 4. 股票选择器与搜索 (单选切换，彻底杜绝 Tab 状态混乱导致美股无法读取的 Bug)
# ==============================================================================
st.subheader(T["market_label"])

MY_STOCKS = [
    ("1155.KL", "Maybank (马来亚银行 - 金融分红王)"),
    ("1295.KL", "Public Bank (大众银行 - 稳健金融巨头)"),
    ("5347.KL", "Tenaga Nasional (国家能源 - 公用事业基建)"),
    ("0166.KL", "Inari Amertron (益纳利 - 科技半导体芯片)"),
    ("5211.KL", "Sunway (双威集团 - 综合地产医疗)"),
    ("7113.KL", "Top Glove (顶级手套 - 医疗制造)"),
    ("5296.KL", "MR D.I.Y. (大型家装零售连锁)"),
    ("5183.KL", "PetChem (国油石化 - 能源化工龙头)")
]

US_STOCKS = [
    ("AAPL", "Apple Inc. (苹果公司 - 消费电子与生态)"),
    ("NVDA", "NVIDIA Corporation (英伟达 - 全球 AI 算力芯片)"),
    ("TSLA", "Tesla Inc. (特斯拉 - 电动车与机器人)"),
    ("MSFT", "Microsoft (微软 - 企业软件与云计算)"),
    ("GOOGL", "Alphabet Inc. (谷歌 - 全球搜索与云原生)"),
    ("AMZN", "Amazon.com (亚马逊 - 全球电商与 AWS)"),
    ("META", "Meta Platforms (Meta - 社交网络与大模型)"),
    ("JPM", "JPMorgan Chase (摩根大通 - 华尔街银行巨头)")
]

if "current_ticker" not in st.session_state:
    st.session_state["current_ticker"] = "1155.KL"

market_choice = st.radio(
    "市场类别：",
    options=[T["market_my"], T["market_us"], T["market_custom"]],
    horizontal=True,
    label_visibility="collapsed"
)

if market_choice == T["market_my"]:
    my_opts = [f"{t} | {name}" for t, name in MY_STOCKS]
    default_idx = 0
    for idx, (t, _) in enumerate(MY_STOCKS):
        if t == st.session_state["current_ticker"]:
            default_idx = idx
            break
    sel_my = st.selectbox(T["choose_stock"], options=my_opts, index=default_idx)
    st.session_state["current_ticker"] = sel_my.split(" | ")[0].strip()

elif market_choice == T["market_us"]:
    us_opts = [f"{t} | {name}" for t, name in US_STOCKS]
    default_idx = 0
    for idx, (t, _) in enumerate(US_STOCKS):
        if t == st.session_state["current_ticker"]:
            default_idx = idx
            break
    sel_us = st.selectbox(T["choose_stock"], options=us_opts, index=default_idx)
    st.session_state["current_ticker"] = sel_us.split(" | ")[0].strip()

else:
    custom_val = st.text_input(
        T["custom_label"],
        value=st.session_state["current_ticker"] if st.session_state["current_ticker"] not in [t for t, _ in MY_STOCKS + US_STOCKS] else "",
        placeholder=T["custom_placeholder"],
        help=T["custom_help"]
    ).strip().upper()
    if custom_val:
        st.session_state["current_ticker"] = custom_val

# 快捷一键切换按钮排
st.write(T["quick_tag"])
q_cols = st.columns(6)
if q_cols[0].button("1155.KL (Maybank)", use_container_width=True):
    st.session_state["current_ticker"] = "1155.KL"
    st.rerun()
if q_cols[1].button("0166.KL (Inari 科技)", use_container_width=True):
    st.session_state["current_ticker"] = "0166.KL"
    st.rerun()
if q_cols[2].button("5347.KL (Tenaga 能源)", use_container_width=True):
    st.session_state["current_ticker"] = "5347.KL"
    st.rerun()
if q_cols[3].button("AAPL (苹果)", use_container_width=True):
    st.session_state["current_ticker"] = "AAPL"
    st.rerun()
if q_cols[4].button("NVDA (英伟达)", use_container_width=True):
    st.session_state["current_ticker"] = "NVDA"
    st.rerun()
if q_cols[5].button("TSLA (特斯拉)", use_container_width=True):
    st.session_state["current_ticker"] = "TSLA"
    st.rerun()

current_ticker = st.session_state["current_ticker"]

st.markdown("---")

# ==============================================================================
# 5. 核心参数调节
# ==============================================================================
with st.expander(f"{T['param_header']} 👈 (小白用户建议直接保持默认，无需改动)", expanded=False):
    param_col1, param_col2 = st.columns(2)
    with param_col1:
        custom_terminal_g = st.slider(
            T["param_terminal_g"],
            min_value=1.0,
            max_value=3.5,
            value=2.5,
            step=0.1,
            help=T["param_terminal_g_help"]
        ) / 100.0
    with param_col2:
        custom_erp = st.slider(
            T["param_erp"],
            min_value=4.0,
            max_value=7.0,
            value=5.5,
            step=0.1,
            help=T["param_erp_help"]
        ) / 100.0

# ==============================================================================
# 6. 后台轻量金融量化引擎 (极度健壮，杜绝任何 KeyError: 0)
# ==============================================================================

def safe_extract_item(df, item_name, default=0.0):
    """
    安全提取财务报表中指标最新一期数据（完全杜绝 Pandas KeyError: 0）
    """
    if df is None or df.empty:
        return default
    try:
        for idx in df.index:
            if str(idx).strip().lower() == str(item_name).strip().lower():
                row = df.loc[idx]
                if hasattr(row, 'iloc') and len(row) > 0:
                    val = row.iloc[0]
                elif hasattr(row, '__iter__') and len(row) > 0:
                    val = list(row)[0]
                else:
                    val = row
                if pd.notna(val):
                    return float(val)
    except Exception:
        pass
    return default

def fetch_risk_free_rate(is_my):
    if is_my:
        return 0.0385, "BNM 官方动态基准 (MGS 10Y: ~3.85%)"
    try:
        tnx = yf.Ticker("^TNX").history(period="5d")
        if not tnx.empty and 'Close' in tnx:
            valid_closes = tnx['Close'].dropna()
            if len(valid_closes) > 0:
                rf = float(valid_closes.iloc[-1]) / 100.0
                return rf, f"US Treasury 10Y (^TNX: {rf*100:.2f}%)"
        return 0.042, "US Treasury 10Y Benchmark (4.20%)"
    except Exception:
        return 0.042, "US Treasury 10Y Benchmark (4.20%)"

def run_dynamic_beta_regression(ticker, is_my):
    benchmark_symbol = "EWM" if is_my else "SPY"
    benchmark_label = "iShares MSCI Malaysia ETF (EWM)" if is_my else "S&P 500 ETF (SPY)"
    try:
        df = yf.download(
            [ticker, benchmark_symbol],
            period="3y",
            interval="1wk",
            auto_adjust=True,
            progress=False
        )
        if df.empty:
            return 1.0, None, 0.0

        if 'Close' in df:
            df_close = df['Close']
        else:
            df_close = df

        if isinstance(df_close.columns, pd.MultiIndex):
            df_close.columns = df_close.columns.get_level_values(0)

        df_close.columns = [str(c).strip().upper() for c in df_close.columns]
        target_t = ticker.strip().upper()
        target_b = benchmark_symbol.strip().upper()

        if target_t not in df_close.columns or target_b not in df_close.columns:
            return 1.0, None, 0.0

        returns = df_close[[target_t, target_b]].pct_change().dropna()
        if len(returns) < 20:
            return 1.0, None, 0.0

        y = returns[target_t].values * 100.0
        x = returns[target_b].values * 100.0
        beta, alpha = np.polyfit(x, y, 1)
        corr = np.corrcoef(x, y)[0, 1]
        r2 = float(corr ** 2) if pd.notna(corr) else 0.0

        # 绘制散点图
        fig, ax = plt.subplots(figsize=(5.5, 3.8), dpi=110)
        ax.scatter(x, y, alpha=0.5, color="#2980b9", edgecolors="none", s=25, label="Weekly Returns (3Y)")
        x_line = np.linspace(x.min(), x.max(), 100)
        ax.plot(x_line, beta * x_line + alpha, color="#e74c3c", linewidth=2, label=f"Fit Line (Beta = {beta:.2f})")
        ax.axhline(0, color="gray", linestyle="--", linewidth=0.6, alpha=0.5)
        ax.axvline(0, color="gray", linestyle="--", linewidth=0.6, alpha=0.5)
        ax.set_xlabel(f"Benchmark: {benchmark_label} (%)", fontsize=9)
        ax.set_ylabel(f"Stock: {ticker} (%)", fontsize=9)
        ax.set_title(f"Beta Regression (Beta = {beta:.2f} | R² = {r2:.2f})", fontsize=10, fontweight="bold")
        ax.grid(True, linestyle=":", alpha=0.4)
        ax.legend(loc="upper left", fontsize=8)
        plt.tight_layout()

        safe_beta = float(min(max(beta, 0.40), 2.20))
        return safe_beta, fig, r2
    except Exception:
        return 1.0, None, 0.0

# ==============================================================================
# 7. 核心执行与结果呈现
# ==============================================================================
if current_ticker:
    is_my = current_ticker.endswith(".KL")

    with st.spinner(f"正在全维度测算 {current_ticker} 的真实公道价值..." if lang_key == "zh" else f"Calculating fair intrinsic valuation for {current_ticker}..."):
        try:
            stock = yf.Ticker(current_ticker)
            info = stock.info or {}

            company_name = info.get('longName') or info.get('shortName') or current_ticker
            sector = info.get('sector', 'Unknown')
            industry = info.get('industry', 'Unknown')
            currency = info.get('currency', 'MYR' if is_my else 'USD')

            # 稳健价格提取
            price = (
                info.get('currentPrice') 
                or info.get('regularMarketPrice') 
                or info.get('previousClose') 
                or 0.0
            )
            if price == 0.0:
                try:
                    h_2d = stock.history(period="5d")
                    if not h_2d.empty and 'Close' in h_2d:
                        valid_closes = h_2d['Close'].dropna()
                        if len(valid_closes) > 0:
                            price = float(valid_closes.iloc[-1])
                except Exception:
                    pass

            shares = info.get('sharesOutstanding', 1) or 1

            # 1. 无风险利率与动态 Beta
            rf, rf_label = fetch_risk_free_rate(is_my)
            beta, beta_fig, beta_r2 = run_dynamic_beta_regression(current_ticker, is_my)
            ke = rf + (beta * custom_erp)

            # 2. 安全读取报表数据
            bs = stock.balance_sheet
            fin = stock.financials
            cfs = stock.cashflow

            total_debt = safe_extract_item(bs, 'Total Debt', 0.0)
            if total_debt == 0.0:
                total_debt = float(info.get('totalDebt', 0.0) or 0.0)

            cash = safe_extract_item(bs, 'Cash And Cash Equivalents', 0.0)
            if cash == 0.0:
                cash = safe_extract_item(bs, 'Cash Cash Equivalents And Short Term Investments', 0.0)
            if cash == 0.0:
                cash = float(info.get('totalCash', 0.0) or 0.0)

            interest_exp = abs(safe_extract_item(fin, 'Interest Expense', 0.0))
            tax = safe_extract_item(fin, 'Tax Provision', 0.0)
            pretax = safe_extract_item(fin, 'Pretax Income', 0.0)

            tax_rate = 0.24 if is_my else 0.21
            if pretax > 0 and tax > 0:
                tax_rate = min(max(tax / pretax, 0.10), 0.35)

            kd = (interest_exp / total_debt) if total_debt > 0 else 0.0
            market_cap = price * shares
            total_capital = market_cap + total_debt
            wacc = (market_cap / total_capital * ke) + (total_debt / total_capital * kd * (1.0 - tax_rate)) if total_capital > 0 else ke
            wacc = max(wacc, custom_terminal_g + 0.02)

            # ------------------------------------------------------------------
            # 模型一：两阶段现金流贴现模型 (Two-Stage DCF)
            # ------------------------------------------------------------------
            val_dcf = None
            fcf = float(info.get('freeCashflow', 0.0) or 0.0)
            if fcf <= 0.0:
                fcf = safe_extract_item(cfs, 'Free Cash Flow', 0.0)
            if fcf <= 0.0:
                ocf = safe_extract_item(cfs, 'Operating Cash Flow', 0.0)
                capex = abs(safe_extract_item(cfs, 'Capital Expenditure', 0.0))
                if ocf > capex:
                    fcf = ocf - capex

            growth_dcf = 0.05
            if fcf > 0.0:
                if is_my:
                    try:
                        if cfs is not None and not cfs.empty:
                            for idx in cfs.index:
                                if 'free cash flow' in str(idx).lower():
                                    row = cfs.loc[idx]
                                    if hasattr(row, 'iloc') and len(row) >= 3:
                                        f_now = float(row.iloc[0])
                                        f_past = float(row.iloc[2])
                                        if f_now > 0 and f_past > 0:
                                            growth_dcf = (f_now / f_past) ** 0.5 - 1.0
                                        break
                    except Exception:
                        pass
                    growth_dcf = min(max(growth_dcf, 0.02), 0.15)
                else:
                    g_raw = info.get('earningsGrowth') or info.get('revenueGrowth') or 0.08
                    try:
                        growth_dcf = min(max(float(g_raw), 0.03), 0.20)
                    except Exception:
                        growth_dcf = 0.08

                pv_stage1 = sum([ (fcf * ((1.0 + growth_dcf) ** yr)) / ((1.0 + wacc) ** yr) for yr in range(1, 6) ])
                fcf_yr5 = fcf * ((1.0 + growth_dcf) ** 5)
                pv_tv = ((fcf_yr5 * (1.0 + custom_terminal_g)) / (wacc - custom_terminal_g)) / ((1.0 + wacc) ** 5)
                ev = pv_stage1 + pv_tv
                equity_val = ev - total_debt + cash
                val_dcf = equity_val / shares if shares > 0 else None

            # ------------------------------------------------------------------
            # 模型二：股息分红折现模型 (DDM)
            # ------------------------------------------------------------------
            val_ddm = None
            dps = float(info.get('dividendRate') or info.get('trailingAnnualDividendRate') or 0.0)
            if dps > 0.0:
                g_ddm = min(custom_terminal_g, ke - 0.01)
                val_ddm = (dps * (1.0 + g_ddm)) / (ke - g_ddm) if ke > g_ddm else 0.0

            # ------------------------------------------------------------------
            # 模型三：市盈率倍数估值法 (P/E Multiples)
            # ------------------------------------------------------------------
            val_pe = None
            eps = float(info.get('trailingEps') or info.get('forwardEps') or 0.0)
            if eps <= 0.0:
                net_inc = safe_extract_item(fin, 'Net Income', 0.0)
                if net_inc > 0 and shares > 0:
                    eps = net_inc / shares

            if eps > 0.0:
                if sector in ['Technology', 'Communication Services']:
                    bench_pe = 24.0
                elif sector in ['Financial Services']:
                    bench_pe = 11.5
                elif sector in ['Utilities', 'Real Estate']:
                    bench_pe = 14.0
                elif sector in ['Healthcare', 'Consumer Defensive']:
                    bench_pe = 18.0
                else:
                    bench_pe = 16.0
                val_pe = eps * bench_pe

            # ------------------------------------------------------------------
            # 确定系统最推荐模型 (Recommendation Decision)
            # ------------------------------------------------------------------
            if sector in ['Financial Services', 'Utilities', 'Real Estate'] and val_ddm is not None:
                primary_model_name = T["model_ddm_name"]
                primary_val = val_ddm
                rec_reason = "高杠杆/稳定分红商业模式，以持续派息能力为主" if lang_key == "zh" else "High-dividend/regulated financial structure"
            elif val_dcf is not None:
                primary_model_name = T["model_dcf_name"]
                primary_val = val_dcf
                rec_reason = "实体经营自主造血能力最客观真实" if lang_key == "zh" else "Most authentic reflection of operating cash generation"
            elif val_pe is not None:
                primary_model_name = T["model_pe_name"]
                primary_val = val_pe
                rec_reason = "现金流处于重投资期，采用市盈率盈利倍数衡量" if lang_key == "zh" else "Reinvestment phase, evaluated via P/E multiple"
            else:
                primary_model_name = "N/A"
                primary_val = None
                rec_reason = "暂无充足盈利数据" if lang_key == "zh" else "Insufficient earnings data"

            # ==================================================================
            # 结果呈现区 (步骤 3)
            # ==================================================================
            st.subheader(T["result_header"])
            st.markdown(f"#### 🏢 **{company_name}** (`{current_ticker}`) | `{sector}` | `{industry}` | `{currency}`")

            # 顶部最推荐结论大卡片
            top_col1, top_col2, top_col3 = st.columns([1, 1.2, 1.4])
            with top_col1:
                st.metric(label=T["curr_price"], value=f"{currency} {price:.2f}" if price > 0 else "N/A")

            with top_col2:
                if primary_val and primary_val > 0:
                    st.metric(
                        label=f"{T['fair_price_rec']} ({primary_model_name})", 
                        value=f"{currency} {primary_val:.2f}",
                        help=rec_reason
                    )
                else:
                    st.metric(label=T["fair_price_rec"], value=T["no_data"])

            with top_col3:
                if primary_val and primary_val > 0 and price > 0:
                    diff_pct = (primary_val - price) / price * 100.0
                    if primary_val > price:
                        st.success(f"### {T['verdict_under']}\n**{T['upside_prefix']} +{diff_pct:.1f}%**")
                    else:
                        st.error(f"### {T['verdict_over']}\n**{T['downside_prefix']} {abs(diff_pct):.1f}%**")
                else:
                    st.warning(T["no_data"])

            st.markdown("---")

            # 三大模型横向对比矩阵 (DCF + DDM + P/E)
            st.markdown("#### ⚖️ 三大经典估值模型横向横比 (Valuation Matrix)")
            m_col1, m_col2, m_col3 = st.columns(3)

            # 模型 1: DCF
            with m_col1:
                is_rec = (primary_model_name == T["model_dcf_name"])
                badge = f"`{T['badge_recommended']}`" if is_rec else f"`{T['badge_reference']}`"
                st.markdown(f"##### {T['model_dcf_name']} {badge}")
                if val_dcf and val_dcf > 0:
                    dcf_diff = (val_dcf - price) / price * 100.0 if price > 0 else 0
                    st.metric("公道估值", f"{currency} {val_dcf:.2f}", f"{dcf_diff:+.1f}% vs 市价")
                    st.caption("基于未来 5 年公司自由现金流与 WACC 折现。")
                else:
                    st.metric("公道估值", "N/A")
                    st.caption(f"⚠️ {T['no_data_dcf']}")

            # 模型 2: DDM
            with m_col2:
                is_rec = (primary_model_name == T["model_ddm_name"])
                badge = f"`{T['badge_recommended']}`" if is_rec else f"`{T['badge_reference']}`"
                st.markdown(f"##### {T['model_ddm_name']} {badge}")
                if val_ddm and val_ddm > 0:
                    ddm_diff = (val_ddm - price) / price * 100.0 if price > 0 else 0
                    st.metric("公道估值", f"{currency} {val_ddm:.2f}", f"{ddm_diff:+.1f}% vs 市价")
                    st.caption("基于历史股息分红及永续增长率折现。")
                else:
                    st.metric("公道估值", "N/A")
                    st.caption(f"⚠️ {T['no_data_ddm']}")

            # 模型 3: P/E
            with m_col3:
                is_rec = (primary_model_name == T["model_pe_name"])
                badge = f"`{T['badge_recommended']}`" if is_rec else f"`{T['badge_reference']}`"
                st.markdown(f"##### {T['model_pe_name']} {badge}")
                if val_pe and val_pe > 0:
                    pe_diff = (val_pe - price) / price * 100.0 if price > 0 else 0
                    st.metric("公道估值", f"{currency} {val_pe:.2f}", f"{pe_diff:+.1f}% vs 市价")
                    st.caption("基于每股净收益 (EPS) 乘以行业合理市盈率倍数。")
                else:
                    st.metric("公道估值", "N/A")
                    st.caption(f"⚠️ {T['no_data_pe']}")

            st.markdown("---")

            # ==================================================================
            # 小白通俗名词字典 (四个直观数据卡片)
            # ==================================================================
            st.subheader(T["glossary_header"])
            g_col1, g_col2, g_col3, g_col4 = st.columns(4)
            
            with g_col1:
                st.markdown(f"##### {T['card_beta_title']}")
                st.metric("Beta", f"{beta:.2f}")
                st.info(T["card_beta_desc"])

            with g_col2:
                st.markdown(f"##### {T['card_growth_title']}")
                st.metric(f"Growth (5Y)", f"{growth_dcf * 100:.1f}%")
                st.info(T["card_growth_desc"])

            with g_col3:
                st.markdown(f"##### {T['card_wacc_title']}")
                st.metric("Discount Rate", f"{wacc * 100:.1f}%")
                st.info(T["card_wacc_desc"])

            with g_col4:
                st.markdown(f"##### {T['card_fair_title']}")
                st.metric("Fair Value", f"{currency} {primary_val:.2f}" if primary_val else "N/A")
                st.info(T["card_fair_desc"])

            st.markdown("---")

            # ==================================================================
            # 视觉图表区域 (步骤 4：包含多周期动态走势图 1D, 1M, 1Y, 5Y, MAX)
            # ==================================================================
            st.subheader(T["chart_header"])
            ch_col1, ch_col2 = st.columns([1.3, 1])

            with ch_col1:
                st.markdown(f"##### 📈 {T['chart_history_title']}")
                
                timeframe = st.radio(
                    T["timeframe_label"],
                    options=["1D (1天)", "1M (1个月)", "1Y (1年)", "5Y (5年)", "MAX (全部)"],
                    index=3,
                    horizontal=True
                )
                
                tf_map = {
                    "1D (1天)": ("1d", "5m"),
                    "1M (1个月)": ("1mo", "1d"),
                    "1Y (1年)": ("1y", "1d"),
                    "5Y (5年)": ("5y", "1wk"),
                    "MAX (全部)": ("max", "1mo")
                }
                period_val, interval_val = tf_map[timeframe]

                try:
                    hist_data = yf.download(
                        current_ticker,
                        period=period_val,
                        interval=interval_val,
                        progress=False
                    )
                    if not hist_data.empty and 'Close' in hist_data:
                        st.line_chart(hist_data['Close'], use_container_width=True)
                    else:
                        st.write("暂无该周期的走势数据")
                except Exception:
                    st.write("获取该周期走势数据失败")

            with ch_col2:
                st.markdown(f"##### 🎯 {T['chart_beta_title']}")
                st.caption(T["chart_beta_exp"])
                if beta_fig is not None:
                    st.pyplot(beta_fig)
                else:
                    st.write("暂无散点图数据")

            # ==================================================================
            # 美股专属：华尔街一致预期
            # ==================================================================
            if not is_my:
                target_mean = info.get('targetMeanPrice')
                target_high = info.get('targetHighPrice')
                target_low = info.get('targetLowPrice')
                num_analysts = info.get('numberOfAnalystOpinions', 0)
                rating = str(info.get('recommendationKey', 'N/A')).upper()

                if target_mean and num_analysts > 0:
                    st.markdown("---")
                    st.subheader(T["ws_header"])
                    ws1, ws2, ws3 = st.columns(3)
                    ws1.metric(T["ws_mean"], f"${target_mean:.2f}", f"{num_analysts} Analysts")
                    ws2.metric(T["ws_range"], f"${target_low:.2f} ~ ${target_high:.2f}")
                    ws3.metric(T["ws_rating"], rating)

                    if primary_val and abs((primary_val - target_mean) / target_mean) <= 0.15:
                        st.success(T["ws_match"])

            # ==================================================================
            # 重要法律与风险免责声明 (醒目展示在底部)
            # ==================================================================
            st.markdown("---")
            st.warning(f"### {T['disclaimer_title']}\n\n{T['disclaimer_content']}")

        except Exception as e:
            st.error(f"测算遇到异常，请检查代码或重试。错误详情: {e}")
