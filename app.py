# app.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="SIP & Compounding Planner", layout="wide")
st.title("💰 SIP & Compounding Planner")

with st.sidebar:
    st.header("Inputs")
    monthly = st.number_input("Monthly SIP (₹)", min_value=0, value=10000, step=500)
    annual_rate = st.number_input("Expected annual return (%)", min_value=0.0, value=12.0, step=0.1)
    years = st.number_input("Investment horizon (years)", min_value=1, value=20, step=1)
    payment_timing = st.selectbox("Contribution timing", ["End of period (default)", "Start of period (contribute then earn)"])
    show_table = st.checkbox("Show year-wise table", value=True)

st.markdown(
    "This planner assumes monthly compounding. Choose 'Start of period' if you want contributions to "
    "earn interest immediately in the month they are contributed."
)

def simulate_sip(monthly, annual_rate, years, start=False):
    i = annual_rate / 100.0 / 12.0          # monthly rate
    n = int(years * 12)                     # total months
    balances = []
    balance = 0.0
    for m in range(1, n + 1):
        if start:
            balance = (balance + monthly) * (1 + i)   # contribution at start of period
        else:
            balance = balance * (1 + i) + monthly     # contribution at end of period
        balances.append(balance)
    months = np.arange(1, n + 1)
    df = pd.DataFrame({"month": months, "balance": balances})
    df["year"] = ((df["month"] - 1) // 12) + 1
    yearly = df.groupby("year").last().reset_index()
    yearly["invested"] = monthly * (yearly["year"] * 12)
    yearly["returns"] = yearly["balance"] - yearly["invested"]
    return df, yearly

df_monthly, df_yearly = simulate_sip(monthly, annual_rate, years, start=(payment_timing.startswith("Start")))

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

if show_table:
    st.subheader("Year-wise snapshot")
    st.dataframe(df_yearly[["year","invested","balance","returns"]].rename(columns={
        "year":"Year", "invested":"Invested (₹)", "balance":"Estimated Corpus (₹)", "returns":"Returns (₹)"
    }).style.format({"Invested (₹)":"{:.0f}","Estimated Corpus (₹)":"{:.0f}","Returns (₹)":"{:.0f}"}))

csv = df_monthly.to_csv(index=False).encode("utf-8")
st.download_button("Download monthly CSV", data=csv, file_name="sip_monthly.csv", mime="text/csv")
