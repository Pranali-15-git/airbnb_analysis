
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Airbnb Analytics Dashboard",
    page_icon="🏠",
    layout="wide"
)

# =========================================================
# CUSTOM DESIGN
# =========================================================

st.markdown("""
<style>

.stApp {
    background-color: #F4F7FB;
}

h1 {
    color: #172554;
}

h2, h3 {
    color: #1E293B;
}

[data-testid="stMetric"] {
    background-color: white;
    border: 1px solid #E2E8F0;
    padding: 18px;
    border-radius: 15px;
    box-shadow: 0px 2px 6px rgba(0,0,0,0.04);
}

[data-testid="stSidebar"] {
    background-color: #EAF0F8;
}

div[data-testid="stPlotlyChart"] {
    background-color: white;
    border-radius: 12px;
    padding: 8px;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# TITLE
# =========================================================

st.title("🏠 Airbnb Analytics Dashboard")

st.markdown(
    "Interactive dashboard for exploring Airbnb listings, "
    "pricing, neighbourhoods, hosts, reviews and availability."
)

# =========================================================
# FILE UPLOAD
# =========================================================

st.sidebar.header("📂 Upload Dataset")

uploaded_file = st.sidebar.file_uploader(
    "Upload Airbnb CSV File",
    type=["csv"]
)

if uploaded_file is None:
    st.info("👈 Upload your Airbnb CSV file to view the dashboard.")
    st.stop()

# =========================================================
# LOAD DATA
# =========================================================

@st.cache_data
def load_data(file):

    df = pd.read_csv(file, low_memory=False)

    # Standardize column names
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )

    # Remove unnecessary columns
    df = df.drop(
        columns=[
            "id",
            "lat",
            "long",
            "country_code",
            "house_rules"
        ],
        errors="ignore"
    )

    # Convert numeric columns
    numeric_columns = [
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

        if col in df.columns:

            df[col] = (
                df[col]
                .astype(str)
                .str.replace(r"[$,]", "", regex=True)
            )

            df[col] = pd.to_numeric(
                df[col],
                errors="coerce"
            )

    # Clean text columns
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

        if col in df.columns:

            df[col] = (
                df[col]
                .fillna("Unknown")
                .astype(str)
                .str.strip()
            )

    # Fix neighbourhood group spelling
    if "neighbourhood_group" in df.columns:

        df["neighbourhood_group"] = (
            df["neighbourhood_group"]
            .replace({
                "brookln": "Brooklyn",
                "manhatan": "Manhattan"
            })
        )

    # Convert review date
    if "last_review" in df.columns:

        df["last_review"] = pd.to_datetime(
            df["last_review"],
            errors="coerce"
        )

        df["review_year"] = df["last_review"].dt.year

        df["review_month"] = (
            df["last_review"].dt.month_name()
        )

    return df


df = load_data(uploaded_file)

# =========================================================
# SIDEBAR FILTERS
# =========================================================

st.sidebar.markdown("---")
st.sidebar.header("🎛️ Filters")

filtered_df = df.copy()

# Neighbourhood group
if "neighbourhood_group" in df.columns:

    group_options = sorted(
        df["neighbourhood_group"].dropna().unique()
    )

    selected_groups = st.sidebar.multiselect(
        "Neighbourhood Group",
        group_options,
        default=group_options
    )

    filtered_df = filtered_df[
        filtered_df["neighbourhood_group"].isin(
            selected_groups
        )
    ]

# Room type
if "room_type" in df.columns:

    room_options = sorted(
        df["room_type"].dropna().unique()
    )

    selected_rooms = st.sidebar.multiselect(
        "Room Type",
        room_options,
        default=room_options
    )

    filtered_df = filtered_df[
        filtered_df["room_type"].isin(selected_rooms)
    ]

# Host verification
if "host_identity_verified" in df.columns:

    verification_options = sorted(
        df["host_identity_verified"].dropna().unique()
    )

    selected_verification = st.sidebar.multiselect(
        "Host Verification",
        verification_options,
        default=verification_options
    )

    filtered_df = filtered_df[
        filtered_df["host_identity_verified"].isin(
            selected_verification
        )
    ]

# Cancellation policy
if "cancellation_policy" in df.columns:

    cancellation_options = sorted(
        df["cancellation_policy"].dropna().unique()
    )

    selected_cancellation = st.sidebar.multiselect(
        "Cancellation Policy",
        cancellation_options,
        default=cancellation_options
    )

    filtered_df = filtered_df[
        filtered_df["cancellation_policy"].isin(
            selected_cancellation
        )
    ]

st.sidebar.markdown("---")

st.sidebar.metric(
    "Filtered Listings",
    f"{len(filtered_df):,}"
)

# =========================================================
# KPI CARDS
# =========================================================

total_listings = len(filtered_df)

avg_price = (
    filtered_df["price"].mean()
    if "price" in filtered_df.columns
    else 0
)

avg_availability = (
    filtered_df["availability_365"].mean()
    if "availability_365" in filtered_df.columns
    else 0
)

total_hosts = (
    filtered_df["host_id"].nunique()
    if "host_id" in filtered_df.columns
    else 0
)

total_reviews = (
    filtered_df["number_of_reviews"].sum()
    if "number_of_reviews" in filtered_df.columns
    else 0
)

c1, c2, c3, c4, c5 = st.columns(5)

c1.metric("🏘️ Total Listings", f"{total_listings:,}")
c2.metric("💰 Average Price", f"${avg_price:,.2f}")
c3.metric("📅 Avg Availability", f"{avg_availability:,.1f} days")
c4.metric("👤 Total Hosts", f"{total_hosts:,}")
c5.metric("⭐ Total Reviews", f"{total_reviews:,.0f}")

st.markdown("---")

# =========================================================
# DYNAMIC PARAMETER DROPDOWN
# =========================================================

st.header("📊 Dynamic Parameter Analysis")

numeric_parameters = [
    col for col in filtered_df.select_dtypes(
        include=np.number
    ).columns
    if filtered_df[col].nunique() > 1
]

if len(numeric_parameters) == 0:
    st.warning("No numeric columns available for analysis.")
    st.stop()

selected_parameter = st.selectbox(
    "🎯 Select Parameter",
    numeric_parameters,
    index=(
        numeric_parameters.index("price")
        if "price" in numeric_parameters
        else 0
    )
)

st.markdown(
    f"### Analysis for: **{selected_parameter.replace('_', ' ').title()}**"
)

parameter_data = filtered_df[
    selected_parameter
].dropna()

# =========================================================
# DYNAMIC KPI
# =========================================================

p1, p2, p3, p4 = st.columns(4)

p1.metric(
    f"Average {selected_parameter.title()}",
    f"{parameter_data.mean():,.2f}"
)

p2.metric(
    f"Median {selected_parameter.title()}",
    f"{parameter_data.median():,.2f}"
)

p3.metric(
    f"Maximum {selected_parameter.title()}",
    f"{parameter_data.max():,.2f}"
)

p4.metric(
    f"Minimum {selected_parameter.title()}",
    f"{parameter_data.min():,.2f}"
)

# =========================================================
# DYNAMIC GRAPHS
# =========================================================

col1, col2 = st.columns(2)

# Distribution graph
with col1:

    fig = px.histogram(
        filtered_df,
        x=selected_parameter,
        nbins=40,
        marginal="box",
        title=f"{selected_parameter.title()} Distribution",
        color_discrete_sequence=["#636EFA"]
    )

    fig.update_layout(
        template="plotly_white",
        height=450
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

# Parameter by room type
with col2:

    if "room_type" in filtered_df.columns:

        room_parameter = (
            filtered_df.groupby("room_type")
            [selected_parameter]
            .mean()
            .reset_index()
            .sort_values(
                selected_parameter,
                ascending=False
            )
        )

        fig = px.bar(
            room_parameter,
            x="room_type",
            y=selected_parameter,
            color="room_type",
            text_auto=".2f",
            title=f"Average {selected_parameter.title()} by Room Type"
        )

        fig.update_layout(
            template="plotly_white",
            height=450
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

# Parameter by neighbourhood group
col1, col2 = st.columns(2)

with col1:

    if "neighbourhood_group" in filtered_df.columns:

        group_parameter = (
            filtered_df.groupby("neighbourhood_group")
            [selected_parameter]
            .mean()
            .reset_index()
            .sort_values(
                selected_parameter,
                ascending=False
            )
        )

        fig = px.bar(
            group_parameter,
            x="neighbourhood_group",
            y=selected_parameter,
            color=selected_parameter,
            text_auto=".2f",
            title=f"Average {selected_parameter.title()} by Neighbourhood Group",
            color_continuous_scale="Viridis"
        )

        fig.update_layout(
            template="plotly_white",
            height=450
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

with col2:

    if "neighbourhood" in filtered_df.columns:

        neighbourhood_parameter = (
            filtered_df.groupby("neighbourhood")
            [selected_parameter]
            .mean()
            .nlargest(10)
            .reset_index()
        )

        fig = px.bar(
            neighbourhood_parameter,
            x=selected_parameter,
            y="neighbourhood",
            orientation="h",
            color=selected_parameter,
            text_auto=".2f",
            title=f"Top 10 Neighbourhoods by {selected_parameter.title()}",
            color_continuous_scale="Plasma"
        )

        fig.update_layout(
            template="plotly_white",
            height=450,
            yaxis={
                "categoryorder": "total ascending"
            }
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

# =========================================================
# PARAMETER VS REVIEWS SCATTER PLOT
# =========================================================

if "number_of_reviews" in filtered_df.columns:

    st.subheader("📈 Parameter vs Number of Reviews")

    fig = px.scatter(
        filtered_df,
        x=selected_parameter,
        y="number_of_reviews",
        color=(
            "room_type"
            if "room_type" in filtered_df.columns
            else None
        ),
        hover_data=[
            c for c in [
                "neighbourhood",
                "host_name",
                "price"
            ]
            if c in filtered_df.columns
        ],
        title=f"{selected_parameter.title()} vs Number of Reviews",
        opacity=0.6
    )

    fig.update_layout(
        template="plotly_white",
        height=500
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

# =========================================================
# LOCATION ANALYSIS
# =========================================================

st.markdown("---")
st.header("📍 Location & Listings Analysis")

col1, col2 = st.columns(2)

# Listings by neighbourhood group
with col1:

    if "neighbourhood_group" in filtered_df.columns:

        group_count = (
            filtered_df["neighbourhood_group"]
            .value_counts()
            .reset_index()
        )

        group_count.columns = [
            "Neighbourhood Group",
            "Listings"
        ]

        fig = px.pie(
            group_count,
            names="Neighbourhood Group",
            values="Listings",
            hole=0.45,
            title="Listings by Neighbourhood Group"
        )

        fig.update_layout(
            template="plotly_white",
            height=450
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

# Top 10 neighbourhoods
with col2:

    if "neighbourhood" in filtered_df.columns:

        top_neighbourhood = (
            filtered_df["neighbourhood"]
            .value_counts()
            .head(10)
            .reset_index()
        )

        top_neighbourhood.columns = [
            "Neighbourhood",
            "Listings"
        ]

        fig = px.bar(
            top_neighbourhood,
            x="Listings",
            y="Neighbourhood",
            orientation="h",
            color="Listings",
            text="Listings",
            title="Top 10 Neighbourhoods by Listings",
            color_continuous_scale="Viridis"
        )

        fig.update_layout(
            template="plotly_white",
            height=450,
            yaxis={
                "categoryorder": "total ascending"
            }
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

# =========================================================
# PRICE ANALYSIS
# =========================================================

st.markdown("---")
st.header("💰 Price Analysis")

col1, col2 = st.columns(2)

if "price" in filtered_df.columns:

    with col1:

        fig = px.histogram(
            filtered_df,
            x="price",
            nbins=50,
            title="Price Distribution",
            color_discrete_sequence=["#00CC96"]
        )

        fig.update_layout(
            template="plotly_white",
            height=450
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    with col2:

        if "neighbourhood_group" in filtered_df.columns:

            neighbourhood_price = (
                filtered_df.groupby("neighbourhood_group")
                ["price"]
                .mean()
                .sort_values(ascending=False)
                .reset_index()
            )

            fig = px.bar(
                neighbourhood_price,
                x="neighbourhood_group",
                y="price",
                color="price",
                title="Average Price by Neighbourhood Group",
                text_auto=".2f",
                color_continuous_scale="Plasma"
            )

            fig.update_layout(
                template="plotly_white",
                height=450
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

    if "room_type" in filtered_df.columns:

        room_price = (
            filtered_df.groupby("room_type")
            ["price"]
            .mean()
            .reset_index()
        )

        fig = px.bar(
            room_price,
            x="room_type",
            y="price",
            color="room_type",
            title="Average Price by Room Type",
            text_auto=".2f"
        )

        fig.update_layout(
            template="plotly_white"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

# =========================================================
# ROOM TYPE ANALYSIS
# =========================================================

st.markdown("---")
st.header("🛏️ Room Type Analysis")

if "room_type" in filtered_df.columns:

    room_count = (
        filtered_df["room_type"]
        .value_counts()
        .reset_index()
    )

    room_count.columns = [
        "Room Type",
        "Listings"
    ]

    fig = px.pie(
        room_count,
        names="Room Type",
        values="Listings",
        hole=0.5,
        title="Room Type Distribution",
        color_discrete_sequence=px.colors.qualitative.Set2
    )

    fig.update_layout(
        template="plotly_white",
        height=450
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

# =========================================================
# AVAILABILITY ANALYSIS
# =========================================================

st.markdown("---")
st.header("📅 Availability Analysis")

col1, col2 = st.columns(2)

if "availability_365" in filtered_df.columns:

    with col1:

        fig = px.histogram(
            filtered_df,
            x="availability_365",
            nbins=40,
            title="Availability Days Distribution",
            color_discrete_sequence=["#AB63FA"]
        )

        fig.update_layout(
            template="plotly_white",
            height=450
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    with col2:

        if "neighbourhood_group" in filtered_df.columns:

            availability_group = (
                filtered_df.groupby("neighbourhood_group")
                ["availability_365"]
                .mean()
                .reset_index()
            )

            fig = px.bar(
                availability_group,
                x="neighbourhood_group",
                y="availability_365",
                color="neighbourhood_group",
                text_auto=".2f",
                title="Average Availability by Group"
            )

            fig.update_layout(
                template="plotly_white",
                height=450
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

# Review month availability
if (
    "review_month" in filtered_df.columns
    and "availability_365" in filtered_df.columns
):

    monthly_availability = (
        filtered_df.groupby("review_month")
        ["availability_365"]
        .mean()
        .reset_index()
    )

    month_order = [
        "January", "February", "March", "April",
        "May", "June", "July", "August",
        "September", "October", "November", "December"
    ]

    monthly_availability["review_month"] = pd.Categorical(
        monthly_availability["review_month"],
        categories=month_order,
        ordered=True
    )

    monthly_availability = (
        monthly_availability.sort_values("review_month")
    )

    fig = px.line(
        monthly_availability,
        x="review_month",
        y="availability_365",
        markers=True,
        title="Average Availability by Review Month"
    )

    fig.update_layout(
        template="plotly_white"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

# =========================================================
# HOST ANALYSIS
# =========================================================

st.markdown("---")
st.header("👤 Host Analysis")

col1, col2 = st.columns(2)

if "host_name" in filtered_df.columns:

    with col1:

        top_hosts = (
            filtered_df["host_name"]
            .value_counts()
            .head(10)
            .reset_index()
        )

        top_hosts.columns = [
            "Host",
            "Listings"
        ]

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
            template="plotly_white",
            yaxis={
                "categoryorder": "total ascending"
            }
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    with col2:

        if "number_of_reviews" in filtered_df.columns:

            host_reviews = (
                filtered_df.groupby("host_name")
                ["number_of_reviews"]
                .sum()
                .nlargest(10)
                .reset_index()
            )

            host_reviews.columns = [
                "Host",
                "Reviews"
            ]

            fig = px.bar(
                host_reviews,
                x="Host",
                y="Reviews",
                color="Reviews",
                title="Top Hosts by Total Reviews"
            )

            fig.update_layout(
                template="plotly_white"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

# Host verification
if (
    "host_identity_verified" in filtered_df.columns
    and "price" in filtered_df.columns
):

    verified_data = (
        filtered_df.groupby("host_identity_verified")
        ["price"]
        .mean()
        .reset_index()
    )

    fig = px.bar(
        verified_data,
        x="host_identity_verified",
        y="price",
        color="host_identity_verified",
        title="Verified vs Non-Verified Hosts - Average Price",
        text_auto=".2f"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

# Ratings by verification
if (
    "host_identity_verified" in filtered_df.columns
    and "review_rate_number" in filtered_df.columns
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
        title="Host Verification vs Average Rating",
        text_auto=".2f"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

# =========================================================
# CUSTOMER PREFERENCES
# =========================================================

st.markdown("---")
st.header("⭐ Customer Preferences")

col1, col2 = st.columns(2)

if "number_of_reviews" in filtered_df.columns:

    with col1:

        if "room_type" in filtered_df.columns:

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

            st.plotly_chart(
                fig,
                use_container_width=True
            )

    with col2:

        if "neighbourhood" in filtered_df.columns:

            top_reviews = (
                filtered_df.groupby("neighbourhood")
                ["number_of_reviews"]
                .sum()
                .nlargest(10)
                .reset_index()
            )

            fig = px.bar(
                top_reviews,
                x="number_of_reviews",
                y="neighbourhood",
                orientation="h",
                color="number_of_reviews",
                title="Top Neighbourhoods by Reviews"
            )

            fig.update_layout(
                yaxis={
                    "categoryorder": "total ascending"
                }
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

# =========================================================
# CORRELATION ANALYSIS
# =========================================================

st.markdown("---")
st.header("📊 Correlation Analysis")

correlation_columns = [
    "price",
    "service_fee",
    "minimum_nights",
    "number_of_reviews",
    "reviews_per_month",
    "review_rate_number",
    "calculated_host_listings_count",
    "availability_365"
]

correlation_columns = [
    col for col in correlation_columns
    if col in filtered_df.columns
]

if len(correlation_columns) > 1:

    correlation = (
        filtered_df[correlation_columns]
        .corr()
    )

    fig = px.imshow(
        correlation,
        text_auto=".2f",
        color_continuous_scale="RdBu",
        zmin=-1,
        zmax=1,
        title="Correlation Heatmap"
    )

    fig.update_layout(
        template="plotly_white",
        height=600
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

# =========================================================
# OUTLIER ANALYSIS
# =========================================================

st.markdown("---")
st.header("🚨 Outlier Analysis")

if "price" in filtered_df.columns:

    col1, col2 = st.columns(2)

    with col1:

        fig = px.box(
            filtered_df,
            y="price",
            points="outliers",
            title="Price Outlier Detection"
        )

        fig.update_layout(
            template="plotly_white"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    with col2:

        expensive = (
            filtered_df
            .nlargest(10, "price")
        )

        display_columns = [
            col for col in [
                "name",
                "host_name",
                "neighbourhood",
                "room_type",
                "price"
            ]
            if col in expensive.columns
        ]

        st.subheader("Top 10 Expensive Listings")

        st.dataframe(
            expensive[display_columns],
            use_container_width=True
        )

# =========================================================
# DATA TABLE
# =========================================================

st.markdown("---")
st.header("📋 Dataset View")

st.dataframe(
    filtered_df,
    use_container_width=True,
    height=400
)

# =========================================================
# DOWNLOAD FILTERED DATA
# =========================================================

csv_data = filtered_df.to_csv(
    index=False
).encode("utf-8")

st.download_button(
    label="📥 Download Filtered Dataset",
    data=csv_data,
    file_name="filtered_airbnb_dataset.csv",
    mime="text/csv"
)

# =========================================================
# FOOTER
# =========================================================

st.markdown("---")

st.markdown(
    """
    <div style="text-align:center; color:gray;">
    🏠 Airbnb Analytics Dashboard | Built with Python, Streamlit & Plotly
    </div>
    """,
    unsafe_allow_html=True
)

st.success("Dashboard Loaded Successfully! 🎉")






        



          
  

 
           

           


       
  
          
           
      
 
