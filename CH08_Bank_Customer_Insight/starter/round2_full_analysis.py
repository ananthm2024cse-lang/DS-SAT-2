"""CH08 Bank Customer Insight — full Round 2 analysis.

This script cleans the synthetic banking dataset, documents the main data-quality
rules applied, creates engineered features, and saves summary CSVs and charts to
`outputs/`.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "outputs"
OUT.mkdir(exist_ok=True)


def standardize_account_type(value: object) -> str:
    if pd.isna(value):
        return "Unknown"

    cleaned = str(value).strip().lower().replace("_", " ")
    mapping = {
        "saving": "Savings",
        "savings": "Savings",
        "savings account": "Savings",
        "current": "Current",
        "current account": "Current",
        "checking": "Current",
        "fixed deposit": "Fixed Deposit",
        "fixed deposit account": "Fixed Deposit",
        "term deposit": "Fixed Deposit",
        "loan": "Loan",
    }
    return mapping.get(cleaned, cleaned.title())


def cap_outliers(series: pd.Series) -> pd.Series:
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    return series.clip(lower=lower_bound, upper=upper_bound)


def clean_customers(df: pd.DataFrame) -> pd.DataFrame:
    cleaned = df.copy()
    cleaned["Region"] = cleaned["Region"].fillna("Unknown")

    cleaned["Relationship_Years"] = pd.to_numeric(cleaned["Relationship_Years"], errors="coerce")
    invalid_rel = cleaned["Relationship_Years"] < 0
    if invalid_rel.any():
        cleaned.loc[invalid_rel, "Relationship_Years"] = pd.NA
    median_years = cleaned["Relationship_Years"].median()
    cleaned["Relationship_Years"] = cleaned["Relationship_Years"].fillna(median_years)
    return cleaned


def clean_accounts(df: pd.DataFrame) -> pd.DataFrame:
    cleaned = df.copy()
    cleaned["Account_Type"] = cleaned["Account_Type"].map(standardize_account_type)
    cleaned["Status"] = cleaned["Status"].fillna("Unknown")
    return cleaned


def clean_transactions(df: pd.DataFrame) -> pd.DataFrame:
    cleaned = df.drop_duplicates().drop_duplicates(subset=["Transaction_ID"], keep="first").copy()
    cleaned["Channel"] = cleaned["Channel"].fillna("Unknown")
    cleaned["Amount"] = pd.to_numeric(cleaned["Amount"], errors="coerce")

    negative_amounts = cleaned["Amount"] < 0
    if negative_amounts.any():
        cleaned.loc[negative_amounts, "Amount"] = pd.NA

    valid_amounts = cleaned["Amount"].dropna()
    if not valid_amounts.empty:
        median_amount = valid_amounts.median()
        cleaned["Amount"] = cleaned["Amount"].fillna(median_amount)
        cleaned["Amount"] = cap_outliers(cleaned["Amount"])

    cleaned["Transaction_Date"] = pd.to_datetime(cleaned["Transaction_Date"], errors="coerce")
    return cleaned


def clean_channels(df: pd.DataFrame) -> pd.DataFrame:
    cleaned = df.copy()
    cleaned["Channel"] = cleaned["Channel"].fillna("Unknown")
    cleaned["Usage_Count_30D"] = pd.to_numeric(cleaned["Usage_Count_30D"], errors="coerce")
    invalid_usage = cleaned["Usage_Count_30D"] < 0
    if invalid_usage.any():
        cleaned.loc[invalid_usage, "Usage_Count_30D"] = pd.NA
    median_usage = cleaned["Usage_Count_30D"].median()
    cleaned["Usage_Count_30D"] = cleaned["Usage_Count_30D"].fillna(median_usage)
    return cleaned


def clean_service(df: pd.DataFrame) -> pd.DataFrame:
    cleaned = df.copy()
    cleaned["Is_Complaint"] = cleaned["Is_Complaint"].fillna("Unknown")
    cleaned["Resolution_Days"] = pd.to_numeric(cleaned["Resolution_Days"], errors="coerce")
    invalid_resolution = cleaned["Resolution_Days"] < 0
    if invalid_resolution.any():
        cleaned.loc[invalid_resolution, "Resolution_Days"] = pd.NA
    median_resolution = cleaned["Resolution_Days"].median()
    cleaned["Resolution_Days"] = cleaned["Resolution_Days"].fillna(median_resolution)
    return cleaned


def save_summary_csv(df: pd.DataFrame, filename: str) -> None:
    df.to_csv(OUT / filename, index=False)


def build_analytics(
    customers: pd.DataFrame,
    accounts: pd.DataFrame,
    transactions: pd.DataFrame,
    channels: pd.DataFrame,
    service: pd.DataFrame,
) -> None:
    channel_summary = (
        channels.groupby("Channel", dropna=False)["Usage_Count_30D"].sum().sort_values(ascending=False).reset_index()
    )
    channel_summary.columns = ["Channel", "Total_Usage_Count_30D"]
    save_summary_csv(channel_summary, "channel_usage_summary.csv")

    monthly = transactions.copy()
    monthly["Month"] = monthly["Transaction_Date"].dt.to_period("M").astype(str)
    monthly_summary = (
        monthly.groupby("Month")
        .agg(
            Transaction_Count=("Transaction_ID", "count"),
            Total_Amount=("Amount", "sum"),
            Average_Amount=("Amount", "mean"),
        )
        .reset_index()
    )
    save_summary_csv(monthly_summary, "monthly_transaction_summary.csv")

    complaint_summary = service.merge(customers[["Customer_ID", "Region"]], on="Customer_ID", how="left")
    complaint_summary = (
        complaint_summary.groupby("Region")
        .agg(
            Complaint_Count=("Is_Complaint", lambda s: (s == "Yes").sum()),
            Total_Requests=("Service_ID", "count"),
        )
        .reset_index()
    )
    complaint_summary["Complaint_Rate"] = complaint_summary["Complaint_Count"] / complaint_summary["Total_Requests"]
    save_summary_csv(complaint_summary, "complaints_by_region.csv")

    account_counts = (
        accounts.groupby("Customer_ID", as_index=False)["Account_ID"].count().rename(columns={"Account_ID": "Account_Count"})
    )
    customer_features = customers.merge(account_counts, on="Customer_ID", how="left")

    digital_usage = (
        channels[channels["Channel"].isin(["Mobile", "Internet"])].groupby("Customer_ID", as_index=False)["Usage_Count_30D"].sum()
    )
    digital_usage = digital_usage.rename(columns={"Usage_Count_30D": "Digital_Usage_Count_30D"})
    total_usage = channels.groupby("Customer_ID", as_index=False)["Usage_Count_30D"].sum().rename(columns={"Usage_Count_30D": "Channel_Usage_Total"})
    customer_features = customer_features.merge(total_usage, on="Customer_ID", how="left")
    customer_features = customer_features.merge(digital_usage, on="Customer_ID", how="left")
    customer_features["Digital_Usage_Share"] = customer_features["Digital_Usage_Count_30D"].fillna(0) / customer_features["Channel_Usage_Total"].fillna(1)
    customer_features["Digital_Usage_Share"] = customer_features["Digital_Usage_Share"].fillna(0)

    service_features = (
        service.groupby("Customer_ID", as_index=False)
        .agg(
            Complaint_Count=("Is_Complaint", lambda s: (s == "Yes").sum()),
            Service_Request_Count=("Service_ID", "count"),
            Avg_Resolution_Days=("Resolution_Days", "mean"),
        )
    )
    customer_features = customer_features.merge(service_features, on="Customer_ID", how="left")
    customer_features["Complaint_Count"] = customer_features["Complaint_Count"].fillna(0)
    customer_features["Service_Request_Count"] = customer_features["Service_Request_Count"].fillna(0)
    customer_features["Avg_Resolution_Days"] = customer_features["Avg_Resolution_Days"].fillna(0)
    save_summary_csv(customer_features, "customer_feature_summary.csv")

    account_status_summary = (
        accounts.groupby(["Account_Type", "Status"], as_index=False)["Account_ID"].count().rename(columns={"Account_ID": "Account_Count"})
    )
    save_summary_csv(account_status_summary, "account_status_summary.csv")

    requests_by_type = (
        service.groupby("Request_Type", as_index=False)["Service_ID"].count().rename(columns={"Service_ID": "Request_Count"})
    )
    save_summary_csv(requests_by_type, "service_requests_by_type.csv")

    fig, ax = plt.subplots(figsize=(9, 5))
    channel_summary.plot(kind="bar", x="Channel", y="Total_Usage_Count_30D", ax=ax, color="steelblue")
    ax.set_title("Banking Channel Usage (30 Days)")
    ax.set_xlabel("Channel")
    ax.set_ylabel("Usage Count")
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    plt.tight_layout()
    fig.savefig(OUT / "channel_usage.png", dpi=150)
    plt.close(fig)

    age_channel = channels.merge(customers[["Customer_ID", "Age_Band"]], on="Customer_ID", how="left")
    age_channel_summary = age_channel.groupby(["Age_Band", "Channel"], as_index=False)["Usage_Count_30D"].sum()
    fig, ax = plt.subplots(figsize=(10, 6))
    pivot = age_channel_summary.pivot(index="Age_Band", columns="Channel", values="Usage_Count_30D").fillna(0)
    pivot.plot(kind="bar", ax=ax)
    ax.set_title("Channel Usage by Age Band")
    ax.set_xlabel("Age Band")
    ax.set_ylabel("Usage Count")
    ax.legend(title="Channel")
    plt.tight_layout()
    fig.savefig(OUT / "channel_usage_by_age_band.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 6))
    status_pivot = account_status_summary.pivot(index="Account_Type", columns="Status", values="Account_Count").fillna(0)
    status_pivot.plot(kind="bar", ax=ax)
    ax.set_title("Account Type vs Status")
    ax.set_xlabel("Account Type")
    ax.set_ylabel("Account Count")
    ax.legend(title="Status")
    plt.tight_layout()
    fig.savefig(OUT / "account_status_by_type.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 5))
    complaint_summary.sort_values("Complaint_Rate", ascending=False).plot(
        x="Region", y="Complaint_Rate", kind="bar", ax=ax, color="darkorange"
    )
    ax.set_title("Complaint Rate by Region")
    ax.set_xlabel("Region")
    ax.set_ylabel("Complaint Rate")
    plt.tight_layout()
    fig.savefig(OUT / "complaint_rate_by_region.png", dpi=150)
    plt.close(fig)

    balance_segment = accounts.merge(customers[["Customer_ID", "Customer_Segment"]], on="Customer_ID", how="left")
    fig, ax = plt.subplots(figsize=(9, 5))
    balance_segment.boxplot(column="Balance", by="Customer_Segment", ax=ax)
    ax.set_title("Balance Distribution by Customer Segment")
    ax.set_xlabel("Customer Segment")
    ax.set_ylabel("Balance")
    plt.tight_layout()
    fig.savefig(OUT / "balance_by_segment.png", dpi=150)
    plt.close(fig)


def main() -> None:
    files = ["customers", "accounts", "transactions", "channels", "service"]
    raw = {name: pd.read_csv(DATA / f"{name}.csv") for name in files}

    print("=== DATASET OVERVIEW ===")
    for name, df in raw.items():
        print(f"\n{name}.csv | rows={len(df)} | columns={len(df.columns)}")
        print(df.head(3).to_string(index=False))
        print("Missing values:\n", df.isna().sum())
        print("Exact duplicate rows:", int(df.duplicated().sum()))

    customers = clean_customers(raw["customers"])
    accounts = clean_accounts(raw["accounts"])
    transactions = clean_transactions(raw["transactions"])
    channels = clean_channels(raw["channels"])
    service = clean_service(raw["service"])

    print("\n=== CLEANING NOTES ===")
    print("- Negative relationship years were invalid and set to the median value to retain rows.")
    print("- Missing channel values were filled with 'Unknown'.")
    print("- Negative usage counts and resolution days were set to median values to keep otherwise valid records.")
    print("- Exact duplicate transaction rows and duplicate Transaction_ID rows were removed.")
    print("- Extreme transaction amounts were retained but clipped using the IQR rule to reduce skew without deleting genuine large transfers.")

    cleaned = {
        "customers_cleaned": customers,
        "accounts_cleaned": accounts,
        "transactions_cleaned": transactions,
        "channels_cleaned": channels,
        "service_cleaned": service,
    }
    for name, df in cleaned.items():
        save_summary_csv(df, f"{name}.csv")

    build_analytics(customers, accounts, transactions, channels, service)

    print(f"\nFinished. Cleaned files and analysis outputs saved in: {OUT}")


if __name__ == "__main__":
    main()
