import streamlit as st
import pandas as pd
import plotly.express as px

# Load data
df = pd.read_csv("dashboard_data.csv")
df = df.dropna(subset=["crude_mortality", "year", "country"])

# Page layout
st.set_page_config(layout="wide")
st.title("\U0001F4CA Global Suicide Analytics Dashboard From 2000 till 2021")
st.markdown("**Powered by WHO & OWID | Designed for MSBA382 | By Lynn Shehab**")
st.markdown("---")

# Sidebar Filters
st.sidebar.header("\U0001F50D Filter")
year = st.sidebar.slider("Year", int(df["year"].min()), int(df["year"].max()), 2019)
country = st.sidebar.selectbox("Country", sorted(df["country"].dropna().unique()))
country_df = df[df["country"] == country]
filtered_df = df[df["year"] == year]
latest = country_df[country_df["year"] == year]
previous = country_df[country_df["year"] == year - 1]

# === TOP METRICS ===
st.markdown("### \U0001F522 Key Indicators")
col1, col3 = st.columns(2)

with col1:
    delta = (latest['crude_mortality'].values[0] - previous['crude_mortality'].values[0]) if not previous.empty else None
    st.metric(
        "Crude Mortality Rate",
        f"{latest['crude_mortality'].values[0]:.2f} per 100k" if not latest.empty else "N/A",
        f"{delta:+.2f}" if delta else "N/A",
        help="Total suicide deaths per 100,000 people — includes all age groups and genders."
    )


with col3:
    if "male_to_female_suicide_death_rate_ratio_age_standardized" in latest.columns:
        st.metric(
            "Male-to-Female Ratio",
            f"{latest['male_to_female_suicide_death_rate_ratio_age_standardized'].values[0]:.2f}" if not latest.empty else "N/A",
            help="Ratio of male to female suicide mortality - values above 1 mean male rates are higher."
        )

st.markdown("---")

# === TRENDS & DEMOGRAPHICS ===
st.markdown("### \U0001F4C8 Suicide Trends & Demographics")
col1, col2, col3 = st.columns(3)

with col1:
    fig = px.line(country_df, x="year", y="crude_mortality", markers=True,
                  title=f"Crude Mortality Over Time — {country}",
                  color_discrete_sequence=["#1f77b4"])
    fig.update_layout(template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Crude mortality includes all age groups and genders.")

with col2:
    age_cols = [c for c in df.columns if "aged_" in c and "both_sexes" in c]
    if age_cols and not latest.empty:
        age_data = latest[age_cols].T.dropna()
        age_data.columns = ["rate"]
        age_data = age_data.sort_values("rate")
        age_labels = []
        for col in age_data.index:
            if "aged_" in col and "_year_olds" in col:
                label = col.split("aged_")[1].split("_year_olds")[0]
                label = label.replace("_", "–")
                age_labels.append(label)
            else:
                age_labels.append(col)
        age_data.index = age_labels
        age_data.index.name = "Age Group"
        fig = px.bar(
            age_data,
            x=age_data.index,
            y="rate",
            title=f"Suicide Rate by Age Group — {country} ({year})",
            labels={"rate": "Deaths per 100k", "index": "Age Group"},
            text_auto=".2f",
            color_discrete_sequence=["#2ca02c"]
        )
        fig.update_layout(template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Note: Only includes both sexes.")

with col3:
    if "male_to_female_suicide_death_rate_ratio_age_standardized" in country_df.columns:
        fig = px.line(
            country_df.dropna(subset=["male_to_female_suicide_death_rate_ratio_age_standardized"]),
            x="year", y="male_to_female_suicide_death_rate_ratio_age_standardized",
            title=f"M:F Suicide Ratio — {country}", markers=True,
            color_discrete_sequence=["#ff7f0e"])
        fig.update_layout(template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# === REGIONAL ANALYSIS ===
st.markdown("### 🌍 Regional Analysis & Rankings")
col4, col5, col6 = st.columns(3)

with col4:
    map_fig = px.choropleth(filtered_df,
                            locations="country",
                            locationmode="country names",
                            color="crude_mortality",
                            color_continuous_scale="Tealgrn",
                            title=f"Suicide Rate Map — {year}")
    map_fig.update_layout(template="plotly_white")
    st.plotly_chart(map_fig, use_container_width=True)

with col5:
    top10 = filtered_df.sort_values("crude_mortality", ascending=False).head(10)
    fig = px.bar(top10, x="country", y="crude_mortality", color="country",
                 title=f"Top 10 Countries — {year}", text_auto=".2s",
                 color_discrete_sequence=px.colors.qualitative.Set3)
    fig.update_layout(showlegend=False, template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)

with col6:
    region_data = top10.groupby("country")["crude_mortality"].mean().reset_index()
    fig = px.pie(region_data, names="country", values="crude_mortality",
                 title=f"Top 10 Country Share — {year}",
                 color_discrete_sequence=px.colors.qualitative.Pastel)
    fig.update_traces(textinfo="percent+label")
    fig.update_layout(template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.download_button("⬇️ Download Filtered Data", filtered_df.to_csv(index=False), "filtered_data.csv")
st.markdown("© 2025 Lynn Shehab | MSBA Capstone Project | AUB")
