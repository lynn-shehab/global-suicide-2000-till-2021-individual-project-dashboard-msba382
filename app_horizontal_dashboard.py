import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Load data 
@st.cache_data
def load_data():
    df = pd.read_csv("dashboard_data.csv")
    df = df.dropna(subset=["crude_mortality", "year", "country"]) # Ensure primary cols are not NaN
    # Clean up column names for easier access, especially for gender-specific rates
    df.rename(columns={
        "age_standardized_death_rate_from_self_inflicted_injuries_per_100,000_population___sex:_males___age_group:_all_ages": "male_suicide_rate_age_standardized",
        "age_standardized_death_rate_from_self_inflicted_injuries_per_100,000_population___sex:_females___age_group:_all_ages": "female_suicide_rate_age_standardized"
    }, inplace=True)
    return df

df = load_data()

# --- COLOR DYNAMICS SETUP ---
min_mortality = df['crude_mortality'].min()
max_mortality = df['crude_mortality'].max()

BLUE_COLOR_SCALE = [
    [0.0, "#E0F2F7"],  # Very Light Blue
    [0.2, "#B3E0F2"],
    [0.4, "#80CCEB"],
    [0.6, "#4DB8E0"],
    [0.8, "#1F77B4"],
    [1.0, "#0A3B57"]
]

