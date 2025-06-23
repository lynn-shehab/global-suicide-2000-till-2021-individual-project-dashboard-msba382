import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Load data
df = pd.read_csv("dashboard_data.csv")
df = df.dropna(subset=["crude_mortality", "year", "country"])

# --- COLOR DYNAMICS SETUP ---
# Determine the range of your suicide rate for color mapping
min_mortality = df['crude_mortality'].min()
max_mortality = df['crude_mortality'].max()

# Define a blue color scale (lighter for lower rates, darker for higher rates)
BLUE_COLOR_SCALE = [
    [0.0, "#E0F2F7"],  # Very Light Blue
    [0.2, "#B3E0F2"],
    [0.4, "#80CCEB"],
    [0.6, "#4DB8E0"],
    [0.8, "#1F77B4"],  # A standard blue (Plotly default)
    [1.0, "#0A3B57"]   # Very Dark Blue
]

def get_dynamic_color(value, min_val, max_val, color_scale):
    """
    Maps a value to a color within a defined color scale.
    """
    if pd.isna(value) or (max_val - min_val) == 0: # Handle division by zero if min_val == max_val
        # Return a middle shade or default blue if no variation or data
        return color_scale[len(color_scale)//2][1] if color_scale else "#1F77B4"

    normalized_value = (value - min_val) / (max_val - min_val)
    normalized_value = max(0.0, min(1.0, normalized_value)) # Ensure bounds

    # Find the two closest color points in the scale and interpolate
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
    return color_scale[-1][1] # Return darkest blue if value is max or above

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

# Get the crude mortality for the selected country and year
current_crude_mortality = latest['crude_mortality'].values[0] if not latest.empty else (min_mortality + max_mortality) / 2
# Determine the main line color based on the current crude mortality
main_line_color = get_dynamic_color(current_crude_mortality, min_mortality, max_mortality, BLUE_COLOR_SCALE)

# Default title font color for dark theme (common for Streamlit dashboards unless explicitly changed)
DEFAULT_TITLE_COLOR = "white" # Or "#FFFFFF" or "rgba(255, 255, 255, 0.8)" for a slightly softer white.

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
    fig = px.line(country_df, x="year", y="crude_mortality", markers=True,
                  title=f"Crude Mortality Over Time — {country}")
    # Apply the main dynamic blue color to the line chart
    fig.update_traces(line=dict(color=main_line_color))
    fig.update_layout(template="plotly_white", title_font_color=DEFAULT_TITLE_COLOR) # Restore title color
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

        # Dynamically color each bar based on its own 'rate' value
        bar_colors_age = [get_dynamic_color(rate, age_data['rate'].min(), age_data['rate'].max(), BLUE_COLOR_SCALE) for rate in age_data['rate']]

        fig = px.bar(
            age_data,
            x=age_data.index,
            y="rate",
            title=f"Suicide Rate by Age Group — {country} ({year})",
            labels={"rate": "Deaths per 100k", "index": "Age Group"},
            text_auto=".2f"
        )
        fig.update_traces(marker_color=bar_colors_age) # Apply the dynamic colors
        fig.update_layout(template="plotly_white", title_font_color=DEFAULT_TITLE_COLOR) # Restore title color
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Note: Only includes both sexes.")

with col3:
    if "male_to_female_suicide_death_rate_ratio_age_standardized" in country_df.columns:
        fig = px.line(
            country_df.dropna(subset=["male_to_female_suicide_death_rate_ratio_age_standardized"]),
            x="year", y="male_to_female_suicide_death_rate_ratio_age_standardized",
            title=f"M:F Suicide Ratio — {country}", markers=True
        )
        # Apply a consistent, but perhaps slightly contrasting blue, or vary based on ratio itself
        fig.update_traces(line=dict(color=main_line_color)) # Use the main line color for consistency
        fig.update_layout(template="plotly_white", title_font_color=DEFAULT_TITLE_COLOR) # Restore title color
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
                            color_continuous_scale="Blues", # Keep this as a continuous blue scale for the map
                            title=f"Suicide Rate Map — {year}")
    map_fig.update_layout(template="plotly_white", title_font_color=DEFAULT_TITLE_COLOR) # Restore title color
    st.plotly_chart(map_fig, use_container_width=True)

with col5:
    top10 = filtered_df.sort_values("crude_mortality", ascending=False).head(10)
    # Dynamically color each bar based on its own 'crude_mortality' value
    bar_colors_top10 = [get_dynamic_color(val, top10['crude_mortality'].min(), top10['crude_mortality'].max(), BLUE_COLOR_SCALE) for val in top10["crude_mortality"]]

    fig = px.bar(top10, x="country", y="crude_mortality",
                 title=f"Top 10 Countries — {year}", text_auto=".2s")
    fig.update_traces(marker_color=bar_colors_top10) # Apply the dynamic colors
    fig.update_layout(showlegend=False, template="plotly_white", title_font_color=DEFAULT_TITLE_COLOR) # Restore title color
    st.plotly_chart(fig, use_container_width=True)

with col6:
    region_data = top10.groupby("country")["crude_mortality"].mean().reset_index()
    pie_min_mortality = region_data["crude_mortality"].min()
    pie_max_mortality = region_data["crude_mortality"].max()
    pie_colors = [get_dynamic_color(val, pie_min_mortality, pie_max_mortality, BLUE_COLOR_SCALE) for val in region_data["crude_mortality"]]

    fig = px.pie(region_data, names="country", values="crude_mortality",
                 title=f"Top 10 Country Share — {year}")
    fig.update_traces(textinfo="percent+label", marker=dict(colors=pie_colors))
    fig.update_layout(template="plotly_white", title_font_color=DEFAULT_TITLE_COLOR) # Restore title color
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.download_button("⬇️ Download Filtered Data", filtered_df.to_csv(index=False), "filtered_data.csv")
st.markdown("© 2025 Lynn Shehab | MSBA382 - Individual Project | AUB")
