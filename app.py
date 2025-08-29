# app.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="SIP & Compounding Planner", layout="wide")
st.title("💰 SIP & Compounding Planner")

with st.sidebar:
    st.header("Inputs")
    initial = st.number_input("Initial Investment (₹)", min_value=0, value=0, step=1000)
    monthly = st.number_input("Monthly SIP (₹)", min_value=0, value=10000, step=500)
    annual_rate = st.number_input("Expected annual return (%)", min_value=0.0, value=12.0, step=0.1)
    years = st.number_input("Investment horizon (years)", min_value=1, value=20, step=1)
    payment_timing = st.selectbox("Contribution timing", ["End of period (default)", "Start of period (contribute then earn)"])
    show_table = st.checkbox("Show year-wise table", value=True)

st.markdown(
    "This planner assumes monthly compounding. Choose 'Start of period' if you want contributions to "
    "earn interest immediately in the month they are contributed."
)

def simulate_sip(monthly, annual_rate, years, start=False, initial=0):
    i = annual_rate / 100.0 / 12.0          # monthly rate
    n = int(years * 12)                     # total months
    balances = []
    balance = initial                       # start with initial investment
    for m in range(1, n + 1):
        if start:
            balance = (balance + monthly) * (1 + i)   # contribution at start
        else:
            balance = balance * (1 + i) + monthly     # contribution at end
        balances.append(balance)

    months = np.arange(1, n + 1)
    df = pd.DataFrame({"month": months, "balance": balances})
    df["year"] = ((df["month"] - 1) // 12) + 1

    yearly = df.groupby("year").last().reset_index()
    yearly["invested"] = (monthly * (yearly["year"] * 12)) + initial
    yearly["returns"] = yearly["balance"] - yearly["invested"]

    return df, yearly

st.subheader("📈 Mutual Fund Tracker (Mock Data)")

# Mock dataset of funds (you can replace later with real API/CSV)
data = {
    "Fund": ["Alpha Growth Fund", "Beta Equity Fund", "Gamma Balanced Fund"],
    "CAGR (%)": [12.5, 15.2, 10.8],
    "3Y Return (%)": [42.0, 52.5, 35.0],
    "5Y Return (%)": [80.0, 100.0, 65.0],
}
df_funds = pd.DataFrame(data)

# Show the mock fund table
st.dataframe(df_funds)

# Let user select funds to compare
selected_funds = st.multiselect("Select funds to compare", df_funds["Fund"].tolist(), default=df_funds["Fund"].tolist())

if selected_funds:
    # Filter selected
    df_sel = df_funds[df_funds["Fund"].isin(selected_funds)]

    # Plot CAGR comparison
    fig3 = px.bar(df_sel, x="Fund", y="CAGR (%)", title="CAGR Comparison", text="CAGR (%)")
    st.plotly_chart(fig3, use_container_width=True)

    # Optional: Show returns table nicely formatted
    st.write("📊 Selected Fund Performance")
    st.dataframe(df_sel.style.format({"CAGR (%)": "{:.1f}", "3Y Return (%)": "{:.1f}", "5Y Return (%)": "{:.1f}"}))



df_monthly, df_yearly = simulate_sip(monthly, annual_rate, years, start=(payment_timing.startswith("Start")), initial=initial)

final_balance = df_monthly["balance"].iloc[-1]
total_invested = monthly * years * 12
total_returns = final_balance - total_invested

col1, col2, col3 = st.columns([1,1,1])
col1.metric("Total Invested (₹)", f"{total_invested:,.0f}")
col2.metric("Estimated Corpus (₹)", f"{final_balance:,.0f}")
col3.metric("Estimated Returns (₹)", f"{total_returns:,.0f}")

st.subheader("Growth over time")
fig = px.line(df_yearly, x="year", y=["invested", "balance"],
              labels={"value":"Amount (₹)", "year":"Year"},
              title="Invested vs Estimated Corpus")
st.plotly_chart(fig, use_container_width=True)

st.subheader("📊 What-if Growth Comparison")

# Predefined return rates
rates = [12, 15, 18]

comparison = []
fig2 = px.line(title="Corpus Growth at Different Return Rates")

for r in rates:
    _, df_yearly_r = simulate_sip(monthly, r, years, start=(payment_timing.startswith("Start")))
    final_val = df_yearly_r["balance"].iloc[-1]
    comparison.append({"Rate (%)": r, "Final Corpus (₹)": final_val})
    
    fig2.add_scatter(
        x=df_yearly_r["year"], 
        y=df_yearly_r["balance"], 
        mode="lines", 
        name=f"{r}%"
    )

fig2.update_layout(xaxis_title="Year", yaxis_title="Corpus (₹)")
st.plotly_chart(fig2, use_container_width=True)

# Show final corpus table
df_comp = pd.DataFrame(comparison)
st.dataframe(df_comp.style.format({"Final Corpus (₹)": "{:,.0f}"}))

if show_table:
    st.subheader("Year-wise snapshot")
    st.dataframe(df_yearly[["year","invested","balance","returns"]].rename(columns={
        "year":"Year", "invested":"Invested (₹)", "balance":"Estimated Corpus (₹)", "returns":"Returns (₹)"
    }).style.format({"Invested (₹)":"{:.0f}","Estimated Corpus (₹)":"{:.0f}","Returns (₹)":"{:.0f}"}))

csv = df_monthly.to_csv(index=False).encode("utf-8")
st.download_button("Download monthly CSV", data=csv, file_name="sip_monthly.csv", mime="text/csv")
