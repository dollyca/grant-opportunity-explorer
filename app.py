import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")

@st.cache_data
def load_data():
    return pd.read_csv("clean_sales.csv")

df = load_data()

st.title("Sales Dashboard")

c1, c2, c3 = st.columns(3)

c1.metric("Orders", len(df))
c2.metric("Total Revenue", f"${df['revenue'].sum():,.0f}")
c3.metric("Avg Order", f"${df['revenue'].mean():.2f}")

st.divider()

st.subheader("Revenue by Category")
st.bar_chart(df.groupby("category")["revenue"].sum())

st.subheader("Data Preview")
st.dataframe(df)
