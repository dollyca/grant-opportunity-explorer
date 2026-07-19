import re
import streamlit as st
import pandas as pd
from datetime import date, datetime
from PIL import Image

logo = Image.open("medica_logo.png")
st.set_page_config(
    page_title="Grant Opportunity Explorer",
    page_icon=logo,
    layout="wide",
)


# --------------------------------------------------
# Data cleaning functions
# --------------------------------------------------

def clean_text_column(series):
    """
    Remove extra spaces while preserving missing values.

    Examples:
    "  Federal Grant  " -> "Federal Grant"
    "Mental   Health"   -> "Mental Health"
    """
    return (
        series.astype("string")
        .str.strip()
        .str.replace(r"\s+", " ", regex=True)
        .replace("", pd.NA)
    )


def clean_funding_type(df):
    """
    Standardize common Funding Type variations.

    Add more mappings later only when actual duplicate
    categories appear in the Excel file.
    """
    if "Funding Type" not in df.columns:
        return df

    df["Funding Type"] = clean_text_column(df["Funding Type"])

    mapping = {
        "federal": "Federal",
        "federal grant": "Federal",
        "federal funding": "Federal",
        "government": "Government",
        "government grant": "Government",
        "state": "State",
        "state grant": "State",
        "local": "Local",
        "local grant": "Local",
        "foundation": "Foundation",
        "foundation grant": "Foundation",
        "corporate": "Corporate",
        "corporate grant": "Corporate",
        "private": "Private",
        "private grant": "Private",
        "nonprofit": "Nonprofit",
    }

    normalized = df["Funding Type"].str.lower()

    df["Funding Type"] = normalized.map(mapping).fillna(
        df["Funding Type"]
    )

    return df


def clean_focus_area(df):
    """
    Clean spacing and standardize a few obvious Focus Area variations.
    """
    if "Focus Area" not in df.columns:
        return df

    df["Focus Area"] = clean_text_column(df["Focus Area"])

    mapping = {
        "mental health": "Mental Health",
        "behavioral health": "Behavioral Health",
        "behavioural health": "Behavioral Health",
        "health care": "Healthcare",
        "healthcare": "Healthcare",
        "public health": "Public Health",
        "community health": "Community Health",
        "workforce development": "Workforce Development",
        "economic development": "Economic Development",
        "education": "Education",
        "housing": "Housing",
        "homelessness": "Homelessness",
        "food insecurity": "Food Insecurity",
        "social services": "Social Services",
    }

    normalized = df["Focus Area"].str.lower()

    df["Focus Area"] = normalized.map(mapping).fillna(
        df["Focus Area"]
    )

    return df


def clean_geographic_scope(df):
    """
    Standardize common geographic abbreviations and variations.
    """
    if "Geographic Scope" not in df.columns:
        return df

    df["Geographic Scope"] = clean_text_column(
        df["Geographic Scope"]
    )

    mapping = {
        "ca": "California",
        "calif": "California",
        "calif.": "California",
        "california": "California",
        "us": "National",
        "u.s.": "National",
        "usa": "National",
        "u.s.a.": "National",
        "united states": "National",
        "nationwide": "National",
        "national": "National",
        "orange county": "Orange County",
        "orange county, ca": "Orange County",
        "southern california": "Southern California",
        "southern ca": "Southern California",
        "regional": "Regional",
        "local": "Local",
    }

    normalized = df["Geographic Scope"].str.lower()

    df["Geographic Scope"] = normalized.map(mapping).fillna(
        df["Geographic Scope"]
    )

    return df


def clean_website(df):
    """
    Clean website links and add https:// when the protocol is missing.
    """
    if "Website Link" not in df.columns:
        return df

    def fix_url(value):
        if pd.isna(value):
            return pd.NA

        url = str(value).strip()

        if not url:
            return pd.NA

        if url.lower() in {
            "n/a",
            "na",
            "none",
            "not available",
            "unknown",
        }:
            return pd.NA

        if not url.lower().startswith(
            ("http://", "https://")
        ):
            url = "https://" + url

        return url

    df["Website Link"] = df["Website Link"].apply(fix_url)

    return df


