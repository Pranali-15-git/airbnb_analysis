
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# ============================================================
# 1. PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Airbnb Insights",
    page_icon="🏡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# 2. CUSTOM CSS
# ============================================================

st.markdown("""
<style>

.stApp {
    background: #F4F7FC;
}

[data-testid="stSidebar"] {
    background-color: #EAF0FA;
}

.main-title {
    font-size: 38px;
    font-weight: 800;
    color: #182B49;
}

.subtitle {
    color: #718096;
    font-size: 16px;
}

.kpi-card {
    background: linear-gradient(135deg, #FFFFFF, #F8FAFF);
    padding: 22px 20px;
    border-radius: 18px;
    border: 1px solid #E3EAF4;
    box-shadow: 0 4px 15px rgba(34, 60, 100, 0.06);
    min-height: 125px;
}

.kpi-title {
    color: #718096;
    font-size: 14px;
    font-weight: 600;
}

.kpi-value {
    color: #183153;
    font-size: 27px;
    font-weight: 800;
    margin-top: 8px;
}

.section-title {
    font-size: 24px;
    font-weight: 750;
    color: #183153;
}

div[data-testid="stPlotlyChart"] {
    background: white;
    border-radius: 16px;
    border: 1px solid #E8EDF5;
    padding: 8px;
}

div[data-testid="stMetric"] {
    background: white;
    border-radius: 15px;
    padding: 16px;
    border: 1px solid #E3EAF4;
}

.stButton > button {
    border-radius: 10px;
}

</style>
""", unsafe_allow_html=True)

# ============================================================
# 3. HEADER
# ============================================================

st.markdown(
    '<div class="main-title">🏡 Airbnb Insights Dashboard</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">Explore Airbnb data with interactive analytics, '
    'filters and visualizations</div>',
    unsafe_allow_html=True
)

st.markdown("---")

# ============================================================
# 4. UPLOAD DATA
# ============================================================

st.sidebar.markdown("## 📂 Dataset")

uploaded_file = st.sidebar.file_uploader(
    "Upload Airbnb CSV file",
    type=["csv"]
)

if uploaded_file is None:
    st.markdown("""
    ### 👋 Welcome to Airbnb Insights

    Upload your Airbnb dataset using the sidebar to start exploring.

    **Dashboard features:**
    - Interactive parameter dropdown
    - Dynamic Plotly visualizations
    - Price and neighbourhood analysis
    - Host and customer analysis
    - Availability and reviews
    - CSV download
    """)
    st.stop()

# ============================================================
# 5. DATA CLEANING
# ============================================================

@st.cache_data(show_spinner="Loading and cleaning dataset...")
def load_data(file):

    data = pd.read_csv(file, low_memory=False)

    # Standardize columns
    data.columns = (
        data.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
    )

    # Remove unnecessary columns
    data = data.drop(
        columns=[
            "id",
            "lat",
            "long",
            "country_code",
            "house_rules"
        ],
        errors="ignore"
    )

    # Numeric columns
    numeric_columns = [
        "host_id",
        "price",
        "service_fee",
        "minimum_nights",
        "number_of_reviews",
        "reviews_per_month",
        "review_rate_number",
        "calculated_host_listings_count",
        "availability_365",
        "construction_year"
    ]

    for col in numeric_columns:

        if col in data.columns:

            data[col] = (
                data[col]
                .astype(str)
                .str.replace(r"[$,]", "", regex=True)
            )

            data[col] = pd.to_numeric(
                data[col],
                errors="coerce"
            )

    # Text columns
    text_columns = [
        "name",
        "host_name",
        "neighbourhood_group",
        "neighbourhood",
        "room_type",
        "host_identity_verified",
        "instant_bookable",
        "cancellation_policy",
        "country",
        "license"
    ]

    for col in text_columns:

        if col in data.columns:

            data[col] = (
                data[col]
                .fillna("Unknown")
                .astype(str)
                .str.strip()
            )

    # Standardize neighbourhood spellings
    if "neighbourhood_group" in data.columns:

        data["neighbourhood_group"] = (
            data["neighbourhood_group"]
            .replace({
                "brookln": "Brooklyn",
                "manhatan": "Manhattan"
            })
        )

    # Dates
    if "last_review" in data.columns:

        data["last_review"] = pd.to_datetime(
            data["last_review"],
            errors="coerce"
        )

        data["review_year"] = data["last_review"].dt.year
        data["review_month"] = data["last_review"].dt.month_name()

    return data


