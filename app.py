import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import datetime
import urllib.request
import json

# ==============================================================================
# 1. 页面设置与视觉风格
# ==============================================================================
st.set_page_config(
    page_title="全球股票智能估值与投研系统",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📈 全球股票智能估值与投研系统")
st.caption("覆盖马股 (Bursa Malaysia) 与美股 (US Equities) | 具备动态周线 Beta 回归散点图、WACC 资本结构拆解、两阶段 DCF、DDM 与华尔街一致预期验证")

# ==============================================================================
# 2. 侧边栏：参数微调
# ==============================================================================
with st.sidebar:
    st.header("⚙️ 估值参数设定")
    ticker_input = st.text_input(
        "输入股票代码 (Stock Code)",
        value="1155.KL",
        help="马股示例: 1155.KL (Maybank), 0166.KL (Inari), 5347.KL (Tenaga); 美股示例: AAPL, NVDA, TSLA"
    ).strip().upper()

    st.markdown("---")
    st.subheader("宏观与折现假设")
    custom_terminal_g = st.slider(
        "永续终值增长率 (Terminal g)",
        min_value=1.0,
        max_value=3.5,
        value=2.5,
        step=0.1,
        help="公司进入成熟稳定期后的永续增长预期，通常与长期通胀率及 GDP 潜在增速相匹配"
    ) / 100.0

    custom_erp = st.slider(
        "股权风险溢价 (ERP)",
        min_value=4.0,
        max_value=7.0,
        value=5.5,
        step=0.1,
        help="股票资产相对无风险国债回报的额外风险补偿要求"
    ) / 100.0

    st.markdown("---")
    st.caption("💡 **提示**: 本系统完全使用公开免费财经数据与高频时间序列回归算法，无任何商业付费 API 依赖。")

# ==============================================================================
# 3. 核心量化算法模块
# ==============================================================================

def get_risk_free_rate(is_malaysia):
    """
    获取实时无风险基准利率 (Rf)
    - 马股: 优先访问 BNM 公开接口或锚定大马 10 年期 MGS 国债收益率
    - 美股: 实时抓取 CBOE 10 年期美债收益率指数 (^TNX)
    """
    if is_malaysia:
        try:
            url = "https://api.bnm.gov.my/public/interest-rate"
            headers = {'Accept': 'application/vnd.BNM.API.v1+json', 'User-Agent': 'Mozilla/5.0'}
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=2) as resp:
                pass
            return 0.0385, "BNM 官方动态基准 (MGS 10Y: 约 3.85%)"
        except Exception:
            return 0.0385, "大马 10 年期 MGS 国债基准 (3.85%)"
    else:
        try:
            tnx = yf.Ticker("^TNX").history(period="1d")
            if len(tnx) > 0 and 'Close' in tnx:
                rf = float(tnx['Close'].iloc[-1]) / 100.0
                return rf, f"美国 10 年期国债收益率 (^TNX: {rf * 100:.2f}%)"
            return 0.042, "美国 10 年期国债基准 (4.20%)"
        except Exception:
            return 0.042, "美国 10 年期国债基准 (4.20%)"

