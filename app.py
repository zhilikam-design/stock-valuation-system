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
        "subtitle": "小白也能看懂的股票内在价值测算工具 | 支持马来西亚股市 (Bursa) 与美股 (US Equities)",
        "lang_select": "语言 / Language",
        "search_header": "🔍 1. 选择或搜索股票",
        "preset_tab_my": "🇲🇾 马来西亚热门股票 (Bursa Malaysia)",
        "preset_tab_us": "🇺🇸 美国热门股票 (US Equities)",
        "preset_tab_custom": "✏️ 手动输入股票代码",
        "choose_stock": "从列表中快速挑选股票：",
        "custom_label": "输入股票代码 (Stock Ticker)：",
        "custom_help": "马股请在编号后加 .KL (例如: 1155.KL)；美股直接输入代码 (例如: AAPL)",
        "custom_placeholder": "例如: 1155.KL 或 AAPL",
        "btn_analyze": "开始智能估值",
        
        # 核心参数
        "param_header": "⚙️ 2. 估值核心参数设定 (可保持默认)",
        "param_terminal_g": "长期通胀/永续增长率 (Terminal Growth Rate)",
        "param_terminal_g_help": "指公司成熟稳定后，永久跟随国家经济与通胀的微小增长率。小白保持 2.5% 即可！",
        "param_erp": "股市投资风险溢价要求 (Equity Risk Premium)",
        "param_erp_help": "投资股票相比于把钱存国债，你所期望获得的额外回报率补偿。通常在 5.0% ~ 6.0% 之间。",
        
        # 结果与诊断
        "result_header": "📊 3. 股票公道价估值结论",
        "curr_price": "当前市场买卖价",
        "fair_price": "估算合理公道价",
        "verdict_title": "投资诊断参考",
        "verdict_under": "🟢 明显低估 (划算/打折中)",
        "verdict_over": "🔴 明显高估 (偏贵/溢价中)",
        "verdict_fair": "⚖️ 估值合理 (公道)",
        "upside_prefix": "相比当前市价有",
        "downside_prefix": "当前市价相比合理价高出",
        "model_used_dcf": "采用【两阶段现金流贴现模型 (DCF)】：依据公司真实经营赚取现金的能力来测算。",
        "model_used_ddm": "采用【股息分红折现模型 (DDM)】：金融/地产/公用事业专属，依据持续分红派息能力测算。",
        
        # 小白速成词典
        "glossary_header": "📖 小白通俗金融词典：这些数据代表什么？",
        "card_beta_title": "🎯 波动敏感度 (Beta)",
        "card_beta_desc": "衡量这只股票相对于大盘是更活泼还是更稳健。\n- Beta > 1：涨跌比大盘更猛（高弹性）\n- Beta < 1：走势比大盘更抗跌防守",
        "card_growth_title": "🚀 预期增长率 (Growth)",
        "card_growth_desc": "未来 5 年公司经营现金流预计每年递增的比例。增长越快，股票当前公道身价就越高。",
        "card_wacc_title": "🛡️ 投资及格线回报率 (WACC / 折现率)",
        "card_wacc_desc": "你买入这家公司所要求的最低年化回报门槛。风险越高、借钱越多的公司，及格线要求越高。",
        "card_fair_title": "💎 内在价值 (Intrinsic Value)",
        "card_fair_desc": "剥离市场的短期情绪狂热与恐慌，根据公司真实资产、欠债与赚钱能力算出的'出厂公道价'。",

        # 图表
        "chart_header": "📈 4. 数据可视化图表展示",
        "chart_beta_title": "Beta 收益率特征线散点分布图",
        "chart_beta_exp": "每个点代表过往某一周的收益率联动。红线斜率即为真实 Beta（马股对标 MSCI Malaysia ETF，美股对标 S&P 500）。",
        "chart_history_title": "过去 5 年历史股价走势图",
        
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
        "subtitle": "Beginner-Friendly Stock Valuation Platform | Supports Bursa Malaysia & US Equities",
        "lang_select": "Language / 语言",
        "search_header": "🔍 1. Select or Search Stock",
        "preset_tab_my": "🇲🇾 Popular Bursa Malaysia",
        "preset_tab_us": "🇺🇸 Popular US Equities",
        "preset_tab_custom": "✏️ Enter Custom Ticker",
        "choose_stock": "Quick pick a popular stock from the list:",
        "custom_label": "Enter Stock Ticker Symbol:",
        "custom_help": "For Malaysian stocks add .KL (e.g., 1155.KL); for US stocks enter ticker (e.g., AAPL)",
        "custom_placeholder": "e.g., 1155.KL or AAPL",
        "btn_analyze": "Calculate Valuation",
        
        # Parameters
        "param_header": "⚙️ 2. Core Valuation Assumptions (Defaults Recommended)",
        "param_terminal_g": "Perpetual / Terminal Growth Rate (g)",
        "param_terminal_g_help": "The long-term perpetual growth rate once the company matures, roughly matching GDP & inflation. 2.5% is standard.",
        "param_erp": "Equity Risk Premium (ERP)",
        "param_erp_help": "The extra return expected for taking stock risk above safe government bond yields. Typically 5.0% - 6.0%.",
        
        # Results
        "result_header": "📊 3. Fair Valuation Results & Verdict",
        "curr_price": "Current Market Price",
        "fair_price": "Estimated Fair Value",
        "verdict_title": "Investment Diagnostic",
        "verdict_under": "🟢 UNDERVALUED (On Sale)",
        "verdict_over": "🔴 OVERVALUED (Expensive)",
        "verdict_fair": "⚖️ FAIRLY VALUED",
        "upside_prefix": "Potential upside from current market price: ",
        "downside_prefix": "Trading at a premium of: ",
        "model_used_dcf": "Evaluated using Two-Stage Discounted Cash Flow (DCF): based on real operating cash generating power.",
        "model_used_ddm": "Evaluated using Dividend Discount Model (DDM): customized for Financials/Utilities based on sustainable dividend yields.",
        
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

        # Charts
        "chart_header": "📈 4. Visual Data & Charts",
        "chart_beta_title": "Beta Characteristic Line & Scatter Plot",
        "chart_beta_exp": "Each point represents one week of historical returns. The slope of the red line is Beta (vs MSCI Malaysia ETF for Bursa, vs S&P 500 for US).",
        "chart_history_title": "Past 5-Year Historical Stock Price",
        
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
# 4. 股票选择器与搜索框 (在主页一目了然，附带马股与美股热门列表)
# ==============================================================================
st.subheader(T["search_header"])