df = load_data(uploaded_file)

# ============================================================
# 6. FILTERS
# ============================================================

st.sidebar.markdown("---")
st.sidebar.markdown("## 🎛️ Filters")

filtered_df = df.copy()

if "neighbourhood_group" in df.columns:

    options = sorted(df["neighbourhood_group"].dropna().unique())

    selected_group = st.sidebar.multiselect(
        "Neighbourhood Group",
        options,
        default=options
    )

    filtered_df = filtered_df[
        filtered_df["neighbourhood_group"].isin(selected_group)
    ]

if "room_type" in df.columns:

    options = sorted(df["room_type"].dropna().unique())

    selected_room = st.sidebar.multiselect(
        "Room Type",
        options,
        default=options
    )

    filtered_df = filtered_df[
        filtered_df["room_type"].isin(selected_room)
    ]

if "host_identity_verified" in df.columns:

    options = sorted(
        df["host_identity_verified"].dropna().unique()
    )

    selected_host = st.sidebar.multiselect(
        "Host Verification",
        options,
        default=options
    )

    filtered_df = filtered_df[
        filtered_df["host_identity_verified"].isin(selected_host)
    ]

if "cancellation_policy" in df.columns:

    options = sorted(
        df["cancellation_policy"].dropna().unique()
    )

    selected_cancel = st.sidebar.multiselect(
        "Cancellation Policy",
        options,
        default=options
    )

    filtered_df = filtered_df[
        filtered_df["cancellation_policy"].isin(selected_cancel)
    ]

st.sidebar.markdown("---")

st.sidebar.metric(
    "Filtered Records",
    f"{len(filtered_df):,}"
)

# ============================================================
# 7. HELPER FUNCTIONS
# ============================================================

def make_chart(fig, height=430):

    fig.update_layout(
        template="plotly_white",
        height=height,
        font=dict(
            family="Arial",
            size=13,
            color="#334155"
        ),
        title_font=dict(
            size=19,
            color="#183153"
        ),
        margin=dict(
            l=35,
            r=25,
            t=65,
            b=40
        ),
        hovermode="closest"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


def show_kpi(title, value, icon):

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">{icon} {title}</div>
            <div class="kpi-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def available(col):

    return col in filtered_df.columns


# ============================================================
# 8. KPI DASHBOARD
# ============================================================

total_listing = len(filtered_df)

avg_price = (
    filtered_df["price"].mean()
    if available("price")
    else 0
)

avg_availability = (
    filtered_df["availability_365"].mean()
    if available("availability_365")
    else 0
)

total_host = (
    filtered_df["host_id"].nunique()
    if available("host_id")
    else 0
)

total_reviews = (
    filtered_df["number_of_reviews"].sum()
    if available("number_of_reviews")
    else 0
)

k1, k2, k3, k4, k5 = st.columns(5)

with k1:
    show_kpi("Total Listings", f"{total_listing:,}", "🏘️")

with k2:
    show_kpi("Average Price", f"${avg_price:,.2f}", "💰")

with k3:
    show_kpi("Avg Availability", f"{avg_availability:,.1f} days", "📅")

with k4:
    show_kpi("Total Hosts", f"{total_host:,}", "👤")

with k5:
    show_kpi("Total Reviews", f"{total_reviews:,.0f}", "⭐")

st.markdown("---")

# ============================================================
# 9. DASHBOARD TABS
# ============================================================

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🏠 Overview",
    "🎯 Parameter Explorer",
    "📍 Location",
    "💰 Price",
    "👤 Hosts & Reviews",
    "📋 Dataset"
])