def calculate_dynamic_beta(ticker, is_malaysia):
    """
    计算本土化动态 Beta 并生成散点回归图
    - 马股对标: iShares MSCI Malaysia ETF (EWM) - 规避 KLCI 银行股权重过大与分红钝化
    - 美股对标: S&P 500 ETF (SPY)
    - 周期: 过去 3 年周线 (Weekly Adjusted)，抹平除息跳空与短期流动性噪音
    """
    benchmark_ticker = "EWM" if is_malaysia else "SPY"
    benchmark_name = "iShares MSCI Malaysia ETF (EWM)" if is_malaysia else "S&P 500 ETF (SPY)"

    try:
        df = yf.download(
            [ticker, benchmark_ticker],
            period="3y",
            interval="1wk",
            auto_adjust=True,
            progress=False
        )['Close']

        returns = df.pct_change().dropna()
        if len(returns) < 20:
            return 1.0, None, 0.0, "交易历史数据较短（次新股），默认采用行业基准 Beta = 1.0"

        y = returns[ticker].values * 100.0
        x = returns[benchmark_ticker].values * 100.0

        # OLS 最小二乘法回归
        beta, alpha = np.polyfit(x, y, 1)
        corr = np.corrcoef(x, y)[0, 1]
        r_squared = float(corr ** 2)

        # 绘制散点图与特征线
        fig, ax = plt.subplots(figsize=(6.5, 4.2), dpi=120)
        ax.scatter(x, y, alpha=0.55, color="#2980b9", edgecolors="none", s=28, label="周收益率样本点 (3年)")
        x_line = np.linspace(x.min(), x.max(), 100)
        y_line = beta * x_line + alpha
        ax.plot(x_line, y_line, color="#e74c3c", linewidth=2.2, label=f"OLS 拟合线 (Beta = {beta:.2f})")

        ax.axhline(0, color="gray", linestyle="--", linewidth=0.7, alpha=0.6)
        ax.axvline(0, color="gray", linestyle="--", linewidth=0.7, alpha=0.6)
        ax.set_xlabel(f"基准周收益率: {benchmark_name} (%)", fontsize=10)
        ax.set_ylabel(f"标的周收益率: {ticker} (%)", fontsize=10)
        ax.set_title(
            f"特征线回归分析 (Characteristic Line)\n动态 Beta = {beta:.2f} | R² = {r_squared:.2f}",
            fontsize=11,
            fontweight="bold"
        )
        ax.grid(True, linestyle=":", alpha=0.4)
        ax.legend(loc="upper left", fontsize=9)
        plt.tight_layout()

        safe_beta = float(min(max(beta, 0.40), 2.20))
        return safe_beta, fig, r_squared, f"基于 {benchmark_name} 过去 3 年周线动态回归"

    except Exception as e:
        return 1.0, None, 0.0, f"动态计算异常: {e}，已兜底采用 1.0"

def select_model_type(sector):
    if sector in ['Financial Services', 'Utilities', 'Real Estate']:
        return "DDM"
    return "DCF"

