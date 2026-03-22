import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from datetime import date

st.set_page_config(page_title="Bitcoin Allocation", layout="wide")

st.sidebar.markdown("### 🔗 External Tools")
st.sidebar.markdown(
    "[NiceHash Profitability Calculator](https://www.nicehash.com/profitability-calculator)"
)

st.sidebar.markdown("### ⚡ GPU Efficiency (Quick Check)")

st.sidebar.markdown(
    """
Check up-to-date mining efficiency, hashrates and prices:

- NVIDIA RTX 4060  
- NVIDIA RTX 3070  
- NVIDIA RTX 3060 Ti  
- NVIDIA RTX 4070  
- AMD RX 7900 XTX  

👉 [NiceHash Profitability Calculator](https://www.nicehash.com/profitability-calculator)
"""
)

# -------------------------
# Helpers
# -------------------------
def format_nok(value: float) -> str:
    return f"{value:,.0f} kr".replace(",", " ")

def format_btc(value: float) -> str:
    return f"{value:.6f} BTC"

def month_range(start_year: int, start_month: int, months: int):
    result = []
    year = start_year
    month = start_month
    for _ in range(months):
        result.append((year, month))
        month += 1
        if month > 12:
            month = 1
            year += 1
    return result

def monthly_price_path(start_price: float, end_price: float, months: int, mode: str):
    if months <= 1:
        return [start_price]

    prices = []
    if mode == "Linear":
        step = (end_price - start_price) / (months - 1)
        for i in range(months):
            prices.append(start_price + step * i)
    else:
        # Exponential growth/decline
        if start_price <= 0:
            start_price = 1
        ratio = (end_price / start_price) ** (1 / (months - 1)) if end_price > 0 else 0
        for i in range(months):
            prices.append(start_price * (ratio ** i))
    return prices

def is_after_halving(year: int, month: int, halving_year: int = 2028, halving_month: int = 4):
    return (year > halving_year) or (year == halving_year and month >= halving_month)

# -------------------------
# Title
# -------------------------
st.title("Bitcoin Allocation")
st.write(
    "Compare Bitcoin mining versus buying directly. "
    "This tool focuses on capital allocation, BTC accumulation, future price scenarios, and the 2028 halving effect."
)

# -------------------------
# Sidebar Inputs
# -------------------------
st.sidebar.header("Inputs")

btc_price_today = st.sidebar.number_input(
    "Bitcoin price today (NOK)",
    min_value=1.0,
    value=1_000_000.0,
    step=10_000.0,
)

future_btc_price = st.sidebar.number_input(
    "Future Bitcoin price (NOK)",
    min_value=1.0,
    value=1_800_000.0,
    step=10_000.0,
)

months = st.sidebar.slider(
    "Time horizon (months)",
    min_value=6,
    max_value=60,
    value=36,
    step=1,
)

price_path_mode = st.sidebar.selectbox(
    "BTC price path",
    ["Linear", "Exponential"],
    index=1,
)

st.sidebar.markdown("---")
st.sidebar.subheader("Mining setup")

gpu_price = st.sidebar.number_input(
    "GPU / rig price (NOK)",
    min_value=0.0,
    value=35_000.0,
    step=1_000.0,
)

btc_mined_per_month = st.sidebar.number_input(
    "BTC allocated per month from mining",
    min_value=0.0,
    value=0.0015,
    step=0.0001,
    format="%.6f",
)

power_watts = st.sidebar.number_input(
    "Power usage (watts)",
    min_value=0.0,
    value=1200.0,
    step=50.0,
)

electricity_price = st.sidebar.number_input(
    "Electricity price (NOK per kWh)",
    min_value=0.0,
    value=1.20,
    step=0.05,
)

other_monthly_cost = st.sidebar.number_input(
    "Other monthly cost (NOK)",
    min_value=0.0,
    value=0.0,
    step=100.0,
)

apply_halving = st.sidebar.checkbox(
    "Apply 2028 halving effect",
    value=True,
)