# ============================================================
# TAB 1: OVERVIEW
# ============================================================

with tab1:

    st.markdown("## 📊 Airbnb Overview")

    col1, col2 = st.columns(2)

    # Listings by room type
    with col1:

        if available("room_type"):

            room_data = (
                filtered_df["room_type"]
                .value_counts()
                .reset_index()
            )

            room_data.columns = ["Room Type", "Listings"]

            fig = px.pie(
                room_data,
                names="Room Type",
                values="Listings",
                hole=0.55,
                title="Room Type Distribution",
                color_discrete_sequence=px.colors.qualitative.Bold
            )

            fig.update_traces(
                textinfo="label+percent",
                pull=[0.04] * len(room_data)
            )

            make_chart(fig)

    # Neighbourhood listings
    with col2:

        if available("neighbourhood_group"):

            location_data = (
                filtered_df["neighbourhood_group"]
                .value_counts()
                .reset_index()
            )

            location_data.columns = [
                "Neighbourhood Group",
                "Listings"
            ]

            fig = px.bar(
                location_data,
                x="Neighbourhood Group",
                y="Listings",
                color="Listings",
                text="Listings",
                title="Listings by Neighbourhood Group",
                color_continuous_scale="Blues"
            )

            make_chart(fig)

    # Price distribution
    col1, col2 = st.columns(2)

    with col1:

        if available("price"):

            fig = px.histogram(
                filtered_df,
                x="price",
                nbins=50,
                title="Price Distribution",
                marginal="box",
                color_discrete_sequence=["#636EFA"]
            )

            make_chart(fig)

    with col2:

        if available("availability_365"):

            fig = px.histogram(
                filtered_df,
                x="availability_365",
                nbins=40,
                title="Availability Distribution",
                color_discrete_sequence=["#00CC96"]
            )

            make_chart(fig)

# ============================================================
# TAB 2: PARAMETER EXPLORER
# ============================================================