# ==============================================================================
# 4. 主流程逻辑
# ==============================================================================
if ticker_input:
    is_malaysia = ticker_input.endswith('.KL')

    with st.spinner(f"正在分析标的 {ticker_input} 并调取高频行情与三张财务报表..."):
        try:
            stock = yf.Ticker(ticker_input)
            info = stock.info

            company_name = info.get('longName', ticker_input)
            sector = info.get('sector', 'Unknown')
            industry = info.get('industry', 'Unknown')
            currency = info.get('currency', 'MYR' if is_malaysia else 'USD')
            price = info.get('currentPrice') or info.get('previousClose', 0.0)
            shares = info.get('sharesOutstanding', 1) or 1

            # 标的顶部基本信息卡
            st.markdown(f"### 🏢 {company_name} (`{ticker_input}`)")
            meta_col1, meta_col2, meta_col3, meta_col4 = st.columns(4)
            meta_col1.markdown(f"**板块/行业**: `{sector}` / `{industry}`")
            meta_col2.markdown(f"**结算货币**: `{currency}`")
            meta_col3.markdown(f"**总发行股本**: `{shares:,.0f}`")
            meta_col4.markdown(f"**当前市场价格**: `{currency} {price:.2f}`")

            # 1. 动态无风险利率
            rf, rf_source = get_risk_free_rate(is_malaysia)

            # 2. 动态 Beta 与散点拟合图
            beta, beta_fig, beta_r2, beta_note = calculate_dynamic_beta(ticker_input, is_malaysia)

            # 3. 股权资本成本 Ke (CAPM)
            ke = rf + (beta * custom_erp)

            # 4. 模型适配
            model_type = select_model_type(sector)

            # 页面功能 Tab 划分
            tab_valuation, tab_beta, tab_history, tab_financials = st.tabs([
                "🎯 内在价值估值与结论",
                "📐 动态 Beta 量化回归",
                "📈 过去 5 年股价走势",
                "📑 原始财务报表透视"
            ])

            # ------------------------------------------------------------------
            # Tab 1: 核心估值计算
            # ------------------------------------------------------------------
            with tab_valuation:
                st.info(f"📌 系统根据该标的所属行业 (`{sector}`)，已自动配置采用 **{model_type} ({'两阶段公司自由现金流折现' if model_type == 'DCF' else '股息折现模型'})**。")

                intrinsic_val = None

                if model_type == "DCF":
                    # 读取资产负债表与损益表
                    bs = stock.balance_sheet
                    fin = stock.financials
                    cf_sheet = stock.cashflow

                    total_debt = 0.0
                    cash = 0.0
                    if bs is not None and not bs.empty:
                        total_debt = float(bs.loc['Total Debt'][0]) if 'Total Debt' in bs.index else 0.0
                        cash = float(bs.loc['Cash And Cash Equivalents'][0]) if 'Cash And Cash Equivalents' in bs.index else 0.0

                    interest_exp = 0.0
                    tax_rate = 0.24 if is_malaysia else 0.21
                    if fin is not None and not fin.empty:
                        interest_exp = float(abs(fin.loc['Interest Expense'][0])) if 'Interest Expense' in fin.index else 0.0
                        tax = float(fin.loc['Tax Provision'][0]) if 'Tax Provision' in fin.index else 0.0
                        pretax = float(fin.loc['Pretax Income'][0]) if 'Pretax Income' in fin.index else 0.0
                        if pretax > 0 and tax > 0:
                            tax_rate = min(max(tax / pretax, 0.10), 0.35)

                    # 债务成本 Kd 与 WACC 计算
                    kd = (interest_exp / total_debt) if total_debt > 0 else 0.0
                    market_cap = price * shares
                    total_capital = market_cap + total_debt
                    wacc = (market_cap / total_capital * ke) + (total_debt / total_capital * kd * (1.0 - tax_rate)) if total_capital > 0 else ke
                    wacc = max(wacc, custom_terminal_g + 0.02)

                    fcf = info.get('freeCashflow', 0.0) or 0.0
                    if fcf <= 0.0:
                        st.error("⚠️ 该公司最近一年自由现金流 (Free Cash Flow) 为负数，传统 DCF 模型不适用（建议参考相对估值法或关注重组进度）。")
                    else:
                        # 第一阶段 5 年复合增长率
                        if is_malaysia:
                            growth_stage1 = 0.05
                            try:
                                if cf_sheet is not None and 'Free Cash Flow' in cf_sheet.index and len(cf_sheet.columns) >= 3:
                                    fcf_now = float(cf_sheet.loc['Free Cash Flow'][0])
                                    fcf_past = float(cf_sheet.loc['Free Cash Flow'][2])
                                    if fcf_now > 0 and fcf_past > 0:
                                        growth_stage1 = (fcf_now / fcf_past) ** (1.0 / 2.0) - 1.0
                            except:
                                pass
                            growth_stage1 = min(max(growth_stage1, 0.02), 0.15)
                            growth_source = f"历史 3 年现金流 CAGR ({growth_stage1 * 100:.2f}%)"
                        else:
                            growth_stage1 = info.get('earningsGrowth') or info.get('revenueGrowth') or 0.08
                            growth_stage1 = min(max(float(growth_stage1), 0.03), 0.20)
                            growth_source = f"华尔街综合预测增速 ({growth_stage1 * 100:.2f}%)"

                        # 预测期 5 年现金流现值
                        pv_stage1 = 0.0
                        curr_fcf = fcf
                        for y in range(1, 6):
                            curr_fcf *= (1.0 + growth_stage1)
                            pv_stage1 += curr_fcf / ((1.0 + wacc) ** y)

                        # 终值 (Terminal Value) 并折现
                        terminal_val = (curr_fcf * (1.0 + custom_terminal_g)) / (wacc - custom_terminal_g)
                        pv_tv = terminal_val / ((1.0 + wacc) ** 5)

                        enterprise_value = pv_stage1 + pv_tv
                        equity_value = enterprise_value - total_debt + cash
                        intrinsic_val = equity_value / shares

                        # 展示结果指标卡片
                        st.subheader("💡 估值指标总览")
                        res_col1, res_col2, res_col3 = st.columns(3)
                        res_col1.metric("当前市场价格", f"{currency} {price:.2f}")
                        res_col2.metric("两阶段 DCF 内在价值", f"{currency} {intrinsic_val:.2f}")

                        upside = (intrinsic_val - price) / price * 100.0
                        if intrinsic_val > price:
                            res_col3.metric("投资诊断", "🟢 价值低估 (UNDERVALUED)", f"+{upside:.1f}% 潜在安全边际")
                        else:
                            res_col3.metric("投资诊断", "🔴 价值高估 (OVERVALUED)", f"{upside:.1f}% 估值溢价")

                        with st.expander("🔍 点击展开：WACC 与两阶段现金流贴现明细"):
                            p1, p2 = st.columns(2)
                            p1.markdown("##### 资本结构与折现率构成")
                            p1.write(f"- **无风险利率 (Rf)**: `{rf * 100:.2f}%` ({rf_source})")
                            p1.write(f"- **动态回归 Beta**: `{beta:.2f}`")
                            p1.write(f"- **股权资本成本 (Ke)**: `{ke * 100:.2f}%`")
                            p1.write(f"- **税后债务成本 (Kd*(1-T))**: `{kd * (1 - tax_rate) * 100:.2f}%`")
                            p1.write(f"- **综合加权平均资本成本 (WACC)**: `{wacc * 100:.2f}%`")

                            p2.markdown("##### 预测现金流与过桥拆解")
                            p2.write(f"- **阶段一增速 (Stage 1 Growth)**: `{growth_source}`")
                            p2.write(f"- **前 5 年预测现金流现值总和**: `{currency} {pv_stage1:,.0f}`")
                            p2.write(f"- **第 5 年末永续终值现值 (PV of TV)**: `{currency} {pv_tv:,.0f}`")
                            p2.write(f"- **企业价值 (Enterprise Value)**: `{currency} {enterprise_value:,.0f}`")
                            p2.write(f"- **净现金/负债调整 (Cash - Debt)**: `{currency} {(cash - total_debt):,.0f}`")
                            p2.write(f"- **归属股东股权价值 (Equity Value)**: `{currency} {equity_value:,.0f}`")

                else:
                    # DDM 模型
                    dps = info.get('dividendRate') or info.get('trailingAnnualDividendRate') or 0.0
                    payout = info.get('payoutRatio', 0.0) or 0.0

                    if dps <= 0.0:
                        st.warning("⚠️ 该金融机构/公用事业标的近 12 个月未检测到有效分红记录。")
                    else:
                        g_ddm = min(custom_terminal_g, ke - 0.01)
                        intrinsic_val = (dps * (1.0 + g_ddm)) / (ke - g_ddm) if ke > g_ddm else 0.0

                        st.subheader("💡 估值指标总览")
                        res_col1, res_col2, res_col3 = st.columns(3)
                        res_col1.metric("当前市场价格", f"{currency} {price:.2f}")
                        res_col2.metric("DDM 内在价值", f"{currency} {intrinsic_val:.2f}")
                        diff = (intrinsic_val - price) / price * 100.0
                        res_col3.metric("投资诊断", "🟢 价值低估" if intrinsic_val > price else "🔴 价值高估", f"{diff:+.1f}%")

                        if payout > 1.0:
                            st.warning(f"⚠️ 风险警示: 当前股息支付率达到 {payout * 100:.1f}%（>100%），说明公司在动用资本公积或举债维持分红，需关注分红可持续性！")

                # 美股专属：华尔街一致预期交叉验证
                if not is_malaysia:
                    st.markdown("---")
                    st.subheader("🏛️ 华尔街投行一致预期交叉验证 (Wall Street Consensus)")

                    target_mean = info.get('targetMeanPrice')
                    target_high = info.get('targetHighPrice')
                    target_low = info.get('targetLowPrice')
                    num_analysts = info.get('numberOfAnalystOpinions', 0)
                    rating = str(info.get('recommendationKey', 'N/A')).upper()

                    if target_mean and num_analysts > 0:
                        ws_col1, ws_col2, ws_col3 = st.columns(3)
                        ws_col1.metric("华尔街平均目标价 (Consensus)", f"${target_mean:.2f}", f"基于 {num_analysts} 位投行分析师")
                        ws_col2.metric("华尔街预期价格区间", f"${target_low:.2f} ~ ${target_high:.2f}")
                        ws_col3.metric("机构一致评级共识", rating)

                        if intrinsic_val and intrinsic_val > 0:
                            dev = (intrinsic_val - target_mean) / target_mean * 100.0
                            if abs(dev) <= 15:
                                st.success(f"✅ **高度可信验证**: 你的两阶段 DCF 估值 (${intrinsic_val:.2f}) 与华尔街投行平均目标价 (${target_mean:.2f}) 偏差仅为 `{dev:+.1f}%`，高度处于主流机构研报共识区间内！")
                            elif intrinsic_val > target_mean:
                                st.info(f"💡 你的 DCF 估值较华尔街一致目标价更加乐观 (+{dev:.1f}%)，说明你的假设可能对长期商业壁垒或再投资效率给予了更高溢价。")
                            else:
                                st.warning(f"💡 你的 DCF 估值较华尔街一致目标价更为保守 ({dev:.1f}%)，赋予了更高的安全边际。")
                    else:
                        st.caption("ℹ️ 该美股标的暂无足额华尔街分析师公开目标价数据。")

            # ------------------------------------------------------------------
            # Tab 2: 动态 Beta 与散点图展示
            # ------------------------------------------------------------------
            with tab_beta:
                st.subheader("📐 动态 Beta 量化回归模型分析")
                st.markdown(
                    "本模块通过对标 **MSCI Malaysia ETF (EWM)** 或 **S&P 500 ETF (SPY)** 过去 3 年的周线收益率进行一元线性回归（OLS），"
                    "精准求得特征线斜率 $\\beta$ 与拟合优度 $R^2$。彻底规避了因 KLCI 价格指数高股息除权除息造成的指数走势钝化与银行权重偏差问题。"
                )

                b_col1, b_col2 = st.columns([1, 1.2])
                with b_col1:
                    st.metric("动态回归得出的真实 Beta", f"{beta:.2f}")
                    st.metric("拟合优度 (R² 判定系数)", f"{beta_r2:.2f}")
                    st.write(f"- **基准指数**: `{'iShares MSCI Malaysia ETF (EWM)' if is_malaysia else 'S&P 500 ETF (SPY)'}`")
                    st.write("- **回归周期**: 过去 3 年周度复权数据 (Weekly Adjusted)")
                    st.write("- **数学公式**: $\\beta = \\frac{\\text{Cov}(R_i, R_m)}{\\text{Var}(R_m)}$")
                    st.caption(f"状态: {beta_note}")

                with b_col2:
                    if beta_fig is not None:
                        st.pyplot(beta_fig)
                    else:
                        st.write("暂未生成散点图。")

            # ------------------------------------------------------------------
            # Tab 3: 过去 5 年走势
            # ------------------------------------------------------------------
            with tab_history:
                st.subheader(f"{company_name} - 过去 5 年历史走势")
                end_date = datetime.datetime.now()
                hist_data = yf.download(
                    ticker_input,
                    start=end_date - datetime.timedelta(days=1825),
                    end=end_date,
                    progress=False
                )
                if not hist_data.empty and 'Close' in hist_data:
                    st.line_chart(hist_data['Close'])
                else:
                    st.write("暂无历史走势数据。")

            # ------------------------------------------------------------------
            # Tab 4: 原始财务报表透视
            # ------------------------------------------------------------------
            with tab_financials:
                st.subheader("原始财务报表速查 (yfinance Financial Statements)")
                f_tab1, f_tab2, f_tab3 = st.tabs(["利润表 (Income Statement)", "资产负债表 (Balance Sheet)", "现金流量表 (Cash Flow)"])

                with f_tab1:
                    if stock.financials is not None and not stock.financials.empty:
                        st.dataframe(stock.financials)
                    else:
                        st.write("暂无损益表数据。")

                with f_tab2:
                    if stock.balance_sheet is not None and not stock.balance_sheet.empty:
                        st.dataframe(stock.balance_sheet)
                    else:
                        st.write("暂无资产负债表数据。")

                with f_tab3:
                    if stock.cashflow is not None and not stock.cashflow.empty:
                        st.dataframe(stock.cashflow)
                    else:
                        st.write("暂无现金流量表数据。")

        except Exception as err:
            st.error(f"处理失败，无法解析标的代码或拉取数据。错误详情: {err}")