halving_impact = st.sidebar.slider(
    "Halving impact on BTC output (%)",
    min_value=0,
    max_value=100,
    value=50,
    step=5,
    help="50% means monthly BTC mined is cut in half after halving.",
)

st.sidebar.markdown("---")
st.sidebar.subheader("Buy strategy")

buy_with_gpu_upfront = st.sidebar.checkbox(
    "Use GPU cost as upfront BTC purchase in buy scenario",
    value=True,
)

use_monthly_electricity_as_dca = st.sidebar.checkbox(
    "Use avoided mining operating cost as monthly BTC purchase",
    value=True,
)

start_today = date.today()
start_year = start_today.year
start_month = start_today.month

# -------------------------
# Core calculations
# -------------------------
price_path = monthly_price_path(
    start_price=btc_price_today,
    end_price=future_btc_price,
    months=months,
    mode=price_path_mode,
)

month_list = month_range(start_year, start_month, months)

kwh_per_month = (power_watts * 24 * 30) / 1000
monthly_electricity_cost = kwh_per_month * electricity_price
monthly_operating_cost = monthly_electricity_cost + other_monthly_cost

rows = []

cum_btc_mined = 0.0
cum_btc_bought = 0.0
cum_mining_cost = gpu_price
cum_buy_cost = 0.0

if buy_with_gpu_upfront and btc_price_today > 0:
    upfront_btc_bought = gpu_price / btc_price_today
    cum_btc_bought += upfront_btc_bought
    cum_buy_cost += gpu_price
else:
    upfront_btc_bought = 0.0

for i in range(months):
    year, month = month_list[i]
    btc_price_this_month = price_path[i]

    mined_this_month = btc_mined_per_month

    if apply_halving and is_after_halving(year, month):
        mined_this_month *= (1 - halving_impact / 100)

    cum_btc_mined += mined_this_month
    cum_mining_cost += monthly_operating_cost

    bought_this_month = 0.0
    buy_amount_nok_this_month = 0.0

    if use_monthly_electricity_as_dca and btc_price_this_month > 0:
        buy_amount_nok_this_month = monthly_operating_cost
        bought_this_month = buy_amount_nok_this_month / btc_price_this_month
        cum_btc_bought += bought_this_month
        cum_buy_cost += buy_amount_nok_this_month

    rows.append(
        {
            "Month #": i + 1,
            "Year": year,
            "Month": month,
            "BTC Price (NOK)": btc_price_this_month,
            "BTC Mined": mined_this_month,
            "Cumulative BTC Mined": cum_btc_mined,
            "Mining Operating Cost (NOK)": monthly_operating_cost,
            "Cumulative Mining Cost (NOK)": cum_mining_cost,
            "BTC Bought": bought_this_month,
            "Cumulative BTC Bought": cum_btc_bought,
            "Buy Amount This Month (NOK)": buy_amount_nok_this_month,
            "Cumulative Buy Cost (NOK)": cum_buy_cost,
        }
    )

df = pd.DataFrame(rows)

final_price = price_path[-1]

final_value_mining = cum_btc_mined * final_price
final_value_buy = cum_btc_bought * final_price

net_mining = final_value_mining - cum_mining_cost
net_buy = final_value_buy - cum_buy_cost

btc_difference = cum_btc_mined - cum_btc_bought
value_difference = final_value_mining - final_value_buy

# Effective average acquisition cost
avg_cost_per_btc_mining = cum_mining_cost / cum_btc_mined if cum_btc_mined > 0 else None
avg_cost_per_btc_buy = cum_buy_cost / cum_btc_bought if cum_btc_bought > 0 else None

# Break-even current BTC price estimate:
# Compare BTC from mining over horizon against BTC bought directly today + monthly DCA
# Solve simplified threshold where:
# mining BTC over horizon = (upfront capital / P) + sum(monthly DCA / monthly price path dependent on P)
# For simplicity, report today's equivalent break-even from upfront+flat operating assumption:
# total buy BTC if bought all comparable capital at today's price
comparable_capital = gpu_price + (monthly_operating_cost * months)
break_even_buy_price_today = (
    comparable_capital / cum_btc_mined if cum_btc_mined > 0 else None
)