with tab2:

    st.markdown("## 🎯 Dynamic Parameter Explorer")

    st.markdown(
        "Select a parameter from the dropdown. "
        "The graphs and statistics will update automatically."
    )

    numeric_parameters = [
        col for col in filtered_df.select_dtypes(
            include=np.number
        ).columns
        if filtered_df[col].nunique() > 1
    ]

    if numeric_parameters:

        # Dropdown 1: Parameter
        selected_parameter = st.selectbox(
            "🔽 Select Parameter",
            numeric_parameters,
            index=(
                numeric_parameters.index("price")
                if "price" in numeric_parameters
                else 0
            ),
            key="parameter_dropdown"
        )

        # Dropdown 2: Chart type
        chart_type = st.selectbox(
            "📈 Select Visualization",
            [
                "Histogram",
                "Box Plot",
                "Violin Plot",
                "Density Plot",
                "Scatter Plot",
                "Bar Chart"
            ],
            key="chart_dropdown"
        )

        # Dropdown 3: Grouping
        categorical_columns = [
            col for col in filtered_df.select_dtypes(
                include=["object", "category"]
            ).columns
            if filtered_df[col].nunique() > 1
        ]

        group_options = ["None"] + categorical_columns

        selected_group = st.selectbox(
            "📌 Group Parameter By",
            group_options,
            index=(
                group_options.index("room_type")
                if "room_type" in group_options
                else 0
            ),
            key="group_dropdown"
        )

        data = filtered_df[
            selected_parameter
        ].dropna()

        # Parameter KPIs
        st.markdown("### 📌 Parameter Summary")

        a, b, c, d = st.columns(4)

        a.metric("Average", f"{data.mean():,.2f}")
        b.metric("Median", f"{data.median():,.2f}")
        c.metric("Maximum", f"{data.max():,.2f}")
        d.metric("Minimum", f"{data.min():,.2f}")

        st.markdown("---")

        # Dynamic chart
        if chart_type == "Histogram":

            fig = px.histogram(
                filtered_df,
                x=selected_parameter,
                nbins=40,
                color=(
                    selected_group
                    if selected_group != "None"
                    else None
                ),
                marginal="box",
                title=f"Distribution of {selected_parameter}"
            )

        elif chart_type == "Box Plot":

            if selected_group != "None":

                fig = px.box(
                    filtered_df,
                    x=selected_group,
                    y=selected_parameter,
                    color=selected_group,
                    points="outliers",
                    title=f"{selected_parameter} by {selected_group}"
                )

            else:

                fig = px.box(
                    filtered_df,
                    y=selected_parameter,
                    points="outliers",
                    title=f"Box Plot of {selected_parameter}"
                )

        elif chart_type == "Violin Plot":

            if selected_group != "None":

                fig = px.violin(
                    filtered_df,
                    x=selected_group,
                    y=selected_parameter,
                    color=selected_group,
                    box=True,
                    points="outliers",
                    title=f"{selected_parameter} by {selected_group}"
                )

            else:

                fig = px.violin(
                    filtered_df,
                    y=selected_parameter,
                    box=True,
                    points="outliers",
                    title=f"Violin Plot of {selected_parameter}"
                )

        elif chart_type == "Density Plot":

            fig = px.histogram(
                filtered_df,
                x=selected_parameter,
                color=(
                    selected_group
                    if selected_group != "None"
                    else None
                ),
                histnorm="probability density",
                marginal="rug",
                title=f"Density of {selected_parameter}"
            )

        elif chart_type == "Scatter Plot":

            scatter_options = [
                col for col in numeric_parameters
                if col != selected_parameter
            ]

            if scatter_options:

                scatter_y = st.selectbox(
                    "Select Y-Axis Parameter",
                    scatter_options
                )

                fig = px.scatter(
                    filtered_df,
                    x=selected_parameter,
                    y=scatter_y,
                    color=(
                        selected_group
                        if selected_group != "None"
                        else None
                    ),
                    hover_data=[
                        c for c in [
                            "neighbourhood",
                            "host_name",
                            "room_type"
                        ]
                        if c in filtered_df.columns
                    ],
                    title=f"{selected_parameter} vs {scatter_y}",
                    opacity=0.65
                )

            else:

                fig = px.histogram(
                    filtered_df,
                    x=selected_parameter,
                    title=f"Distribution of {selected_parameter}"
                )

        elif chart_type == "Bar Chart":

            if selected_group != "None":

                grouped_data = (
                    filtered_df.groupby(selected_group)
                    [selected_parameter]
                    .mean()
                    .sort_values(ascending=False)
                    .reset_index()
                )

                fig = px.bar(
                    grouped_data,
                    x=selected_group,
                    y=selected_parameter,
                    color=selected_parameter,
                    text_auto=".2f",
                    title=f"Average {selected_parameter} by {selected_group}",
                    color_continuous_scale="Viridis"
                )

            else:

                fig = px.histogram(
                    filtered_df,
                    x=selected_parameter,
                    title=f"Distribution of {selected_parameter}"
                )

        make_chart(fig, height=550)

        # Top 10 values
        if selected_group != "None":

            st.markdown("### 📊 Group Summary")

            group_summary = (
                filtered_df.groupby(selected_group)
                [selected_parameter]
                .agg(["mean", "median", "count"])
                .reset_index()
                .sort_values("mean", ascending=False)
            )

            group_summary.columns = [
                selected_group,
                "Average",
                "Median",
                "Count"
            ]

            st.dataframe(
                group_summary,
                use_container_width=True
            )

    else:

        st.warning("No numeric parameters available.")

# ============================================================
# TAB 3: LOCATION ANALYSIS
# ============================================================

