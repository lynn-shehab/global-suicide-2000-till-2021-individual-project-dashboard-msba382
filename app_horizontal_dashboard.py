import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go # Import plotly.graph_objects for custom color scales

# Load data
df = pd.read_csv("dashboard_data.csv")
df = df.dropna(subset=["crude_mortality", "year", "country"])

# --- COLOR DYNAMICS SETUP ---
# Determine the range of your suicide rate for color mapping
# We'll use the global min/max for a consistent scale across all years/countries
min_mortality = df['crude_mortality'].min()
max_mortality = df['crude_mortality'].max()

# Define a blue color scale (lighter for lower rates, darker for higher rates)
# These are Hex codes for various shades of blue. You can adjust these.
# '0.0': Lightest Blue (for min_mortality)
# '1.0': Darkest Blue (for max_mortality)
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
    if pd.isna(value) or min_val == max_val:
        return color_scale[0][1] # Return the lightest blue if no data or no variation

    normalized_value = (value - min_val) / (max_val - min_val)
    # Ensure normalized_value is within [0, 1] bounds
    normalized_value = max(0.0, min(1.0, normalized_value))

    # Find the two closest color points in the scale and interpolate
    for i in range(len(color_scale) - 1):
        if normalized_value >= color_scale[i][0] and normalized_value <= color_scale[i+1][0]:
            # Linear interpolation
            lower_bound_val, lower_bound_color = color_scale[i]
            upper_bound_val, upper_bound_color = color_scale[i+1]

            # Convert hex colors to RGB for interpolation
            def hex_to_rgb(hex_color):
                hex_color = hex_color.lstrip('#')
                return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

            def rgb_to_hex(rgb_color):
                return '#%02x%02x%02x' % rgb_color

            rgb1 = hex_to_rgb(lower_bound_color)
            rgb2 = hex_to_rgb(upper_bound_color)

            # Calculate interpolation factor
            if (upper_bound_val - lower_bound_val) == 0: # Avoid division by zero
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
current_crude_mortality = latest['crude_mortality'].values[0] if not latest.empty else min_mortality
# Determine the main color based on the current crude mortality
main_blue_color = get_dynamic_color(current_crude_mortality, min_mortality, max_mortality, BLUE_COLOR_SCALE)

# === TOP METRICS ===
st.markdown("### \U0001F522 Key Indicators")
col1, col3 = st.columns(2)

with col1:
    delta = (latest['crude_mortality'].values[0] - previous['crude_mortality'].values[0]) if not previous.empty and not latest.empty else None
    st.metric(
        "Crude Mortality Rate",
        f"{latest['crude_mortality'].values[0]:.2f} per 100k" if not latest.empty else "N/A",
        f"{delta:+.2f}" if delta is not None else "N/A",
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
                  title=f"Crude Mortality Over Time — {country}")
    # Apply the main dynamic blue color to the line chart
    fig.update_traces(line=dict(color=main_blue_color))
    fig.update_layout(template="plotly_white", title_font_color=main_blue_color) # Also update title color
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
            text_auto=".2f"
        )
        # Apply the main dynamic blue color to the bar chart
        fig.update_traces(marker_color=main_blue_color)
        fig.update_layout(template="plotly_white", title_font_color=main_blue_color)
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
        # For simplicity, we'll use the main_blue_color for now, or a fixed blue if preferred.
        fig.update_traces(line=dict(color=main_blue_color)) # Or a fixed color like "#007BFF"
        fig.update_layout(template="plotly_white", title_font_color=main_blue_color)
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# === REGIONAL ANALYSIS ===
st.markdown("### 🌍 Regional Analysis & Rankings")
col4, col5, col6 = st.columns(3)

with col4:
    # For the choropleth map, we want the color *scale* to be blue, and directly reflect mortality
    map_fig = px.choropleth(filtered_df,
                            locations="country",
                            locationmode="country names",
                            color="crude_mortality",
                            # Use a Plotly built-in bluescale for consistency on the map
                            color_continuous_scale="Blues", # Changed from Tealgrn to Blues
                            title=f"Suicide Rate Map — {year}")
    map_fig.update_layout(template="plotly_white", title_font_color=main_blue_color)
    st.plotly_chart(map_fig, use_container_width=True)

with col5:
    top10 = filtered_df.sort_values("crude_mortality", ascending=False).head(10)
    fig = px.bar(top10, x="country", y="crude_mortality", color="country",
                 title=f"Top 10 Countries — {year}", text_auto=".2s")
    # Instead of Set3, let's try a blue-toned discrete sequence
    # Plotly has some qualitative blues: 'qualitative.Dark24', 'qualitative.Set1', 'qualitative.Pastel1' etc.
    # Or, we can create a custom blue sequence based on the main_blue_color for the top bars.
    # For simplicity, let's use a dynamic range of blues based on the current highest crude mortality values.
    # Or, if you want *all* bars to be shades of blue, we can iterate and assign.
    # Let's try to make them all shades of blue, relative to their own value.
    bar_colors = [get_dynamic_color(val, min_mortality, max_mortality, BLUE_COLOR_SCALE) for val in top10["crude_mortality"]]
    fig.update_traces(marker_color=bar_colors) # Apply the dynamic colors
    fig.update_layout(showlegend=False, template="plotly_white", title_font_color=main_blue_color)
    st.plotly_chart(fig, use_container_width=True)

with col6:
    region_data = top10.groupby("country")["crude_mortality"].mean().reset_index()
    fig = px.pie(region_data, names="country", values="crude_mortality",
                 title=f"Top 10 Country Share — {year}")
    # For the pie chart, we could also use shades of blue, or a diverging color scale if preferred.
    # Let's try to generate shades of blue for the pie slices.
    pie_colors = [get_dynamic_color(val, min_mortality, max_mortality, BLUE_COLOR_SCALE) for val in region_data["crude_mortality"]]
    fig.update_traces(textinfo="percent+label", marker=dict(colors=pie_colors))
    fig.update_layout(template="plotly_white", title_font_color=main_blue_color)
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.download_button("⬇️ Download Filtered Data", filtered_df.to_csv(index=False), "filtered_data.csv")
st.markdown("© 2025 Lynn Shehab | MSBA382 - Individual Project | AUB")