def clean_general_text_columns(df):
    """
    Clean extra spaces in the remaining text columns.
    """
    text_columns = [
        "Funder Name",
        "Program Name",
        "Grant Size",
        "Eligibility",
        "Notes (Fit with Medica Zone's Mission)",
    ]

    for column in text_columns:
        if column in df.columns:
            df[column] = clean_text_column(df[column])

    return df


def clean_deadline(df):
    """
    Preserve text deadlines such as Rolling, September, and application
    instructions. Parse only genuine full calendar dates.
    """
    if "Deadline" not in df.columns:
        df["Deadline Raw"] = pd.NA
        df["Deadline Parsed"] = pd.NaT
        df["Deadline Display"] = ""
        df["Days Until Deadline"] = pd.NA
        df["Deadline Status"] = "Missing deadline"
        return df

    df["Deadline Raw"] = df["Deadline"].copy()

    month_names = {
        1: "January",
        2: "February",
        3: "March",
        4: "April",
        5: "May",
        6: "June",
        7: "July",
        8: "August",
        9: "September",
        10: "October",
        11: "November",
        12: "December",
    }

    def parse_deadline(value):
        if pd.isna(value):
            return pd.NaT

        # Excel may store a month-only value as a date in year 0001.
        if isinstance(value, (pd.Timestamp, datetime)):
            if value.year < 1900:
                return pd.NaT
            return pd.Timestamp(value)

        # Handle genuine Excel serial dates.
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            if 20000 <= value <= 80000:
                return (
                    pd.Timestamp("1899-12-30")
                    + pd.to_timedelta(value, unit="D")
                )

            return pd.NaT

        text = str(value).strip()

        if not text:
            return pd.NaT

        lowered = text.lower()

        if lowered in {
            "nan",
            "nat",
            "none",
            "n/a",
            "na",
            "unknown",
            "rolling",
            "ongoing",
            "annual",
            "annually",
            "monthly",
            "quarterly",
            "open",
            "january",
            "february",
            "march",
            "april",
            "may",
            "june",
            "july",
            "august",
            "september",
            "october",
            "november",
            "december",
        }:
            return pd.NaT

        # Do not parse text unless it contains a real four-digit year.
        if not pd.Series([text]).str.contains(
            r"\b(?:19|20)\d{2}\b",
            regex=True,
        ).iloc[0]:
            return pd.NaT

        parsed = pd.to_datetime(text, errors="coerce")

        if pd.notna(parsed) and parsed.year >= 1900:
            return parsed

        return pd.NaT

    def display_deadline(value, parsed_value):
        if pd.notna(parsed_value):
            return parsed_value.strftime("%m/%d/%Y")

        if pd.isna(value):
            return ""

        # Convert fake year-0001 dates back into month names.
        if isinstance(value, (pd.Timestamp, datetime)):
            if value.year < 1900:
                return month_names.get(value.month, "")

        text = str(value).strip()

        # Also handle cases converted into text before reaching this function.
        fake_date_match = re.fullmatch(
            r"0*1-(\d{1,2})-\d{1,2}(?:\s+00:00:00)?",
            text,
        )

        if fake_date_match:
            month_number = int(fake_date_match.group(1))
            return month_names.get(month_number, text)

        if text.lower() in {
            "",
            "nan",
            "nat",
            "none",
            "n/a",
            "na",
        }:
            return ""

        return text

    df["Deadline Parsed"] = df["Deadline Raw"].apply(
        parse_deadline
    )

    df["Deadline Display"] = df.apply(
        lambda row: display_deadline(
            row["Deadline Raw"],
            row["Deadline Parsed"],
        ),
        axis=1,
    )

    today = pd.Timestamp(date.today())

    df["Days Until Deadline"] = (
        df["Deadline Parsed"].dt.normalize() - today
    ).dt.days

    def classify_deadline(row):
        days = row["Days Until Deadline"]
        display = row["Deadline Display"]

        if not display:
            return "Missing deadline"

        if pd.isna(days):
            return "No fixed date"

        if days < 0:
            return "Past deadline"

        if days <= 7:
            return "Due within 7 days"

        if days <= 30:
            return "Due within 30 days"

        if days <= 90:
            return "Due within 90 days"

        return "More than 90 days"

    df["Deadline Status"] = df.apply(
        classify_deadline,
        axis=1,
    )

    return df


