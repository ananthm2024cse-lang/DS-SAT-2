# CH08 – Bank Customer Insight (Synthetic Practice Project)

## Case study
TrustWave Bank wants to understand customer engagement using account, transaction, channel and service-interaction data.

**Important:** These are synthetic, generated practice records, not real bank/customer data and not official assessment results. Your findings must be calculated from the cleaned files.

## Files
- `data/customers.csv` — customer profile, age band, region, relationship length and segment
- `data/accounts.csv` — customer accounts, type, balance, balance band and status
- `data/transactions.csv` — transaction date, type, amount, channel and IDs
- `data/channels.csv` — customer/channel usage counts over 30 days
- `data/service.csv` — service requests, complaint flag, resolution and service channel

## Intentionally included data quality issues
- Missing channel values in `channels.csv` and `transactions.csv`
- Duplicate transaction rows in `transactions.csv`
- Inconsistent account-type labels in `accounts.csv`
- Extreme transaction amounts and one negative transaction amount
- Incomplete complaint records in `service.csv`
- A few additional invalid values (negative relationship years / channel usage / resolution days)

Do not silently delete all unusual values. Inspect them, document the chosen treatment, and compare results before/after cleaning where appropriate.

## Round 2 – EDA and Feature Engineering (Python)
Suggested workflow:
1. Load all CSVs with pandas; inspect `.shape`, `.head()`, `.info()`, `.isna().sum()`, and duplicate counts.
2. Standardize account labels (e.g. `saving`, `SAVINGS` → `Savings`; `Current Account` → `Current`; `fixed deposit` → `Fixed Deposit`).
3. Investigate duplicate transactions using `Transaction_ID` and duplicate rows. Remove true duplicates; do not drop transactions solely because values are large.
4. Treat missing categorical values as `Unknown` or leave them missing if the analysis requires it. Impute numeric values only with a documented rule.
5. Validate negative values and investigate extreme transaction amounts using IQR/percentiles and domain reasoning.
6. Join tables using `Customer_ID`; keep the analysis grain clear to avoid double-counting after one-to-many joins.
7. Create features such as `Total_Transactions`, `Total_Transaction_Amount`, `Channel_Usage_Total`, `Digital_Usage_Share`, `Complaint_Count`, `Service_Request_Count`, `Avg_Resolution_Days`, and `Account_Count`.
8. Analyse: most-used channels; channel usage by age band; account activity/status; complaints by region; balances by segment; repeated service request types.
9. Encode categorical variables if preparing a model. Feature selection is optional if you explain why it is appropriate.
10. Save cleaned outputs and charts to an `outputs/` folder.

### Suggested charts
- Bar chart: total usage by channel
- Grouped bar chart: channel usage by age band
- Bar chart: account type vs active/inactive/dormant counts
- Bar chart: complaint count/rate by region
- Box plot or histogram: balance by customer segment
- Line chart: monthly transaction count or amount
- Bar chart: service requests by request type and resolution status

### Optional intelligence layer / prototype
This case study does not specify a required ML algorithm or target variable. For a simple prototype, create a transparent engagement summary using engineered features, or optionally define a clearly documented target such as `Low_Engagement` based on a rule (for example, low recent channel usage). If you choose a predictive model, explain the target definition, avoid leakage, and report actual evaluation metrics from a held-out test set. Do not invent model scores.

## Round 3 – Excel analysis
1. Import cleaned tables or summarized tables into Excel.
2. Use PivotTables/PivotCharts for channel usage, customer segment comparisons, account activity, complaints, balances and service trends.
3. Useful formulas: `COUNTIF`, `COUNTIFS`, `SUMIF`, `SUMIFS`, `AVERAGEIF`, `IF`, `XLOOKUP` (or `VLOOKUP`).
4. Create a `Summary` worksheet with headline KPIs and charts. Clearly label all measures and filters.

## Round 4 – Business pitch
Use two evidence-backed findings from your own analysis. Recommendations to consider only if supported by your results:
- Offer digital-banking guidance to age/region segments with lower digital usage.
- Investigate regions or request types with higher complaint rates or longer resolution times.
- Review inactive/dormant accounts and develop segment-specific re-engagement campaigns.
- Improve repeated service request journeys (e.g. password reset or digital help) if they have high volume.

## Folder structure
- `data/` — five raw synthetic CSVs
- `starter/round2_eda_starter.py` — beginner-friendly Python starter
- `templates/round4_pitch_template.md` — short pitch structure
- `templates/round3_excel_checklist.md` — Excel checklist
- `outputs/` — place your cleaned datasets, charts and summary tables here