with tab3:

    st.markdown("## 📍 Location Analysis")

    col1, col2 = st.columns(2)

    with col1:

        if available("neighbourhood_group"):

            location_counts = (
                filtered_df["neighbourhood_group"]
                .value_counts()
                .reset_index()
            )

            location_counts.columns = [
                "Location",
                "Listings"
            ]

            fig = px.pie(
                location_counts,
                names="Location",
                values="Listings",
                hole=0.45,
                title="Listing Distribution by Group"
            )

            make_chart(fig)

    with col2:

        if available("neighbourhood"):

            top_neighbourhoods = (
                filtered_df["neighbourhood"]
                .value_counts()
                .head(10)
                .reset_index()
            )

            top_neighbourhoods.columns = [
                "Neighbourhood",
                "Listings"
            ]

            fig = px.bar(
                top_neighbourhoods,
                x="Listings",
                y="Neighbourhood",
                orientation="h",
                color="Listings",
                text="Listings",
                title="Top 10 Neighbourhoods",
                color_continuous_scale="Viridis"
            )

            fig.update_layout(
                yaxis=dict(categoryorder="total ascending")
            )

            make_chart(fig)

    # Average price by location
    if available("price") and available("neighbourhood_group"):

        location_price = (
            filtered_df.groupby("neighbourhood_group")
            ["price"]
            .mean()
            .reset_index()
            .sort_values("price", ascending=False)
        )

        fig = px.bar(
            location_price,
            x="neighbourhood_group",
            y="price",
            color="price",
            text_auto=".2f",
            title="Average Price by Neighbourhood Group",
            color_continuous_scale="Plasma"
        )

        make_chart(fig)

    # Listings and price by neighbourhood
    if available("price") and available("neighbourhood"):

        neighbourhood_summary = (
            filtered_df.groupby("neighbourhood")
            .agg(
                Listings=("price", "count"),
                Average_Price=("price", "mean")
            )
            .nlargest(15, "Listings")
            .reset_index()
        )

        fig = px.scatter(
            neighbourhood_summary,
            x="Listings",
            y="Average_Price",
            size="Listings",
            color="neighbourhood",
            hover_name="neighbourhood",
            title="Neighbourhood: Listings vs Average Price"
        )

        make_chart(fig)

# ============================================================
# TAB 4: PRICE ANALYSIS
# ============================================================

with tab4:

    st.markdown("## 💰 Price Analysis")

    col1, col2 = st.columns(2)

    with col1:

        if available("price"):

            fig = px.histogram(
                filtered_df,
                x="price",
                nbins=50,
                marginal="box",
                title="Price Distribution",
                color_discrete_sequence=["#636EFA"]
            )

            make_chart(fig)

    with col2:

        if available("price") and available("room_type"):

            room_price = (
                filtered_df.groupby("room_type")
                ["price"]
                .mean()
                .reset_index()
                .sort_values("price", ascending=False)
            )

            fig = px.bar(
                room_price,
                x="room_type",
                y="price",
                color="room_type",
                text_auto=".2f",
                title="Average Price by Room Type"
            )

            make_chart(fig)

    if available("price") and available("neighbourhood"):

        neighbourhood_price = (
            filtered_df.groupby("neighbourhood")
            ["price"]
            .mean()
            .nlargest(10)
            .reset_index()
        )

        fig = px.bar(
            neighbourhood_price,
            x="price",
            y="neighbourhood",
            orientation="h",
            color="price",
            text_auto=".2f",
            title="Top 10 Expensive Neighbourhoods"
        )

        fig.update_layout(
            yaxis=dict(categoryorder="total ascending")
        )

        make_chart(fig)

    if available("price") and available("service_fee"):

        fig = px.scatter(
            filtered_df,
            x="price",
            y="service_fee",
            color=(
                "room_type"
                if available("room_type")
                else None
            ),
            title="Price vs Service Fee",
            opacity=0.6
        )

        make_chart(fig)

# ============================================================
# TAB 5: HOSTS & REVIEWS
# ============================================================