def get_dynamic_color(value, min_val, max_val, color_scale):
    if pd.isna(value) or (max_val - min_val) == 0:
        return color_scale[len(color_scale)//2][1] if color_scale else "#1F77B4"

    normalized_value = (value - min_val) / (max_val - min_val)
    normalized_value = max(0.0, min(1.0, normalized_value))

    for i in range(len(color_scale) - 1):
        if normalized_value >= color_scale[i][0] and normalized_value <= color_scale[i+1][0]:
            lower_bound_val, lower_bound_color = color_scale[i]
            upper_bound_val, upper_bound_color = color_scale[i+1]

            def hex_to_rgb(hex_color):
                hex_color = hex_color.lstrip('#')
                return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

            def rgb_to_hex(rgb_color):
                return '#%02x%02x%02x' % rgb_color

            rgb1 = hex_to_rgb(lower_bound_color)
            rgb2 = hex_to_rgb(upper_bound_color)

            if (upper_bound_val - lower_bound_val) == 0:
                t = 0
            else:
                t = (normalized_value - lower_bound_val) / (upper_bound_val - lower_bound_val)

            interpolated_rgb = tuple(int(rgb1[j] + t * (rgb2[j] - rgb1[j])) for j in range(3))
            return rgb_to_hex(interpolated_rgb)
    return color_scale[-1][1]

# Page layout
st.set_page_config(layout="wide")
st.title("\U0001F4CA Global Suicide Analytics Dashboard From 2000 till 2021")
st.markdown("**Powered by WHO & OWID | Designed for MSBA382 | By Lynn Shehab**")
st.markdown("---")

# Sidebar Filters
st.sidebar.header("\U0001F50D Filter")

selected_year = st.sidebar.slider("Year", int(df["year"].min()), int(df["year"].max()), 2019)
df_by_year = df[df["year"] == selected_year]

available_countries = sorted(df_by_year["country"].dropna().unique())
if not available_countries:
    st.error(f"No data available for the year {selected_year}. Please choose a different year.")
    st.stop()
selected_country = st.sidebar.selectbox("Country", available_countries)

# Filter data for selected country and year for current metrics/charts
latest = df[(df["country"] == selected_country) & (df["year"] == selected_year)]
previous = df[(df["country"] == selected_country) & (df["year"] == selected_year - 1)]

# Data for country-specific time trends
country_trend_df = df[df["country"] == selected_country].dropna(subset=["crude_mortality", "population"])

# Data for year-specific, all-country charts
filtered_data_for_year = df[df["year"] == selected_year]
# Ensure population is not NaN for total suicides calculation
filtered_data_for_year = filtered_data_for_year.dropna(subset=["population"])
# Calculate estimated total suicides for the filtered_data_for_year
if not filtered_data_for_year.empty:
    filtered_data_for_year['estimated_total_suicides'] = (filtered_data_for_year['crude_mortality'] * filtered_data_for_year['population'] / 100000).astype(int)

# Determine the main line color based on the current crude mortality
current_crude_mortality = latest['crude_mortality'].values[0] if not latest.empty and 'crude_mortality' in latest.columns else (min_mortality + max_mortality) / 2
main_line_color = get_dynamic_color(current_crude_mortality, min_mortality, max_mortality, BLUE_COLOR_SCALE)


# === TOP METRICS ===
st.markdown("### \U0001F522 Key Indicators")
col1, col2, col3 = st.columns(3) # Added more columns for new metrics

with col1:
    crude_mortality_delta = (latest['crude_mortality'].values[0] - previous['crude_mortality'].values[0]) if not previous.empty and not latest.empty and 'crude_mortality' in previous.columns and 'crude_mortality' in latest.columns else None
    st.metric(
        "Crude Mortality Rate",
        f"{latest['crude_mortality'].values[0]:.2f} per 100k" if not latest.empty and 'crude_mortality' in latest.columns else "N/A",
        f"{crude_mortality_delta:+.2f}" if crude_mortality_delta is not None else "N/A",
        help="Total suicide deaths per 100,000 people — includes all age groups and genders."
    )

with col2:
    if "male_to_female_suicide_death_rate_ratio_age_standardized" in latest.columns:
        current_m_f_ratio = latest['male_to_female_suicide_death_rate_ratio_age_standardized'].values[0] if not latest.empty else None
        previous_m_f_ratio = previous['male_to_female_suicide_death_rate_ratio_age_standardized'].values[0] if not previous.empty else None

        m_f_ratio_delta = None
        if current_m_f_ratio is not None and previous_m_f_ratio is not None:
            m_f_ratio_delta = current_m_f_ratio - previous_m_f_ratio

        st.metric(
            "Male-to-Female Ratio",
            f"{current_m_f_ratio:.2f}" if current_m_f_ratio is not None else "N/A",
            f"{m_f_ratio_delta:+.2f}" if m_f_ratio_delta is not None else "N/A",
            help="Ratio of male to female suicide mortality - values above 1 mean male rates are higher."
        )
    else:
        st.metric("Male-to-Female Ratio", "N/A", "N/A", help="Ratio of male to female suicide mortality - values above 1 mean male rates are higher.")

with col3:
    current_total_suicides = None
    if not latest.empty and 'crude_mortality' in latest.columns and 'population' in latest.columns and pd.notna(latest['crude_mortality'].values[0]) and pd.notna(latest['population'].values[0]):
        current_total_suicides = int(latest['crude_mortality'].values[0] * latest['population'].values[0] / 100000)

    previous_total_suicides = None
    if not previous.empty and 'crude_mortality' in previous.columns and 'population' in previous.columns and pd.notna(previous['crude_mortality'].values[0]) and pd.notna(previous['population'].values[0]):
        previous_total_suicides = int(previous['crude_mortality'].values[0] * previous['population'].values[0] / 100000)

    total_suicides_delta = None
    if current_total_suicides is not None and previous_total_suicides is not None:
        total_suicides_delta = current_total_suicides - previous_total_suicides

    st.metric(
        "Estimated Total Suicides",
        f"{current_total_suicides:,}" if current_total_suicides is not None else "N/A",
        f"{total_suicides_delta:+,}" if total_suicides_delta is not None else "N/A",
        help="Estimated total number of suicide deaths (Crude Mortality * Population / 100,000)."
    )

st.markdown("---")

# === TRENDS & DEMOGRAPHICS ===
st.markdown("### \U0001F4C8 Suicide Trends & Demographics")
col1, col2, col3 = st.columns(3)

with col1:
    fig = px.line(country_trend_df, x="year", y="crude_mortality", markers=True,
                  title=f"Crude Mortality Over Time — {selected_country}")
    fig.update_traces(line=dict(color=main_line_color))
    fig.update_layout(template="plotly_dark")
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

        if not age_data.empty and age_data['rate'].max() - age_data['rate'].min() != 0:
            bar_colors_age = [get_dynamic_color(rate, age_data['rate'].min(), age_data['rate'].max(), BLUE_COLOR_SCALE) for rate in age_data['rate']]
        else:
            bar_colors_age = [BLUE_COLOR_SCALE[len(BLUE_COLOR_SCALE)//2][1]] * len(age_data) if not age_data.empty else []


        fig = px.bar(
            age_data,
            x=age_data.index,
            y="rate",
            title=f"Suicide Rate by Age Group — {selected_country} ({selected_year})",
            labels={"rate": "Deaths per 100k", "index": "Age Group"},
            text_auto=".2f"
        )
        fig.update_traces(marker_color=bar_colors_age)
        fig.update_layout(template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Note: Only includes both sexes.")
    else:
        st.info(f"No age-group data available for {selected_country} in {selected_year}.")


with col3:
    if "male_to_female_suicide_death_rate_ratio_age_standardized" in country_df.columns:
        fig = px.line(country_df.dropna(subset=["male_to_female_suicide_death_rate_ratio_age_standardized"]),
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
    map_fig = px.choropleth(filtered_data_for_year,
                            locations="country",
                            locationmode="country names",
                            color="crude_mortality",
                            color_continuous_scale="Blues",
                            title=f"Suicide Rate Map — {selected_year}")
    map_fig.update_layout(template="plotly_dark")
    st.plotly_chart(map_fig, use_container_width=True)

with col5:
    top10 = filtered_data_for_year.sort_values("crude_mortality", ascending=False).head(10)
    if not top10.empty:
        if top10['crude_mortality'].max() - top10['crude_mortality'].min() != 0:
            bar_colors_top10 = [get_dynamic_color(val, top10['crude_mortality'].min(), top10['crude_mortality'].max(), BLUE_COLOR_SCALE) for val in top10["crude_mortality"]]
        else:
            bar_colors_top10 = [BLUE_COLOR_SCALE[len(BLUE_COLOR_SCALE)//2][1]] * len(top10)


        fig = px.bar(top10, x="country", y="crude_mortality",
                    title=f"Top 10 Countries (by Crude Mortality) — {selected_year}", text_auto=".2s")
        fig.update_traces(marker_color=bar_colors_top10)
        fig.update_layout(showlegend=False, template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info(f"No top 10 country data available for {selected_year}.")


with col6:
    if not top10.empty:
        region_data = top10.groupby("country")["crude_mortality"].mean().reset_index()
        if not region_data.empty and region_data["crude_mortality"].max() - region_data["crude_mortality"].min() != 0:
            pie_colors = [get_dynamic_color(val, region_data["crude_mortality"].min(), region_data["crude_mortality"].max(), BLUE_COLOR_SCALE) for val in region_data["crude_mortality"]]
        else:
            pie_colors = [BLUE_COLOR_SCALE[len(BLUE_COLOR_SCALE)//2][1]] * len(region_data) if not region_data.empty else []


        fig = px.pie(region_data, names="country", values="crude_mortality",
                    title=f"Top 10 Country Share (by Crude Mortality) — {selected_year}")
        fig.update_traces(textinfo="percent+label", marker=dict(colors=pie_colors))
        fig.update_layout(template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info(f"No data to show for Top 10 Country Share for {selected_year}.")


# New section for Estimated Total Suicides (Absolute Numbers) and Regional Comparison
st.markdown("---")
st.markdown("### \U0001F4C9 Absolute Numbers & Regional Context")
col_abs_suicides, col_regional_avg = st.columns(2)

with col_abs_suicides:
    # Use filtered_data_for_year which already has 'estimated_total_suicides'
    top10_abs = filtered_data_for_year.sort_values("estimated_total_suicides", ascending=False).head(10)
    if not top10_abs.empty:
        # Dynamically color based on estimated_total_suicides
        abs_suicides_min = top10_abs['estimated_total_suicides'].min()
        abs_suicides_max = top10_abs['estimated_total_suicides'].max()
        if abs_suicides_max - abs_suicides_min != 0:
            bar_colors_abs = [get_dynamic_color(val, abs_suicides_min, abs_suicides_max, BLUE_COLOR_SCALE) for val in top10_abs["estimated_total_suicides"]]
        else:
            bar_colors_abs = [BLUE_COLOR_SCALE[len(BLUE_COLOR_SCALE)//2][1]] * len(top10_abs)

        fig = px.bar(top10_abs, x="country", y="estimated_total_suicides",
                     title=f"Top 10 Countries (by Estimated Total Suicides) — {selected_year}",
                     labels={"estimated_total_suicides": "Estimated Total Suicides"},
                     text_auto=".2s")
        fig.update_traces(marker_color=bar_colors_abs)
        fig.update_layout(showlegend=False, template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info(f"No data to show Top 10 Countries by Estimated Total Suicides for {selected_year}.")

with col_regional_avg:
    # Average crude mortality by OWID region for the selected year
    regional_avg_df = filtered_data_for_year.groupby("world_regions_according_to_owid")["crude_mortality"].mean().reset_index()
    regional_avg_df = regional_avg_df.sort_values("crude_mortality", ascending=False).dropna() # Sort and drop NaNs from region

    if not regional_avg_df.empty:
        # Dynamically color based on regional average crude mortality
        regional_min_mortality = regional_avg_df['crude_mortality'].min()
        regional_max_mortality = regional_avg_df['crude_mortality'].max()
        if regional_max_mortality - regional_min_mortality != 0:
            bar_colors_regional = [get_dynamic_color(val, regional_min_mortality, regional_max_mortality, BLUE_COLOR_SCALE) for val in regional_avg_df["crude_mortality"]]
        else:
            bar_colors_regional = [BLUE_COLOR_SCALE[len(BLUE_COLOR_SCALE)//2][1]] * len(regional_avg_df)

        fig = px.bar(regional_avg_df, x="world_regions_according_to_owid", y="crude_mortality",
                     title=f"Regional Average Suicide Rate — {selected_year}",
                     labels={"world_regions_according_to_owid": "Region", "crude_mortality": "Avg. Deaths per 100k"},
                     text_auto=".2f")
        fig.update_traces(marker_color=bar_colors_regional)
        fig.update_layout(showlegend=False, template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info(f"No regional average data available for {selected_year}.")

st.markdown("---")
st.download_button("⬇️ Download Filtered Data", filtered_df.to_csv(index=False), "filtered_data.csv")
st.markdown("© 2025 Lynn Shehab | MSBA382 - Individual Project | AUB")