# Mining payback month based on future price path and cumulative net value
payback_month = None
cum_btc_mined_running = 0.0
cum_cost_running = gpu_price

for i in range(months):
    year, month = month_list[i]
    mined_this_month = btc_mined_per_month
    if apply_halving and is_after_halving(year, month):
        mined_this_month *= (1 - halving_impact / 100)

    cum_btc_mined_running += mined_this_month
    cum_cost_running += monthly_operating_cost
    value_running = cum_btc_mined_running * price_path[i]
    if value_running >= cum_cost_running and payback_month is None:
        payback_month = i + 1

# -------------------------
# Top metrics
# -------------------------
st.subheader("Key Metrics")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Cumulative BTC Mined", format_btc(cum_btc_mined))
    st.metric("Mining Final Value", format_nok(final_value_mining))

with col2:
    st.metric("Cumulative BTC Bought", format_btc(cum_btc_bought))
    st.metric("Buy Final Value", format_nok(final_value_buy))

with col3:
    st.metric("Mining Net Result", format_nok(net_mining))
    st.metric("Buy Net Result", format_nok(net_buy))

with col4:
    if break_even_buy_price_today is not None:
        st.metric("BTC Price Where Buy ≈ Mining", format_nok(break_even_buy_price_today))
    else:
        st.metric("BTC Price Where Buy ≈ Mining", "N/A")

    if payback_month is not None:
        st.metric("Mining Payback Month", str(payback_month))
    else:
        st.metric("Mining Payback Month", "Not reached")

# -------------------------
# Summary box
# -------------------------
st.subheader("Interpretation")

if final_value_mining > final_value_buy:
    better_strategy = "Mining"
else:
    better_strategy = "Buying"

summary_lines = [
    f"**Best strategy under current assumptions:** {better_strategy}",
    f"- Mining accumulates **{format_btc(cum_btc_mined)}**",
    f"- Buying accumulates **{format_btc(cum_btc_bought)}**",
    f"- Difference in BTC accumulated: **{format_btc(abs(btc_difference))}**",
    f"- Difference in final value: **{format_nok(abs(value_difference))}**",
]

if avg_cost_per_btc_mining is not None:
    summary_lines.append(f"- Effective average acquisition cost through mining: **{format_nok(avg_cost_per_btc_mining)} per BTC**")

if avg_cost_per_btc_buy is not None:
    summary_lines.append(f"- Effective average acquisition cost through buying: **{format_nok(avg_cost_per_btc_buy)} per BTC**")

if break_even_buy_price_today is not None:
    summary_lines.append(
        f"- If Bitcoin can be bought below roughly **{format_nok(break_even_buy_price_today)} today**, buying becomes more attractive than mining under these assumptions."
    )

if apply_halving:
    summary_lines.append("- The model includes the 2028 halving, reducing future BTC mining output.")

st.markdown("\n".join(summary_lines))

# -------------------------
# Charts
# -------------------------
st.subheader("Charts")

chart_option = st.selectbox(
    "Select chart",
    [
        "Cumulative BTC: Mine vs Buy",
        "BTC Price Path",
        "Cumulative Value: Mine vs Buy",
        "Monthly BTC Allocation",
    ],
)

if chart_option == "Cumulative BTC: Mine vs Buy":
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(df["Month #"], df["Cumulative BTC Mined"], label="Cumulative BTC Mined")
    ax.plot(df["Month #"], df["Cumulative BTC Bought"], label="Cumulative BTC Bought")
    ax.set_xlabel("Month")
    ax.set_ylabel("BTC")
    ax.set_title("Cumulative BTC: Mining vs Buying")
    ax.legend()
    ax.grid(True, alpha=0.3)
    st.pyplot(fig)

