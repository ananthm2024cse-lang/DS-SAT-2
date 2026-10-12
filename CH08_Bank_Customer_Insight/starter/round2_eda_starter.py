"""
CH08 Bank Customer Insight — Round 2 starter
Run from this project folder:
    python starter/round2_eda_starter.py

This script inspects data quality and creates basic summary CSVs.
It intentionally does not claim findings until it runs on the data.
"""
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "outputs"
OUT.mkdir(exist_ok=True)

files = ["customers", "accounts", "transactions", "channels", "service"]
data = {name: pd.read_csv(DATA / f"{name}.csv") for name in files}

print("=== DATASET OVERVIEW ===")
for name, df in data.items():
    print(f"\n{name}.csv | rows={len(df)} | columns={len(df.columns)}")
    print(df.head(3))
    print("Missing values:\n", df.isna().sum())
    print("Exact duplicate rows:", df.duplicated().sum())

# Standardize account labels
accounts = data["accounts"].copy()
accounts["Account_Type"] = accounts["Account_Type"].replace({
    "saving": "Savings",
    "SAVINGS": "Savings",
    "Current Account": "Current",
    "fixed deposit": "Fixed Deposit"
})
accounts["Account_Type"] = accounts["Account_Type"].fillna("Unknown")

# Remove exact duplicate transaction rows and repeated Transaction_ID records
transactions = data["transactions"].copy()
transactions = transactions.drop_duplicates()
transactions = transactions.drop_duplicates(subset=["Transaction_ID"], keep="first")

# Validate clearly invalid values; retain extreme positive amounts for investigation
customers = data["customers"].copy()
customers.loc[customers["Relationship_Years"] < 0, "Relationship_Years"] = pd.NA

channels = data["channels"].copy()
channels.loc[channels["Usage_Count_30D"] < 0, "Usage_Count_30D"] = pd.NA
channels["Channel"] = channels["Channel"].fillna("Unknown")

service = data["service"].copy()
service.loc[service["Resolution_Days"] < 0, "Resolution_Days"] = pd.NA
service["Is_Complaint"] = service["Is_Complaint"].fillna("Unknown")

# Save cleaned versions
cleaned = {
    "customers_cleaned": customers,
    "accounts_cleaned": accounts,
    "transactions_cleaned": transactions,
    "channels_cleaned": channels,
    "service_cleaned": service,
}
for name, df in cleaned.items():
    df.to_csv(OUT / f"{name}.csv", index=False)

# Summaries at their appropriate grain
channel_summary = channels.groupby("Channel", dropna=False)["Usage_Count_30D"].sum().sort_values(ascending=False)
channel_summary.to_csv(OUT / "channel_usage_summary.csv", header=["Total_Usage_Count_30D"])

monthly = transactions.copy()
monthly["Transaction_Date"] = pd.to_datetime(monthly["Transaction_Date"], errors="coerce")
monthly["Month"] = monthly["Transaction_Date"].dt.to_period("M").astype(str)
monthly.groupby("Month").agg(
    Transaction_Count=("Transaction_ID", "count"),
    Total_Amount=("Amount", "sum"),
    Average_Amount=("Amount", "mean")
).reset_index().to_csv(OUT / "monthly_transaction_summary.csv", index=False)

complaint_summary = service.merge(customers[["Customer_ID", "Region"]], on="Customer_ID", how="left")
complaint_summary = complaint_summary[complaint_summary["Is_Complaint"] == "Yes"]
complaint_summary.groupby("Region").size().rename("Complaint_Count").reset_index().to_csv(
    OUT / "complaints_by_region.csv", index=False
)

# Basic visualization
if not channel_summary.empty:
    channel_summary.plot(kind="bar", title="Banking Channel Usage (30 Days)", ylabel="Usage count")
    plt.tight_layout()
    plt.savefig(OUT / "channel_usage.png", dpi=150)
    plt.close()

print(f"\nFinished. Cleaned files and starter summaries saved in: {OUT}")
print("Review outliers and missing-value choices before submitting your final analysis.")