with tab5:

    st.markdown("## 👤 Host & Review Analysis")

    col1, col2 = st.columns(2)

    with col1:

        if available("host_name"):

            top_hosts = (
                filtered_df["host_name"]
                .value_counts()
                .head(10)
                .reset_index()
            )

            top_hosts.columns = ["Host", "Listings"]

            fig = px.bar(
                top_hosts,
                x="Listings",
                y="Host",
                orientation="h",
                color="Listings",
                title="Top 10 Hosts by Listings",
                color_continuous_scale="Blues"
            )

            fig.update_layout(
                yaxis=dict(categoryorder="total ascending")
            )

            make_chart(fig)

    with col2:

        if available("host_name") and available("number_of_reviews"):

            host_reviews = (
                filtered_df.groupby("host_name")
                ["number_of_reviews"]
                .sum()
                .nlargest(10)
                .reset_index()
            )

            fig = px.bar(
                host_reviews,
                x="host_name",
                y="number_of_reviews",
                color="number_of_reviews",
                title="Top Hosts by Reviews"
            )

            make_chart(fig)

    if available("room_type") and available("number_of_reviews"):

        room_reviews = (
            filtered_df.groupby("room_type")
            ["number_of_reviews"]
            .mean()
            .reset_index()
        )

        fig = px.bar(
            room_reviews,
            x="room_type",
            y="number_of_reviews",
            color="room_type",
            title="Average Reviews by Room Type"
        )

        make_chart(fig)

    if available("neighbourhood") and available("number_of_reviews"):

        neighbourhood_reviews = (
            filtered_df.groupby("neighbourhood")
            ["number_of_reviews"]
            .sum()
            .nlargest(10)
            .reset_index()
        )

        fig = px.bar(
            neighbourhood_reviews,
            x="number_of_reviews",
            y="neighbourhood",
            orientation="h",
            color="number_of_reviews",
            title="Top Neighbourhoods by Reviews"
        )

        fig.update_layout(
            yaxis=dict(categoryorder="total ascending")
        )

        make_chart(fig)

    # Verification comparison
    if (
        available("host_identity_verified")
        and available("review_rate_number")
    ):

        verified_rating = (
            filtered_df.groupby("host_identity_verified")
            ["review_rate_number"]
            .mean()
            .reset_index()
        )

        fig = px.bar(
            verified_rating,
            x="host_identity_verified",
            y="review_rate_number",
            color="host_identity_verified",
            text_auto=".2f",
            title="Host Verification vs Average Rating"
        )

        make_chart(fig)

# ============================================================
# TAB 6: DATASET
# ============================================================

with tab6:

    st.markdown("## 📋 Dataset Explorer")

    st.write(
        "Explore filtered Airbnb data and download it."
    )

    st.dataframe(
        filtered_df,
        use_container_width=True,
        height=500
    )

    st.markdown("### 📥 Download Data")

    csv_data = filtered_df.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        label="Download Filtered CSV",
        data=csv_data,
        file_name="airbnb_filtered_data.csv",
        mime="text/csv"
    )

    st.markdown("### 📌 Dataset Information")

    col1, col2, col3 = st.columns(3)

    col1.metric("Rows", f"{filtered_df.shape[0]:,}")
    col2.metric("Columns", f"{filtered_df.shape[1]:,}")
    col3.metric(
        "Missing Values",
        f"{filtered_df.isnull().sum().sum():,}"
    )

    st.markdown("### Missing Values")

    missing_data = (
        filtered_df.isnull()
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )

    missing_data.columns = [
        "Column",
        "Missing Values"
    ]

    st.dataframe(
        missing_data,
        use_container_width=True
    )

# ============================================================
# 10. FOOTER
# ============================================================

st.markdown("---")

st.markdown("""
<div style="text-align:center; color:#718096; padding:10px;">
    🏡 Airbnb Insights Dashboard<br>
    Built with Python • Streamlit • Plotly
</div>
""", unsafe_allow_html=True)

st.success("Dashboard Loaded Successfully! 🎉")

       
       
        



          
  

 
           

           


       
  
          
           
      
 