elif chart_option == "BTC Price Path":
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(df["Month #"], df["BTC Price (NOK)"])
    ax.set_xlabel("Month")
    ax.set_ylabel("BTC Price (NOK)")
    ax.set_title("Bitcoin Price Path")
    ax.grid(True, alpha=0.3)
    st.pyplot(fig)

elif chart_option == "Cumulative Value: Mine vs Buy":
    value_mining_series = df["Cumulative BTC Mined"] * df["BTC Price (NOK)"]
    value_buy_series = df["Cumulative BTC Bought"] * df["BTC Price (NOK)"]

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(df["Month #"], value_mining_series, label="Mining Value")
    ax.plot(df["Month #"], value_buy_series, label="Buy Value")
    ax.set_xlabel("Month")
    ax.set_ylabel("Value (NOK)")
    ax.set_title("Cumulative Value Over Time")
    ax.legend()
    ax.grid(True, alpha=0.3)
    st.pyplot(fig)

elif chart_option == "Monthly BTC Allocation":
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(df["Month #"], df["BTC Mined"], label="BTC Mined per Month")
    ax.plot(df["Month #"], df["BTC Bought"], label="BTC Bought per Month")
    ax.set_xlabel("Month")
    ax.set_ylabel("BTC")
    ax.set_title("Monthly BTC Allocation")
    ax.legend()
    ax.grid(True, alpha=0.3)
    st.pyplot(fig)

# -------------------------
# Detailed comparison
# -------------------------
st.subheader("Detailed Comparison")

col_a, col_b = st.columns(2)

with col_a:
    st.markdown("### Mining")
    st.write(f"Initial hardware cost: **{format_nok(gpu_price)}**")
    st.write(f"Monthly electricity cost: **{format_nok(monthly_electricity_cost)}**")
    st.write(f"Other monthly cost: **{format_nok(other_monthly_cost)}**")
    st.write(f"Total monthly operating cost: **{format_nok(monthly_operating_cost)}**")
    st.write(f"Total cost over horizon: **{format_nok(cum_mining_cost)}**")
    st.write(f"BTC accumulated: **{format_btc(cum_btc_mined)}**")
    st.write(f"Final value at future BTC price: **{format_nok(final_value_mining)}**")

with col_b:
    st.markdown("### Buying")
    st.write(f"Upfront BTC purchase from GPU cost: **{format_btc(upfront_btc_bought)}**")
    st.write(f"Monthly buy budget from avoided mining cost: **{format_nok(monthly_operating_cost if use_monthly_electricity_as_dca else 0)}**")
    st.write(f"Total capital allocated to buying: **{format_nok(cum_buy_cost)}**")
    st.write(f"BTC accumulated: **{format_btc(cum_btc_bought)}**")
    st.write(f"Final value at future BTC price: **{format_nok(final_value_buy)}**")

# -------------------------
# Monthly table
# -------------------------
st.subheader("Monthly Timeline")

display_df = df.copy()
display_df["BTC Price (NOK)"] = display_df["BTC Price (NOK)"].round(0)
display_df["BTC Mined"] = display_df["BTC Mined"].round(6)
display_df["Cumulative BTC Mined"] = display_df["Cumulative BTC Mined"].round(6)
display_df["Mining Operating Cost (NOK)"] = display_df["Mining Operating Cost (NOK)"].round(0)
display_df["Cumulative Mining Cost (NOK)"] = display_df["Cumulative Mining Cost (NOK)"].round(0)
display_df["BTC Bought"] = display_df["BTC Bought"].round(6)
display_df["Cumulative BTC Bought"] = display_df["Cumulative BTC Bought"].round(6)
display_df["Buy Amount This Month (NOK)"] = display_df["Buy Amount This Month (NOK)"].round(0)
display_df["Cumulative Buy Cost (NOK)"] = display_df["Cumulative Buy Cost (NOK)"].round(0)

st.dataframe(display_df, use_container_width=True)

# -------------------------
# Notes
# -------------------------
st.caption(
    "This is a simplified allocation model. Real mining profitability also depends on network difficulty, pool fees, hardware degradation, downtime, taxes, and possible resale value of equipment."
)