def clean_data(df):
    """
    Run all lightweight cleaning steps.
    """
    df = df.copy()

    df = clean_general_text_columns(df)
    df = clean_funding_type(df)
    df = clean_focus_area(df)
    df = clean_geographic_scope(df)
    df = clean_website(df)
    df = clean_deadline(df)

    return df


# --------------------------------------------------
# Load data
# --------------------------------------------------

@st.cache_data
def load_data():
    df = pd.read_excel(
        "data/Grant Database - Backup.xlsx"
    )

    # Remove spaces from Excel column names.
    df.columns = df.columns.str.strip()

    # Remove completely empty rows.
    df = df.dropna(
        how="all"
    ).reset_index(drop=True)

    # Run data cleaning.
    df = clean_data(df)

    # Columns used to determine whether a record is incomplete.
    original_columns = [
        "Funder Name",
        "Program Name",
        "Website Link",
        "Funding Type",
        "Focus Area",
        "Grant Size",
        "Eligibility",
        "Deadline",
        "Geographic Scope",
        "Notes (Fit with Medica Zone's Mission)",
    ]

    # Only use columns that actually exist in the spreadsheet.
    available_original_columns = [
        column
        for column in original_columns
        if column in df.columns
    ]

    if available_original_columns:
        df["Has Missing Information"] = (
            df[available_original_columns]
            .replace(r"^\s*$", pd.NA, regex=True)
            .isna()
            .any(axis=1)
        )
    else:
        df["Has Missing Information"] = False

    return df

st.cache_data.clear()
df = load_data()


# --------------------------------------------------
# Title
# --------------------------------------------------

st.title("Grant Opportunity Explorer")

st.caption(
    "Explore, filter, and analyze grant opportunities researched "
    "by the Budgeting & Finance team."
)


# --------------------------------------------------
# KPI calculations
# --------------------------------------------------

total_grants = len(df)

incomplete_grants = int(
    df["Has Missing Information"].sum()
)


# --------------------------------------------------
# KPI cards
# --------------------------------------------------

k1, k2, k3, k4 = st.columns(4)

k1.metric(
    "Total Grants",
    total_grants,
)

k2.metric(
    "Funding Types",
    df["Funding Type"].nunique(dropna=True)
    if "Funding Type" in df.columns
    else 0,
)

k3.metric(
    "Focus Areas",
    df["Focus Area"].nunique(dropna=True)
    if "Focus Area" in df.columns
    else 0,
)

k4.metric(
    "Records with Missing Fields",
    incomplete_grants,
    help=(
        "Number of grant records with at least one blank field. "
        "This is a data-quality count, not a completion rate."
    ),
)

st.divider()


# --------------------------------------------------
# Filters
# --------------------------------------------------

st.subheader("Explore Grants")


funding_options = []

