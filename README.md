# Market Risk Analysis — VaR & GARCH

<p>
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/Plotly-3F4F75?style=for-the-badge&logo=plotly&logoColor=white"/>
  <img src="https://img.shields.io/badge/Jupyter-F37626?style=for-the-badge&logo=jupyter&logoColor=white"/>
  <img src="https://img.shields.io/badge/status-90%25%20complete-yellow?style=for-the-badge"/>
</p>

Quantitative market risk analysis using multiple VaR methodologies and GARCH volatility modeling, applied to **GGAL** (Grupo Financiero Galicia) from mid-2000 to present — covering more than two decades of Argentine market history, including some of the most severe financial crises in the country's history.

> Although this project focuses on GGAL, the methodology is fully transferable to any financial asset.

---

## Overview

This project estimates and validates the **Value at Risk (VaR)** of a financial asset using five different approaches, each with distinct assumptions about return distributions and volatility behavior. It also performs **backtesting** to compare VaR estimates against actual price movements, assessing the statistical validity of each model.

A key feature is the integration of **relevant macroeconomic and political events** in Argentina, mapped directly onto the charts — allowing a clear visual understanding of how external shocks impacted asset behavior and model performance.

---

## What this project does

- Computes VaR using **five methodologies:**
  - Normal (Gaussian) distribution
  - Student's t-distribution
  - Historical simulation
  - Monte Carlo simulation
  - GARCH-based dynamic volatility
- Displays the **mathematical formulas and step-by-step calculations** for each method
- Compares **multiple volatility estimates** side by side (simple, exponential, GARCH)
- Performs **backtesting:** actual returns vs. VaR estimates over time
- Visualizes **return distributions** with empirical probability ranges
- Tracks **exceedances, streaks, and transitions** — counting how often actual losses exceeded the VaR threshold
- Maps **key historical events** (political crises, devaluations, economic shocks) directly on the charts

---

## Key context: why GGAL from 2000?

The dataset starts one year before Argentina's **2001 financial crisis** — one of the largest sovereign defaults in history. This was followed by decades of recurring crises, currency devaluations, capital controls, and extreme volatility events (including the 2018 currency crash and the 2019 PASO election shock).

This makes GGAL an exceptionally demanding test case for risk models — far more challenging than assets from stable markets.

---

## Results & outputs

- 📊 **Interactive Bloomberg-style charts** (Plotly) showing:
  - Historical price and returns
  - VaR estimates over time for each methodology
  - Actual return vs. VaR comparison (backtesting view)
  - Return distribution with empirical probability ranges at 1-day horizon
  - Volatility comparison across methods
- 📋 **Summary tables** with:
  - VaR values by method and confidence level
  - Exceedance counts and percentages
  - Streak analysis and state transitions

---

## Tech stack

| Tool | Purpose |
|---|---|
| `Python` | Core language |
| `pandas` / `NumPy` | Data manipulation and numerical computation |
| `arch` | GARCH model estimation |
| `statsmodels` | Statistical analysis |
| `scipy` | Probability distributions |
| `yfinance` | Historical price data retrieval |
| `Plotly` | Interactive visualizations |
| `Jupyter Notebook` | Development and presentation environment |

---

## Project structure

```
market-risk-var-garch/
│
├── notebooks/
│   └── var_garch_analysis.ipynb   # Main analysis notebook
│
├── src/
│   └── (core Python modules and helper functions)
│
├── data/
│   └── (auto-downloaded via yfinance)
│
├── images/
│   └── (exported chart previews)
│
└── README.md
```

---

## How to run

```bash
# Clone the repository
git clone https://github.com/JonatanSiracusa/market-risk-var-garch.git
cd market-risk-var-garch

# Install dependencies
pip install -r requirements.txt

# Launch the notebook
jupyter notebook notebooks/var_garch_analysis.ipynb
```

---

## Methodology note

Each VaR methodology makes different assumptions:

| Method | Volatility assumption | Distribution |
|---|---|---|
| Normal | Constant | Gaussian |
| Student-t | Constant | Fat-tailed |
| Historical | Implicit in data | Empirical |
| Monte Carlo | Constant or simulated | Configurable |
| GARCH | Dynamic (time-varying) | Configurable |

GARCH-based VaR is particularly relevant in markets with **volatility clustering** — periods of high volatility tend to be followed by more high volatility. Argentine equity markets exhibit this behavior intensely.

---

## Status

🟡 **90% complete** — core analysis and visualizations are functional. Final polish in progress.

---

## Author

**Jonatan Siracusa**
[LinkedIn](https://www.linkedin.com/in/ajsiracusa) · [GitHub](https://github.com/JonatanSiracusa) · [Medium](https://jonatansiracusa.medium.com)
