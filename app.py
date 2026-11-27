import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------

st.set_page_config(
    page_title="Airbnb Data Analytics Dashboard",
    page_icon="🏡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------
# THEME / BACKGROUND
# ---------------------------------------------------------

THEMES = {
    "Midnight Blue": {
        "page": "#0B1220", "sidebar": "#111C30", "card": "#17243A",
        "text": "#F4F7FB", "muted": "#AAB7CC", "accent": "#62D6C8",
        "plot": "#17243A", "grid": "#34445D"
    },
    "Light": {
        "page": "#F3F6FB", "sidebar": "#E7EDF6", "card": "#FFFFFF",
        "text": "#172033", "muted": "#5B6578", "accent": "#2563EB",
        "plot": "#FFFFFF", "grid": "#DCE3EE"
    },
    "Purple Glow": {
        "page": "#171126", "sidebar": "#21183A", "card": "#2B2048",
        "text": "#FAF7FF", "muted": "#C4B8DC", "accent": "#C084FC",
        "plot": "#2B2048", "grid": "#55436F"
    },
    "Forest Green": {
        "page": "#0E1B18", "sidebar": "#142923", "card": "#1C382F",
        "text": "#F1FFF8", "muted": "#B1D0C2", "accent": "#6EE7B7",
        "plot": "#1C382F", "grid": "#36594C"
    },
    "Sunset": {
        "page": "#241613", "sidebar": "#38221D", "card": "#4A2C25",
        "text": "#FFF7F2", "muted": "#E6C2B4", "accent": "#FDBA74",
        "plot": "#4A2C25", "grid": "#765044"
    }
}

with st.sidebar:
    st.title("🏡 Airbnb Dashboard")
    st.caption("Interactive data exploration")

    theme_name = st.selectbox(
        "🎨 Dashboard background",
        list(THEMES.keys())
    )

    theme = THEMES[theme_name]

st.markdown(
    f"""
    <style>
    .stApp {{
        background: {theme['page']};
        color: {theme['text']};
    }}

    [data-testid="stSidebar"] {{
        background: {theme['sidebar']};
    }}

    [data-testid="stHeader"] {{
        background: transparent;
    }}

    h1, h2, h3, p, label, span {{
        color: {theme['text']};
    }}

    div[data-testid="stMetric"] {{
        background: {theme['card']};
        border: 1px solid {theme['grid']};
        padding: 18px 20px;
        border-radius: 15px;
    }}

    div[data-testid="stMetricLabel"] {{
        color: {theme['muted']};
    }}

    div[data-testid="stMetricValue"] {{
        color: {theme['accent']};
    }}

    .block-container {{
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }}

    div[data-testid="stFileUploader"] {{
        background: {theme['card']};
        border: 1px dashed {theme['accent']};
        border-radius: 12px;
        padding: 12px;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# ---------------------------------------------------------
# DATA UPLOAD
# ---------------------------------------------------------

st.title("🏡 Airbnb Listings – Data Analytics Dashboard")

st.success("✅ Dashboard Loaded Successfully!")

st.markdown(
    "Upload your Airbnb CSV file to explore listings, prices, availability, hosts and reviews."
)

uploaded_file = st.sidebar.file_uploader(
    "📂 Upload Airbnb CSV file",
    type=["csv"],
    help="Your CSV is processed in this Streamlit session."
)

if uploaded_file is None:

    st.info("👈 Upload your Airbnb CSV file from the sidebar to load the dashboard.")

    st.markdown("""
    **How to use**

    1. Choose your CSV file using the upload button.
    2. Select a dashboard theme from the sidebar.
    3. Use the filters and dropdowns to explore the data.
    4. Download the filtered data whenever required.

    Your 35 MB dataset can stay on your computer.
    """)

    st.stop()

# ---------------------------------------------------------
# LOAD + CLEAN DATA
# ---------------------------------------------------------

@st.cache_data(show_spinner="Loading and preparing your Airbnb data...")

def load_data(file_bytes):

    from io import BytesIO

    data = pd.read_csv(
        BytesIO(file_bytes),
        low_memory=False
    )

    data.columns = data.columns.str.strip()

    rename_map = {
        "host id": "host_id",
        "host name": "host_name",
        "neighbourhood group": "neighbourhood_group",
        "room type": "room_type",
        "Construction year": "Construction_year",
        "service fee": "service_fee",
        "minimum nights": "minimum_nights",
        "number of reviews": "number_of_reviews",
        "last review": "last_review",
        "reviews per month": "reviews_per_month",
        "review rate number": "review_rate_number",
        "calculated host listings count": "calculated_host_listings_count",
        "availability 365": "availability_365"
    }

    data = data.rename(columns=rename_map)

    drop_cols = [
        c for c in ["id", "lat", "long", "country code", "house_rules"]
        if c in data.columns
    ]

    data = data.drop(columns=drop_cols)

    text_cols = [
        "NAME", "host_name", "host_identity_verified",
        "neighbourhood_group", "neighbourhood", "country",
        "instant_bookable", "cancellation_policy",
        "room_type", "license"
    ]

    for col in text_cols:

        if col in data.columns:

            data[col] = (
                data[col]
                .fillna("Unknown")
                .astype(str)
                .str.strip()
            )

    if "neighbourhood_group" in data.columns:

        data["neighbourhood_group"] = data[
            "neighbourhood_group"
        ].replace({
            "brookln": "Brooklyn",
            "manhatan": "Manhattan"
        })

    numeric_cols = [
        "price", "service_fee", "Construction_year",
        "minimum_nights", "number_of_reviews",
        "reviews_per_month", "review_rate_number",
        "calculated_host_listings_count",
        "availability_365", "host_id"
    ]

    for col in numeric_cols:

        if col in data.columns:

            cleaned = data[col].astype(str).str.replace(
                r"[$,]", "", regex=True
            )

            data[col] = pd.to_numeric(
                cleaned,
                errors="coerce"
            )

    if "last_review" in data.columns:

        data["last_review"] = pd.to_datetime(
            data["last_review"],
            errors="coerce"
        )

    for col in numeric_cols:

        if col in data.columns:

            median_value = data[col].median()

            data[col] = data[col].fillna(
                median_value if pd.notna(median_value) else 0
            )

    if "last_review" in data.columns:

        data["Year"] = data["last_review"].dt.year
        data["Month"] = data["last_review"].dt.month_name()
        data["Month_Number"] = data["last_review"].dt.month

    return data


try:

    df = load_data(uploaded_file.getvalue())

except Exception as e:

    st.error(f"Could not read this file. Please upload a valid CSV. Details: {e}")
    st.stop()


if df.empty:

    st.warning("The uploaded CSV has no rows.")
    st.stop()

# ---------------------------------------------------------
# FILTERS
# ---------------------------------------------------------

st.sidebar.divider()
st.sidebar.subheader("🔎 Dashboard Filters")

filtered = df.copy()

if "neighbourhood_group" in filtered.columns:

    groups = sorted(
        filtered["neighbourhood_group"].dropna().astype(str).unique().tolist()
    )

    chosen_groups = st.sidebar.multiselect(
        "Neighbourhood group",
        groups,
        default=groups
    )

    if chosen_groups:

        filtered = filtered[
            filtered["neighbourhood_group"].astype(str).isin(chosen_groups)
        ]

if "room_type" in filtered.columns:

    rooms = sorted(
        filtered["room_type"].dropna().astype(str).unique().tolist()
    )

    chosen_rooms = st.sidebar.multiselect(
        "Room type",
        rooms,
        default=rooms
    )

    if chosen_rooms:

        filtered = filtered[
            filtered["room_type"].astype(str).isin(chosen_rooms)
        ]

if "host_identity_verified" in filtered.columns:

    verified = sorted(
        filtered["host_identity_verified"].dropna().astype(str).unique().tolist()
    )

    chosen_verified = st.sidebar.multiselect(
        "Host verification",
        verified,
        default=verified
    )

    if chosen_verified:

        filtered = filtered[
            filtered["host_identity_verified"].astype(str).isin(chosen_verified)
        ]

if filtered.empty:

    st.warning("No records match the selected filters.")
    st.stop()

# ---------------------------------------------------------
# KPI CARDS
# ---------------------------------------------------------

def numeric_mean(column):

    return (
        filtered[column].mean()
        if column in filtered.columns
        else np.nan
    )


total_listings = len(filtered)

avg_price = numeric_mean("price")

avg_availability = numeric_mean("availability_365")

total_hosts = (
    filtered["host_id"].nunique()
    if "host_id" in filtered.columns
    else (
        filtered["host_name"].nunique()
        if "host_name" in filtered.columns
        else 0
    )
)

total_reviews = (
    filtered["number_of_reviews"].sum()
    if "number_of_reviews" in filtered.columns
    else 0
)

st.subheader("📌 Key Performance Indicators")

k1, k2, k3, k4, k5 = st.columns(5)

k1.metric("Total Listings", f"{total_listings:,.0f}")

k2.metric(
    "Average Price",
    f"${avg_price:,.2f}" if pd.notna(avg_price) else "N/A"
)

k3.metric(
    "Avg. Availability",
    f"{avg_availability:,.1f} days"
    if pd.notna(avg_availability) else "N/A"
)

k4.metric("Total Hosts", f"{total_hosts:,.0f}")

k5.metric("Total Reviews", f"{total_reviews:,.0f}")

st.divider()

# ---------------------------------------------------------
# PLOTLY STYLE
# ---------------------------------------------------------

plot_template = (
    "plotly_dark"
    if theme_name != "Light"
    else "plotly_white"
)


def style_fig(fig, height=430):

    fig.update_layout(
        template=plot_template,
        paper_bgcolor=theme["page"],
        plot_bgcolor=theme["plot"],
        font=dict(
            color=theme["text"],
            size=12
        ),
        title_font=dict(size=17),
        height=height,
        margin=dict(
            l=25,
            r=25,
            t=65,
            b=45
        ),
        legend_title_text="",
        hoverlabel=dict(font_size=13)
    )

    fig.update_xaxes(
        showgrid=False,
        automargin=True
    )

    fig.update_yaxes(
        gridcolor=theme["grid"],
        zerolinecolor=theme["grid"],
        automargin=True
    )

    return fig


def show_chart(fig):

    st.plotly_chart(
        style_fig(fig),
        use_container_width=True,
        theme=None
    )

# ---------------------------------------------------------
# MAIN DASHBOARD VISUALS
# ---------------------------------------------------------

st.subheader("📊 Airbnb Overview")

col1, col2 = st.columns(2)

if "neighbourhood" in filtered.columns:

    listing_area = (
        filtered["neighbourhood"]
        .value_counts()
        .head(10)
        .reset_index()
    )

    listing_area.columns = [
        "Neighbourhood",
        "Listings"
    ]

    fig = px.bar(
        listing_area,
        x="Listings",
        y="Neighbourhood",
        orientation="h",
        color="Listings",
        color_continuous_scale="Teal",
        title="Top 10 Neighbourhoods by Listings",
        text="Listings"
    )

    fig.update_traces(textposition="outside")

    with col1:
        show_chart(fig)


if "neighbourhood" in filtered.columns and "price" in filtered.columns:

    price_area = (
        filtered.groupby("neighbourhood", as_index=False)["price"]
        .mean()
    )

    price_area = price_area.nlargest(10, "price")

    fig = px.bar(
        price_area,
        x="price",
        y="neighbourhood",
        orientation="h",
        color="price",
        color_continuous_scale="Sunset",
        title="Top 10 Neighbourhoods by Average Price",
        labels={
            "price": "Average price",
            "neighbourhood": "Neighbourhood"
        }
    )

    with col2:
        show_chart(fig)


col3, col4 = st.columns(2)

if "price" in filtered.columns:

    price_data = filtered[
        filtered["price"].between(
            0,
            filtered["price"].quantile(0.99)
        )
    ]

    fig = px.histogram(
        price_data,
        x="price",
        nbins=45,
        marginal="box",
        color_discrete_sequence=[theme["accent"]],
        title="Price Distribution (up to 99th percentile)"
    )

    with col3:
        show_chart(fig)


if "room_type" in filtered.columns:

    room_data = (
        filtered["room_type"]
        .value_counts()
        .rename_axis("Room Type")
        .reset_index(name="Listings")
    )

    fig = px.pie(
        room_data,
        names="Room Type",
        values="Listings",
        hole=0.55,
        title="Room Type Distribution",
        color_discrete_sequence=px.colors.qualitative.Set2
    )

    fig.update_traces(
        textposition="inside",
        textinfo="percent+label"
    )

    with col4:
        show_chart(fig)


col5, col6 = st.columns(2)

if "availability_365" in filtered.columns:

    fig = px.histogram(
        filtered,
        x="availability_365",
        nbins=35,
        color_discrete_sequence=["#60A5FA"],
        title="Availability Distribution (Days per Year)"
    )

    with col5:
        show_chart(fig)


if (
    "neighbourhood_group" in filtered.columns
    and "room_type" in filtered.columns
):

    room_group = (
        filtered.groupby(
            ["neighbourhood_group", "room_type"]
        )
        .size()
        .reset_index(name="Listings")
    )

    fig = px.bar(
        room_group,
        x="neighbourhood_group",
        y="Listings",
        color="room_type",
        barmode="group",
        title="Room Types by Neighbourhood Group"
    )

    with col6:
        show_chart(fig)

# ---------------------------------------------------------
# EXTRA ANALYSIS TABS
# ---------------------------------------------------------

st.divider()

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📍 Location & Price",
    "🗓️ Availability",
    "👤 Host Analysis",
    "⭐ Reviews & Ratings",
    "🎛️ Explore Parameters"
])

# ---------------------------------------------------------
# LOCATION & PRICE
# ---------------------------------------------------------

with tab1:

    left, right = st.columns(2)

    if (
        "neighbourhood_group" in filtered.columns
        and "price" in filtered.columns
    ):

        gp = (
            filtered.groupby(
                "neighbourhood_group",
                as_index=False
            )["price"]
            .mean()
            .sort_values("price", ascending=False)
        )

        fig = px.bar(
            gp,
            x="neighbourhood_group",
            y="price",
            color="price",
            title="Average Price by Neighbourhood Group",
            color_continuous_scale="Viridis"
        )

        with left:
            show_chart(fig)

    if (
        "room_type" in filtered.columns
        and "price" in filtered.columns
    ):

        rp = (
            filtered.groupby(
                "room_type",
                as_index=False
            )["price"]
            .mean()
            .sort_values("price", ascending=False)
        )

        fig = px.bar(
            rp,
            x="room_type",
            y="price",
            color="room_type",
            title="Average Price by Room Type"
        )

        with right:
            show_chart(fig)

    if (
        "neighbourhood" in filtered.columns
        and "availability_365" in filtered.columns
    ):

        av = (
            filtered.groupby(
                "neighbourhood",
                as_index=False
            )["availability_365"]
            .mean()
            .nlargest(10, "availability_365")
        )

        fig = px.bar(
            av,
            x="availability_365",
            y="neighbourhood",
            orientation="h",
            title="Top 10 Neighbourhoods by Average Availability",
            color="availability_365"
        )

        show_chart(fig)

# ---------------------------------------------------------
# AVAILABILITY
# ---------------------------------------------------------

with tab2:

    if (
        "Year" in filtered.columns
        and filtered["Year"].notna().any()
        and "availability_365" in filtered.columns
    ):

        yearly = (
            filtered.dropna(subset=["Year"])
            .groupby("Year", as_index=False)["availability_365"]
            .mean()
        )

        fig = px.line(
            yearly,
            x="Year",
            y="availability_365",
            markers=True,
            title="Average Availability by Last Review Year"
        )

        show_chart(fig)

    else:

        st.info(
            "A valid 'last review' date column is needed for yearly availability."
        )

    if (
        "Month_Number" in filtered.columns
        and filtered["Month_Number"].notna().any()
        and "availability_365" in filtered.columns
    ):

        monthly = (
            filtered.dropna(subset=["Month_Number"])
            .groupby("Month_Number", as_index=False)["availability_365"]
            .mean()
        )

        month_names = [
            "Jan", "Feb", "Mar", "Apr",
            "May", "Jun", "Jul", "Aug",
            "Sep", "Oct", "Nov", "Dec"
        ]

        monthly["Month"] = monthly["Month_Number"].map(
            lambda x: (
                month_names[int(x) - 1]
                if 1 <= int(x) <= 12
                else str(x)
            )
        )

        fig = px.line(
            monthly,
            x="Month",
            y="availability_365",
            markers=True,
            title="Average Availability by Review Month"
        )

        show_chart(fig)

    else:

        st.caption(
            "Monthly trend is shown when valid last-review dates are available."
        )

# ---------------------------------------------------------
# HOST ANALYSIS
# ---------------------------------------------------------

with tab3:

    left, right = st.columns(2)

    if "host_name" in filtered.columns:

        top_hosts = (
            filtered["host_name"]
            .value_counts()
            .head(10)
            .rename_axis("Host")
            .reset_index(name="Listings")
        )

        fig = px.bar(
            top_hosts,
            x="Listings",
            y="Host",
            orientation="h",
            title="Top 10 Hosts by Listing Count",
            color="Listings"
        )

        with left:
            show_chart(fig)

    if (
        "host_identity_verified" in filtered.columns
        and "review_rate_number" in filtered.columns
    ):

        verify_rating = (
            filtered.groupby(
                "host_identity_verified",
                as_index=False
            )["review_rate_number"]
            .mean()
        )

        fig = px.bar(
            verify_rating,
            x="host_identity_verified",
            y="review_rate_number",
            color="host_identity_verified",
            title="Average Rating by Host Verification"
        )

        with right:
            show_chart(fig)

    if (
        "host_name" in filtered.columns
        and "number_of_reviews" in filtered.columns
    ):

        host_reviews = (
            filtered.groupby(
                "host_name",
                as_index=False
            )["number_of_reviews"]
            .sum()
            .nlargest(10, "number_of_reviews")
        )

        fig = px.bar(
            host_reviews,
            x="number_of_reviews",
            y="host_name",
            orientation="h",
            title="Top 10 Hosts by Total Reviews",
            color="number_of_reviews"
        )

        show_chart(fig)

# ---------------------------------------------------------
# REVIEWS & RATINGS
# ---------------------------------------------------------

with tab4:

    left, right = st.columns(2)

    if (
        "room_type" in filtered.columns
        and "number_of_reviews" in filtered.columns
    ):

        room_reviews = (
            filtered.groupby(
                "room_type",
                as_index=False
            )["number_of_reviews"]
            .mean()
        )

        fig = px.bar(
            room_reviews,
            x="room_type",
            y="number_of_reviews",
            color="room_type",
            title="Average Reviews by Room Type"
        )

        with left:
            show_chart(fig)

    if (
        "neighbourhood" in filtered.columns
        and "number_of_reviews" in filtered.columns
    ):

        neighbourhood_reviews = (
            filtered.groupby(
                "neighbourhood",
                as_index=False
            )["number_of_reviews"]
            .sum()
            .nlargest(10, "number_of_reviews")
        )

        fig = px.bar(
            neighbourhood_reviews,
            x="number_of_reviews",
            y="neighbourhood",
            orientation="h",
            title="Top 10 Neighbourhoods by Total Reviews",
            color="number_of_reviews"
        )

        with right:
            show_chart(fig)

    if {
        "price",
        "number_of_reviews"
    }.issubset(filtered.columns):

        sample = filtered[
            ["price", "number_of_reviews"]
        ].dropna()

        if len(sample) > 12000:

            sample = sample.sample(
                12000,
                random_state=42
            )

        fig = px.scatter(
            sample,
            x="price",
            y="number_of_reviews",
            opacity=0.45,
            title="Price vs Number of Reviews",
            trendline="ols"
        )

        show_chart(fig)

    corr_cols = [
        c for c in [
            "price",
            "service_fee",
            "minimum_nights",
            "number_of_reviews",
            "reviews_per_month",
            "review_rate_number",
            "calculated_host_listings_count",
            "availability_365"
        ]
        if c in filtered.columns
    ]

    if len(corr_cols) >= 2:

        corr = filtered[corr_cols].corr(
            numeric_only=True
        )

        fig = px.imshow(
            corr,
            text_auto=".2f",
            aspect="auto",
            color_continuous_scale="RdBu_r",
            zmin=-1,
            zmax=1,
            title="Correlation Heatmap"
        )

        show_chart(fig)

# ---------------------------------------------------------
# EXPLORE PARAMETERS
# ---------------------------------------------------------

with tab5:

    st.markdown(
        "Choose any columns and chart type. "
        "This section updates based on your selections."
    )

    all_columns = filtered.columns.tolist()

    numeric_columns = (
        filtered.select_dtypes(include=np.number)
        .columns.tolist()
    )

    cat_columns = (
        filtered.select_dtypes(include=["object", "category"])
        .columns.tolist()
    )

    c1, c2, c3 = st.columns(3)

    x_options = cat_columns + numeric_columns

    x_col = c1.selectbox(
        "Select X-axis parameter",
        x_options,
        index=0 if x_options else None
    )

    y_options = [
        col for col in numeric_columns
        if col != x_col
    ] or all_columns

    y_col = c2.selectbox(
        "Select Y-axis parameter",
        y_options,
        index=0 if y_options else None
    )

    chart_type = c3.selectbox(
        "Select chart type",
        [
            "Bar",
            "Line",
            "Scatter",
            "Histogram",
            "Box",
            "Violin",
            "Area",
            "Pie"
        ]
    )

    if x_col and y_col:

        chart_df = filtered[
            [x_col, y_col]
        ].dropna()

        if len(chart_df) > 15000:

            chart_df = chart_df.sample(
                15000,
                random_state=42
            )

        try:

            if chart_type == "Bar":

                agg = (
                    chart_df.groupby(
                        x_col,
                        as_index=False
                    )[y_col]
                    .mean()
                    .nlargest(25, y_col)
                )

                fig = px.bar(
                    agg,
                    x=x_col,
                    y=y_col,
                    color=y_col,
                    title=f"{y_col} by {x_col}"
                )

            elif chart_type == "Line":

                agg = (
                    chart_df.groupby(
                        x_col,
                        as_index=False
                    )[y_col]
                    .mean()
                    .sort_values(x_col)
                )

                fig = px.line(
                    agg,
                    x=x_col,
                    y=y_col,
                    markers=True,
                    title=f"{y_col} by {x_col}"
                )

            elif chart_type == "Scatter":

                fig = px.scatter(
                    chart_df,
                    x=x_col,
                    y=y_col,
                    opacity=0.55,
                    title=f"{y_col} vs {x_col}"
                )

            elif chart_type == "Histogram":

                fig = px.histogram(
                    filtered,
                    x=x_col,
                    nbins=40,
                    title=f"Distribution of {x_col}"
                )

            elif chart_type == "Box":

                fig = px.box(
                    chart_df,
                    x=x_col if x_col in cat_columns else None,
                    y=y_col if y_col in numeric_columns else x_col,
                    title=f"Box Plot: {y_col} by {x_col}"
                )

            elif chart_type == "Violin":

                fig = px.violin(
                    chart_df,
                    x=x_col if x_col in cat_columns else None,
                    y=y_col,
                    box=True,
                    points="outliers",
                    title=f"Violin Plot: {y_col} by {x_col}"
                )

            elif chart_type == "Area":

                agg = (
                    chart_df.groupby(
                        x_col,
                        as_index=False
                    )[y_col]
                    .mean()
                    .sort_values(x_col)
                )

                fig = px.area(
                    agg,
                    x=x_col,
                    y=y_col,
                    title=f"{y_col} by {x_col}"
                )

            else:

                pie_data = (
                    filtered[x_col]
                    .value_counts()
                    .head(12)
                    .rename_axis(x_col)
                    .reset_index(name="Count")
                )

                fig = px.pie(
                    pie_data,
                    names=x_col,
                    values="Count",
                    hole=0.35,
                    title=f"Distribution of {x_col}"
                )

            show_chart(fig)

        except Exception as e:

            st.error(
                f"Could not create this chart with the selected parameters: {e}"
            )

# ---------------------------------------------------------
# DATA PREVIEW + DOWNLOAD
# ---------------------------------------------------------

st.divider()

with st.expander("🔍 View filtered data"):

    st.dataframe(
        filtered.head(1000),
        use_container_width=True,
        height=350
    )

    st.caption(
        f"Showing up to 1,000 rows from {len(filtered):,} filtered records."
    )

csv_data = filtered.to_csv(
    index=False
).encode("utf-8")

st.download_button(
    "⬇️ Download filtered data as CSV",
    data=csv_data,
    file_name="airbnb_filtered_data.csv",
    mime="text/csv"
)

st.caption(
    "Airbnb Data Analytics Dashboard • Built with Streamlit, Pandas and Plotly"
)