if "Funding Type" in df.columns:
    funding_options = sorted(
        df["Funding Type"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )


focus_options = []

if "Focus Area" in df.columns:
    focus_options = sorted(
        df["Focus Area"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )


deadline_options = [
    "Due within 7 days",
    "Due within 30 days",
    "Due within 90 days",
    "More than 90 days",
    "No fixed date",
    "Missing deadline",
    "Past deadline",
]


f1, f2, f3 = st.columns(3)


selected_funding = f1.multiselect(
    "Funding Type",
    options=funding_options,
)


selected_focus = f2.multiselect(
    "Focus Area",
    options=focus_options,
)


selected_deadline_status = f3.multiselect(
    "Deadline Status",
    options=deadline_options,
)


show_missing = st.checkbox(
    "Show only grants with missing information"
)


search_term = st.text_input(
    "Search grants",
    placeholder=(
        "Search funder, program, focus area, eligibility, "
        "geographic scope, grant size, or notes..."
    ),
)


# --------------------------------------------------
# Apply filters
# --------------------------------------------------

filtered_df = df.copy()


if selected_funding and "Funding Type" in filtered_df.columns:
    filtered_df = filtered_df[
        filtered_df["Funding Type"].isin(
            selected_funding
        )
    ]


if selected_focus and "Focus Area" in filtered_df.columns:
    filtered_df = filtered_df[
        filtered_df["Focus Area"].isin(
            selected_focus
        )
    ]


if (
    selected_deadline_status
    and "Deadline Status" in filtered_df.columns
):
    filtered_df = filtered_df[
        filtered_df["Deadline Status"].isin(
            selected_deadline_status
        )
    ]


if show_missing:
    filtered_df = filtered_df[
        filtered_df["Has Missing Information"]
    ]


if search_term:
    searchable_columns = [
        "Funder Name",
        "Program Name",
        "Funding Type",
        "Focus Area",
        "Grant Size",
        "Eligibility",
        "Deadline Display",
        "Geographic Scope",
        "Notes (Fit with Medica Zone's Mission)",
    ]

    searchable_columns = [
        column
        for column in searchable_columns
        if column in filtered_df.columns
    ]

    if searchable_columns:
        search_mask = (
            filtered_df[searchable_columns]
            .fillna("")
            .astype(str)
            .apply(
                lambda column: column.str.contains(
                    search_term,
                    case=False,
                    na=False,
                    regex=False,
                )
            )
            .any(axis=1)
        )

        filtered_df = filtered_df[search_mask]


st.write(
    f"Showing **{len(filtered_df)}** of "
    f"**{total_grants}** grants"
)


# --------------------------------------------------
# Grant table
# --------------------------------------------------

table_df = filtered_df.copy()


# Replace the mixed Excel deadline with safe display text.
table_df["Deadline"] = table_df["Deadline Display"]


columns_to_show = [
    "Funder Name",
    "Program Name",
    "Website Link",
    "Funding Type",
    "Focus Area",
    "Grant Size",
    "Eligibility",
    "Deadline",
    "Days Until Deadline",
    "Deadline Status",
    "Geographic Scope",
    "Notes (Fit with Medica Zone's Mission)",
]


# Only show columns that exist.
columns_to_show = [
    column
    for column in columns_to_show
    if column in table_df.columns
]


table_df = table_df[columns_to_show]


# Convert text columns safely without turning missing values into "nan".
text_columns = [
    column
    for column in table_df.columns
    if column != "Days Until Deadline"
]


table_df[text_columns] = (
    table_df[text_columns]
    .fillna("")
    .astype(str)
)


st.dataframe(
    table_df,
    width="stretch",
    hide_index=True,
    column_config={
        "Website Link": st.column_config.LinkColumn(
            "Website Link",
            display_text="Open grant page",
        ),
        "Days Until Deadline": st.column_config.NumberColumn(
            "Days Left",
            format="%d",
        ),
        "Notes (Fit with Medica Zone's Mission)": (
            st.column_config.TextColumn(
                "Mission Fit Notes",
                width="large",
            )
        ),
    },
)


# --------------------------------------------------
# Download filtered results
# --------------------------------------------------

download_df = table_df.copy()


csv_data = download_df.to_csv(
    index=False
).encode("utf-8-sig")


st.download_button(
    label="Download Filtered Results as CSV",
    data=csv_data,
    file_name="filtered_grant_opportunities.csv",
    mime="text/csv",
)


st.divider()


# --------------------------------------------------
# Charts
# --------------------------------------------------

st.subheader("Grant Portfolio Overview")


chart_left, chart_right = st.columns(2)


with chart_left:
    st.markdown("#### Grants by Funding Type")

    if "Funding Type" in filtered_df.columns:
        funding_chart = (
            filtered_df["Funding Type"]
            .fillna("Missing")
            .astype(str)
            .value_counts()
            .rename_axis("Funding Type")
            .reset_index(name="Number of Grants")
        )

        if funding_chart.empty:
            st.info(
                "No data available for the current filters."
            )
        else:
            st.bar_chart(
                funding_chart,
                x="Funding Type",
                y="Number of Grants",
                width="stretch",
            )
    else:
        st.info("Funding Type column is unavailable.")


with chart_right:
    st.markdown("#### Grants by Focus Area")

    if "Focus Area" in filtered_df.columns:
        focus_chart = (
            filtered_df["Focus Area"]
            .fillna("Missing")
            .astype(str)
            .value_counts()
            .rename_axis("Focus Area")
            .reset_index(name="Number of Grants")
        )

        if focus_chart.empty:
            st.info(
                "No data available for the current filters."
            )
        else:
            st.bar_chart(
                focus_chart,
                x="Focus Area",
                y="Number of Grants",
                horizontal=True,
                width="stretch",
            )
    else:
        st.info("Focus Area column is unavailable.")