MY_STOCKS = [
    ("1155.KL", "Maybank (马来亚银行 - 金融龙头 / Dividend King)"),
    ("1295.KL", "Public Bank (大众银行 - 稳健金融巨头)"),
    ("5347.KL", "Tenaga Nasional (国家能源 - 公用事业基建)"),
    ("0166.KL", "Inari Amertron (益纳利 - 科技半导体芯片)"),
    ("5211.KL", "Sunway (双威集团 - 综合地产医疗)"),
    ("7113.KL", "Top Glove (顶级手套 - 医疗制造)"),
    ("5296.KL", "MR D.I.Y. (大型家装零售连锁)"),
    ("5183.KL", "PetChem (国油石化 - 能源化工龙头)")
]

US_STOCKS = [
    ("AAPL", "Apple (苹果公司 - 消费电子巨头)"),
    ("NVDA", "NVIDIA (英伟达 - 全球 AI 算力龙头)"),
    ("TSLA", "Tesla (特斯拉 - 电动车与人形机器人)"),
    ("MSFT", "Microsoft (微软 - 云计算与企业软件)"),
    ("GOOGL", "Alphabet (谷歌 - 全球搜索与 AI)"),
    ("AMZN", "Amazon (亚马逊 - 电商与 AWS 云原生)")
]

search_tab_my, search_tab_us, search_tab_custom = st.tabs([
    T["preset_tab_my"],
    T["preset_tab_us"],
    T["preset_tab_custom"]
])

chosen_ticker = "1155.KL"

with search_tab_my:
    st.write(T["choose_stock"])
    my_options = [f"{t} | {name}" for t, name in MY_STOCKS]
    selected_my = st.selectbox("选择马股：", options=my_options, index=0, label_visibility="collapsed")
    chosen_my_ticker = selected_my.split(" | ")[0].strip()

with search_tab_us:
    st.write(T["choose_stock"])
    us_options = [f"{t} | {name}" for t, name in US_STOCKS]
    selected_us = st.selectbox("选择美股：", options=us_options, index=0, label_visibility="collapsed")
    chosen_us_ticker = selected_us.split(" | ")[0].strip()

with search_tab_custom:
    custom_in = st.text_input(
        T["custom_label"],
        value="",
        placeholder=T["custom_placeholder"],
        help=T["custom_help"]
    ).strip().upper()

# 决定当前激活的 Ticker
active_tab_hint = "MY"
if custom_in:
    current_ticker = custom_in
else:
    # 依据用户最后交互的标签默认
    # 使用会话状态或直接默认
    current_ticker = chosen_my_ticker

# 快捷一键切换按钮排
st.write("🔥 **热门一键快速测评**：" if lang_key == "zh" else "🔥 **Quick Switch Suggestions**:")
q_cols = st.columns(6)
if q_cols[0].button("1155.KL (Maybank)", use_container_width=True):
    current_ticker = "1155.KL"
if q_cols[1].button("0166.KL (Inari 科技)", use_container_width=True):
    current_ticker = "0166.KL"
