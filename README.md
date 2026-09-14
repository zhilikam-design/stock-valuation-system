# 📈 全球股票智能估值与投研系统 (Global Stock Valuation & Research System)

基于 Python 与 Streamlit 构建的轻量级、免 API 费用的股票内在价值分析与量化投研平台。支持**马股 (Bursa Malaysia)** 与**美股 (US Equities)**。

---

## 🌟 核心功能与金融学术亮点

1. **马股专属动态 Beta 回归模型与特征线散点图 (MSCI Benchmark)**
   - **对标优化**: 规避富时大马综指 (KLCI) 因银行巨头权重过大及高分红除权除息造成的走势钝化缺陷，采用 **iShares MSCI Malaysia ETF (EWM)** 作为本土基准（美股采用 SPY）。
   - **量化算法**: 采用过去 3 年**周度复权收益率 (Weekly Adjusted Returns)**，抹平日常非同步交易偏差与除息跳空噪音，以最小二乘法 (OLS) 现场回归求得特征线斜率 $\beta$ 与拟合优度 $R^2$。

2. **严谨的两阶段公司自由现金流贴现模型 (Two-Stage DCF)**
   - **资本结构拆解 (WACC)**: 从 `yfinance` 真实报表中提取总有息负债、现金及等价物、利息支出与有效税率，严格根据资本结构权重加权计算 $WACC$。
   - **两阶段增长**: 
     - 阶段一（前 5 年显式预测期）：马股结合历史 3 年自由现金流 CAGR 并施加合理安全上限，美股结合华尔街未来增长预测；
     - 阶段二（永续终值期 TV）：通过戈登模型贴现终值。
   - **过桥拆解**: 企业价值 (Enterprise Value) $\to$ 扣减净负债 (Debt - Cash) $\to$ 归属普通股股东的股权价值 (Equity Value) $\to$ 每股内在价值。

3. **美股专属：华尔街一致预期交叉验证 (Wall Street Consensus)**
   - 自动获取数十位华尔街机构分析师的**平均目标价 (Target Mean)**、**最高/最低预测区间**以及**综合评级**。
   - 与自主两阶段 DCF 模型估值结果进行横向偏差诊断，兼具学术独立性与投行共识说服力。

4. **金融与公用事业专属：股息折现模型 (DDM)**
   - 针对银行、保险、公用事业及房地产信托 (REITs) 等高杠杆商业模式，自适应切换为 DDM 模型。
   - 包含股息支付率超 100% 的财务健康预警机制。

---

## 🚀 本地运行指南

1. **克隆项目并安装依赖**:
   ```bash
   git clone https://github.com/zhilikam-design/stock-valuation-system.git
   cd stock-valuation-system
   pip install -r requirements.txt
   ```

2. **启动 Streamlit 网页**:
   ```bash
   streamlit run app.py
   ```

---

## 🌐 云端部署说明

本项目适配 **Streamlit Community Cloud**，可一键免费托管至公网。
访问地址格式：`https://[your-app-name].streamlit.app`

---

## 🛠️ 技术栈
- **Web 交互**: [Streamlit](https://streamlit.io/)
- **金融数据提取**: [yfinance](https://github.com/ranaroussi/yfinance)
- **数据处理与量化回归**: Pandas, NumPy, Matplotlib
