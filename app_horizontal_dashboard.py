
import streamlit as st
import pandas as pd
import plotly.express as px

# Load data
df = pd.read_csv("dashboard_data.csv")
df = df.dropna(subset=["crude_mortality", "year", "country"])

if "incidence_per_100k" not in df.columns:
    if "suicides_no" in df.columns and "population" in df.columns:
        df["incidence_per_100k"] = (df["suicides_no"] / df["population"]) * 100000
    else:
        df["incidence_per_100k"] = None
    
# Page layout
st.set_page_config(layout="wide")
st.title("📊 Global Suicide Analytics Dashboard From 2000 till 2021")
st.markdown("**Powered by WHO & OWID | Designed for MSBA382 | By Lynn Shehab**")

# Sidebar Filters
st.sidebar.header("🔍 Filter")
year = st.sidebar.slider("Year", int(df["year"].min()), int(df["year"].max()), 2019)
country = st.sidebar.selectbox("Country", sorted(df["country"].dropna().unique()))

filtered_df = df[df["year"] == year]
country_df = df[df["country"] == country]

# === TOP METRICS (KPI cards in a row) ===
latest = country_df[country_df["year"] == year]

st.markdown("### 🔢 Key Indicators")
col1, col2 = st.columns(2)

with col1:
    st.metric(
        "Crude Mortality Rate",
        f"{latest['crude_mortality'].values[0]:.2f} per 100k" if not latest.empty else "N/A",
        help="Total suicide deaths per 100,000 people — includes all age groups and genders."
    )

with col2:
    if "male_to_female_suicide_death_rate_ratio_age_standardized" in latest.columns:
        st.metric(
            "Male-to-Female Ratio",
            f"{latest['male_to_female_suicide_death_rate_ratio_age_standardized'].values[0]:.2f}" if not latest.empty else "N/A",
            help="Ratio of male to female suicide mortality - values above 1 mean male rates are higher."
        )

        
# === ROW 1: Trend by Year, Age Distribution, Gender Ratio ===
st.markdown("### 📈 Suicide Trends & Demographics")
col1, col2, col3 = st.columns(3)

# Line chart: trend over time
with col1:
    fig = px.line(country_df, x="year", y="crude_mortality", markers=True,
                  title=f"Crude Mortality Over Time — {country}")
    st.plotly_chart(fig, use_container_width=True)

# Bar chart: age distribution
with col2:
    age_cols = [c for c in df.columns if "aged_" in c and "both_sexes" in c]
    if age_cols and not latest.empty:
        age_data = latest[age_cols].T.dropna()
        age_data.columns = ["rate"]
        age_data.index = age_data.index.str.extract(r'aged_(\\d+_\\d+|\\d+\\+)_year_olds')[0]
        age_data.index = age_data.index.str.replace("_", "–")
        age_data.index.name = "Age Group"

        fig = px.bar(
            age_data,
            x=age_data.index,
            y="rate",
            title=f"Suicide Rate by Age Group in {country} ({year})",
            labels={"rate": "Deaths per 100k", "index": "Age Group"},
            text_auto=".2f"
        )
        st.plotly_chart(fig, use_container_width=True)

# Gender trend
with col3:
    if "male_to_female_suicide_death_rate_ratio_age_standardized" in country_df.columns:
        fig = px.line(country_df.dropna(subset=["male_to_female_suicide_death_rate_ratio_age_standardized"]),
                      x="year", y="male_to_female_suicide_death_rate_ratio_age_standardized",
                      title=f"M:F Suicide Ratio — {country}", markers=True)
        st.plotly_chart(fig, use_container_width=True)

# === ROW 2: Map, Top 10 Countries, Country Comparison ===
st.markdown("### 🌍 Regional Analysis & Rankings")
col4, col5, col6 = st.columns(3)

# Map: Global distribution
with col4:
    map_fig = px.choropleth(filtered_df,
                            locations="country",
                            locationmode="country names",
                            color="crude_mortality",
                            color_continuous_scale="Reds",
                            title=f"Suicide Rate Map — {year}")
    st.plotly_chart(map_fig, use_container_width=True)

# Bar: Top 10 countries
with col5:
    top10 = filtered_df.sort_values("crude_mortality", ascending=False).head(10)
    fig = px.bar(top10, x="country", y="crude_mortality", color="country",
                 title=f"Top 10 Countries — {year}", text_auto=".2s")
    st.plotly_chart(fig, use_container_width=True)

# Pie: Region/country share (Optional Placeholder)
with col6:
    region_data = top10.groupby("country")["crude_mortality"].mean().reset_index()
    fig = px.pie(region_data, names="country", values="crude_mortality", title="Top 10 Country Share")
    st.plotly_chart(fig, use_container_width=True)