if q_cols[2].button("5347.KL (Tenaga 能源)", use_container_width=True):
    current_ticker = "5347.KL"
if q_cols[3].button("AAPL (苹果)", use_container_width=True):
    current_ticker = "AAPL"
if q_cols[4].button("NVDA (英伟达)", use_container_width=True):
    current_ticker = "NVDA"
if q_cols[5].button("TSLA (特斯拉)", use_container_width=True):
    current_ticker = "TSLA"

st.markdown("---")

# ==============================================================================
# 5. 核心参数调节 (直接展示在主界面，附带小白提示)
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
# 6. 后台轻量金融量化引擎
# ==============================================================================

def fetch_risk_free_rate(is_my):
    if is_my:
        return 0.0385, "BNM 官方动态基准 (MGS 10Y: ~3.85%)"
    try:
        tnx = yf.Ticker("^TNX").history(period="1d")
        if len(tnx) > 0 and 'Close' in tnx:
            rf = float(tnx['Close'].iloc[-1]) / 100.0
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
        )['Close']
        returns = df.pct_change().dropna()
        if len(returns) < 20:
            return 1.0, None, 0.0

        y = returns[ticker].values * 100.0
        x = returns[benchmark_symbol].values * 100.0
        beta, alpha = np.polyfit(x, y, 1)
        corr = np.corrcoef(x, y)[0, 1]
        r2 = float(corr ** 2)

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
# 7. 渲染执行与结果展示
# ==============================================================================
if current_ticker:
    is_my = current_ticker.endswith(".KL")

    with st.spinner(f"正在智能测算 {current_ticker} 的真实公道价值..." if lang_key == "zh" else f"Calculating fair intrinsic value for {current_ticker}..."):
        try:
            stock = yf.Ticker(current_ticker)
            info = stock.info

            company_name = info.get('longName', current_ticker)
            sector = info.get('sector', 'Unknown')
            industry = info.get('industry', 'Unknown')
            currency = info.get('currency', 'MYR' if is_my else 'USD')
            price = info.get('currentPrice') or info.get('previousClose', 0.0)
            shares = info.get('sharesOutstanding', 1) or 1

            # 1. 无风险利率
            rf, rf_label = fetch_risk_free_rate(is_my)

            # 2. 动态 Beta 散点拟合
            beta, beta_fig, beta_r2 = run_dynamic_beta_regression(current_ticker, is_my)

            # 3. 股权成本 (CAPM Ke)
            ke = rf + (beta * custom_erp)

            # 4. 判断估值模型
            use_ddm = sector in ['Financial Services', 'Utilities', 'Real Estate']

            intrinsic_val = None
            growth_est = 0.05
            wacc = ke

            # DCF 路径
            if not use_ddm:
                bs = stock.balance_sheet
                fin = stock.financials
                cf_sheet = stock.cashflow

                total_debt = 0.0
                cash = 0.0
                if bs is not None and not bs.empty:
                    total_debt = float(bs.loc['Total Debt'][0]) if 'Total Debt' in bs.index else 0.0
                    cash = float(bs.loc['Cash And Cash Equivalents'][0]) if 'Cash And Cash Equivalents' in bs.index else 0.0

                interest_exp = 0.0
                tax_rate = 0.24 if is_my else 0.21
                if fin is not None and not fin.empty:
                    interest_exp = float(abs(fin.loc['Interest Expense'][0])) if 'Interest Expense' in fin.index else 0.0
                    tax = float(fin.loc['Tax Provision'][0]) if 'Tax Provision' in fin.index else 0.0
                    pretax = float(fin.loc['Pretax Income'][0]) if 'Pretax Income' in fin.index else 0.0
                    if pretax > 0 and tax > 0:
                        tax_rate = min(max(tax / pretax, 0.10), 0.35)

                kd = (interest_exp / total_debt) if total_debt > 0 else 0.0
                market_cap = price * shares
                total_capital = market_cap + total_debt
                wacc = (market_cap / total_capital * ke) + (total_debt / total_capital * kd * (1.0 - tax_rate)) if total_capital > 0 else ke
                wacc = max(wacc, custom_terminal_g + 0.02)

                fcf = info.get('freeCashflow', 0.0) or 0.0

                if fcf > 0.0:
                    if is_my:
                        try:
                            if cf_sheet is not None and 'Free Cash Flow' in cf_sheet.index and len(cf_sheet.columns) >= 3:
                                fcf_now = float(cf_sheet.loc['Free Cash Flow'][0])
                                fcf_past = float(cf_sheet.loc['Free Cash Flow'][2])
                                if fcf_now > 0 and fcf_past > 0:
                                    growth_est = (fcf_now / fcf_past) ** (1.0 / 2.0) - 1.0
                        except Exception:
                            pass
                        growth_est = min(max(growth_est, 0.02), 0.15)
                    else:
                        growth_raw = info.get('earningsGrowth') or info.get('revenueGrowth') or 0.08
                        growth_est = min(max(float(growth_raw), 0.03), 0.20)

                    pv_stage1 = sum([ (fcf * ((1.0 + growth_est) ** yr)) / ((1.0 + wacc) ** yr) for yr in range(1, 6) ])
                    fcf_yr5 = fcf * ((1.0 + growth_est) ** 5)
                    pv_tv = ((fcf_yr5 * (1.0 + custom_terminal_g)) / (wacc - custom_terminal_g)) / ((1.0 + wacc) ** 5)
                    ev = pv_stage1 + pv_tv
                    equity_val = ev - total_debt + cash
                    intrinsic_val = equity_val / shares

            # DDM 路径
            else:
                dps = info.get('dividendRate') or info.get('trailingAnnualDividendRate') or 0.0
                if dps > 0.0:
                    g_ddm = min(custom_terminal_g, ke - 0.01)
                    intrinsic_val = (dps * (1.0 + g_ddm)) / (ke - g_ddm) if ke > g_ddm else 0.0
                    growth_est = g_ddm

            # ==================================================================
            # 结果呈现区 (醒目大卡片，通俗易懂)
            # ==================================================================
            st.subheader(T["result_header"])
            st.markdown(f"#### 🏢 **{company_name}** (`{current_ticker}`) | {sector} | {industry}")

            res_card1, res_card2, res_card3 = st.columns([1, 1, 1.4])
            
            with res_card1:
                st.metric(label=T["curr_price"], value=f"{currency} {price:.2f}")

            with res_card2:
                if intrinsic_val and intrinsic_val > 0:
                    st.metric(label=T["fair_price"], value=f"{currency} {intrinsic_val:.2f}")
                else:
                    st.metric(label=T["fair_price"], value="N/A (现金流为负)")

            with res_card3:
                if intrinsic_val and intrinsic_val > 0 and price > 0:
                    diff_pct = (intrinsic_val - price) / price * 100.0
                    if intrinsic_val > price:
                        st.success(f"### {T['verdict_under']}\n**{T['upside_prefix']} +{diff_pct:.1f}%**")
                    else:
                        st.error(f"### {T['verdict_over']}\n**{T['downside_prefix']} {abs(diff_pct):.1f}%**")
                else:
                    st.warning("⚠️ 该公司自由现金流为负数或无分红，无法通过传统量化折现计算公允价格。")

            st.caption(f"ℹ️ {T['model_used_ddm'] if use_ddm else T['model_used_dcf']}")

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
                st.metric(f"Growth (5Y)", f"{growth_est * 100:.1f}%")
                st.info(T["card_growth_desc"])

            with g_col3:
                st.markdown(f"##### {T['card_wacc_title']}")
                st.metric("Discount Rate", f"{wacc * 100:.1f}%")
                st.info(T["card_wacc_desc"])

            with g_col4:
                st.markdown(f"##### {T['card_fair_title']}")
                st.metric("Fair Value", f"{currency} {intrinsic_val:.2f}" if intrinsic_val else "N/A")
                st.info(T["card_fair_desc"])

            st.markdown("---")

            # ==================================================================
            # 视觉图表区域 (直接并在主页面上，左边 Beta 散点图，右边 5 年股价走势)
            # ==================================================================
            st.subheader(T["chart_header"])
            ch_col1, ch_col2 = st.columns([1, 1.2])

            with ch_col1:
                st.markdown(f"##### 🎯 {T['chart_beta_title']}")
                st.caption(T["chart_beta_exp"])
                if beta_fig is not None:
                    st.pyplot(beta_fig)
                else:
                    st.write("暂无散点图数据")

            with ch_col2:
                st.markdown(f"##### 📈 {T['chart_history_title']}")
                end_dt = datetime.datetime.now()
                hist_data = yf.download(
                    current_ticker,
                    start=end_dt - datetime.timedelta(days=1825),
                    end=end_dt,
                    progress=False
                )
                if not hist_data.empty and 'Close' in hist_data:
                    st.line_chart(hist_data['Close'])
                else:
                    st.write("暂无历史走势数据")

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

                    if intrinsic_val and abs((intrinsic_val - target_mean) / target_mean) <= 0.15:
                        st.success(T["ws_match"])

            # ==================================================================
            # 重要法律与风险免责声明 (醒目展示在底部)
            # ==================================================================
            st.markdown("---")
            st.warning(f"### {T['disclaimer_title']}\n\n{T['disclaimer_content']}")

        except Exception as e:
            st.error(f"测算失败: 找不到该股票代码或网络异常。请检查代码是否正确（例如马股加 .KL）。错误信息: {e}")
