
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Airbnb Analytics Dashboard",
    page_icon="🏠",
    layout="wide"
)

# ---------------- PAGE DESIGN ----------------

st.markdown("""
<style>
.stApp {
    background-color: #F5F7FB;
}
[data-testid="stMetric"] {
    background: white;
    padding: 18px;
    border-radius: 14px;
    border: 1px solid #E5E7EB;
}
h1 {
    color: #1E293B;
}
</style>
""", unsafe_allow_html=True)

st.title("🏠 Airbnb Analytics Dashboard")
st.markdown("### Explore listing, pricing, host, availability and review insights")

# ---------------- FILE UPLOAD ----------------

uploaded_file = st.sidebar.file_uploader(
    "📁 Upload Airbnb Dataset",
    type=["csv"]
)

if uploaded_file is None:
    st.info("👈 Upload your Airbnb CSV file from the sidebar to start.")
    st.stop()

@st.cache_data
def load_data(file):
    data = pd.read_csv(file, low_memory=False)

    # Rename columns
    data.columns = data.columns.str.strip()

    data = data.rename(columns={
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
        "calculated host listings count":
            "calculated_host_listings_count",
        "availability 365": "availability_365"
    })

    # Remove unnecessary columns if present
    data = data.drop(
        columns=["id", "lat", "long", "country code", "house_rules"],
        errors="ignore"
    )

    # Clean numeric columns
    numeric_cols = [
        "price",
        "service_fee",
        "minimum_nights",
        "number_of_reviews",
        "reviews_per_month",
        "review_rate_number",
        "calculated_host_listings_count",
        "availability_365",
        "Construction_year"
    ]

    for col in numeric_cols:
        if col in data.columns:
            data[col] = (
                data[col]
                .astype(str)
                .str.replace(r"[$,]", "", regex=True)
            )
            data[col] = pd.to_numeric(data[col], errors="coerce")

    # Clean text columns
    text_cols = [
        "NAME",
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

    for col in text_cols:
        if col in data.columns:
            data[col] = data[col].fillna("Unknown").astype(str)

    # Standardize neighbourhood group
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

        data["Year"] = data["last_review"].dt.year
        data["Month"] = data["last_review"].dt.month_name()

    return data


df = load_data(uploaded_file)

# ---------------- SIDEBAR FILTERS ----------------

st.sidebar.header("🎛️ Dashboard Filters")

filtered_df = df.copy()

if "neighbourhood_group" in df.columns:
    groups = sorted(df["neighbourhood_group"].dropna().unique())

    selected_groups = st.sidebar.multiselect(
        "Neighbourhood Group",
        groups,
        default=groups
    )

    filtered_df = filtered_df[
        filtered_df["neighbourhood_group"].isin(selected_groups)
    ]

if "room_type" in df.columns:
    rooms = sorted(df["room_type"].dropna().unique())

    selected_rooms = st.sidebar.multiselect(
        "Room Type",
        rooms,
        default=rooms
    )

    filtered_df = filtered_df[
        filtered_df["room_type"].isin(selected_rooms)
    ]

if "host_identity_verified" in df.columns:
    verified = sorted(
        df["host_identity_verified"].dropna().unique()
    )

    selected_verified = st.sidebar.multiselect(
        "Host Verification",
        verified,
        default=verified
    )

    filtered_df = filtered_df[
        filtered_df["host_identity_verified"].isin(selected_verified)
    ]

if "cancellation_policy" in df.columns:
    policies = sorted(
        df["cancellation_policy"].dropna().unique()
    )

    selected_policy = st.sidebar.multiselect(
        "Cancellation Policy",
        policies,
        default=policies
    )

    filtered_df = filtered_df[
        filtered_df["cancellation_policy"].isin(selected_policy)
    ]

st.sidebar.markdown("---")

st.sidebar.metric(
    "Filtered Records",
    f"{len(filtered_df):,}"
)

# ---------------- KPI CARDS ----------------

total_listings = len(filtered_df)

avg_price = (
    filtered_df["price"].mean()
    if "price" in filtered_df.columns else 0
)

avg_availability = (
    filtered_df["availability_365"].mean()
    if "availability_365" in filtered_df.columns else 0
)

total_hosts = (
    filtered_df["host_id"].nunique()
    if "host_id" in filtered_df.columns else 0
)

total_reviews = (
    filtered_df["number_of_reviews"].sum()
    if "number_of_reviews" in filtered_df.columns else 0
)

c1, c2, c3, c4, c5 = st.columns(5)

c1.metric("🏘️ Total Listings", f"{total_listings:,}")
c2.metric("💰 Average Price", f"${avg_price:,.2f}")
c3.metric("📅 Avg Availability", f"{avg_availability:,.1f} days")
c4.metric("👤 Total Hosts", f"{total_hosts:,}")
c5.metric("⭐ Total Reviews", f"{total_reviews:,.0f}")

st.markdown("---")

# ---------------- DROPDOWN PARAMETER ----------------

st.subheader("🔍 Explore Dataset")

available_parameters = [
    col for col in [
        "price",
        "service_fee",
        "minimum_nights",
        "number_of_reviews",
        "reviews_per_month",
        "review_rate_number",
        "availability_365",
        "calculated_host_listings_count",
        "Construction_year"
    ]
    if col in filtered_df.columns
]

parameter = st.selectbox(
    "Select Parameter to Explore",
    available_parameters
)

col1, col2 = st.columns(2)

with col1:
    fig = px.histogram(
        filtered_df,
        x=parameter,
        nbins=40,
        marginal="box",
        title=f"Distribution of {parameter}",
        color_discrete_sequence=["#636EFA"]
    )

    fig.update_layout(
        template="plotly_white",
        height=450
    )

    st.plotly_chart(fig, use_container_width=True)

with col2:
    if "room_type" in filtered_df.columns:
        parameter_room = filtered_df.groupby(
            "room_type", as_index=False
        )[parameter].mean()

        fig = px.bar(
            parameter_room,
            x="room_type",
            y=parameter,
            color="room_type",
            title=f"Average {parameter} by Room Type",
            text_auto=".2f"
        )

        fig.update_layout(
            template="plotly_white",
            height=450
        )

        st.plotly_chart(fig, use_container_width=True)

# ---------------- LOCATION ANALYSIS ----------------

st.markdown("---")
st.header("📍 Location & Listings Analysis")

col1, col2 = st.columns(2)

if "neighbourhood_group" in filtered_df.columns:

    with col1:
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

        st.plotly_chart(fig, use_container_width=True)

if "neighbourhood" in filtered_df.columns:

    with col2:
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
            title="Top 10 Neighbourhoods by Listings",
            text="Listings",
            color_continuous_scale="Viridis"
        )

        fig.update_layout(
            yaxis={"categoryorder": "total ascending"},
            template="plotly_white"
        )

        st.plotly_chart(fig, use_container_width=True)

# ---------------- PRICE ANALYSIS ----------------

st.markdown("---")
st.header("💰 Pricing Analysis")

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

        fig.update_layout(template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        if "neighbourhood_group" in filtered_df.columns:

            neighbourhood_price = (
                filtered_df.groupby("neighbourhood_group")
                ["price"].mean()
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

            fig.update_layout(template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)

    if "room_type" in filtered_df.columns:

        room_price = (
            filtered_df.groupby("room_type")["price"]
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

        st.plotly_chart(fig, use_container_width=True)

# ---------------- ROOM TYPE ----------------

st.markdown("---")
st.header("🛏️ Room Type Analysis")

if "room_type" in filtered_df.columns:

    room_count = (
        filtered_df["room_type"]
        .value_counts()
        .reset_index()
    )

    room_count.columns = ["Room Type", "Listings"]

    fig = px.pie(
        room_count,
        names="Room Type",
        values="Listings",
        hole=0.5,
        title="Room Type Distribution",
        color_discrete_sequence=px.colors.qualitative.Set2
    )

    st.plotly_chart(fig, use_container_width=True)

# ---------------- AVAILABILITY ----------------

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

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        if "neighbourhood_group" in filtered_df.columns:

            availability_group = (
                filtered_df.groupby("neighbourhood_group")
                ["availability_365"].mean()
                .reset_index()
            )

            fig = px.bar(
                availability_group,
                x="neighbourhood_group",
                y="availability_365",
                color="neighbourhood_group",
                title="Average Availability by Group",
                text_auto=".2f"
            )

            st.plotly_chart(fig, use_container_width=True)

if "Month" in filtered_df.columns:

    monthly_availability = (
        filtered_df.groupby("Month")["availability_365"]
        .mean()
        .reset_index()
    )

    month_order = [
        "January", "February", "March", "April",
        "May", "June", "July", "August",
        "September", "October", "November", "December"
    ]

    monthly_availability["Month"] = pd.Categorical(
        monthly_availability["Month"],
        categories=month_order,
        ordered=True
    )

    monthly_availability = monthly_availability.sort_values("Month")

    fig = px.line(
        monthly_availability,
        x="Month",
        y="availability_365",
        markers=True,
        title="Average Availability by Review Month"
    )

    fig.update_layout(template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)

# ---------------- HOST ANALYSIS ----------------

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
            yaxis={"categoryorder": "total ascending"}
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        host_reviews = (
            filtered_df.groupby("host_name")
            ["number_of_reviews"].sum()
            .nlargest(10)
            .reset_index()
        )

        host_reviews.columns = ["Host", "Reviews"]

        fig = px.bar(
            host_reviews,
            x="Host",
            y="Reviews",
            title="Top Hosts by Total Reviews",
            color="Reviews"
        )

        st.plotly_chart(fig, use_container_width=True)

if "host_identity_verified" in filtered_df.columns:

    verified_data = (
        filtered_df.groupby("host_identity_verified")
        [["price", "review_rate_number"]]
        .mean()
        .reset_index()
    )

    col1, col2 = st.columns(2)

    with col1:
        fig = px.bar(
            verified_data,
            x="host_identity_verified",
            y="price",
            color="host_identity_verified",
            title="Verified Hosts vs Average Price"
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.bar(
            verified_data,
            x="host_identity_verified",
            y="review_rate_number",
            color="host_identity_verified",
            title="Verified Hosts vs Average Rating"
        )

        st.plotly_chart(fig, use_container_width=True)

# ---------------- CUSTOMER PREFERENCES ----------------

st.markdown("---")
st.header("⭐ Customer Preferences")

col1, col2 = st.columns(2)

if "number_of_reviews" in filtered_df.columns:

    with col1:
        room_reviews = (
            filtered_df.groupby("room_type")
            ["number_of_reviews"].mean()
            .reset_index()
        )

        fig = px.bar(
            room_reviews,
            x="room_type",
            y="number_of_reviews",
            color="room_type",
            title="Average Reviews by Room Type"
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        if "neighbourhood" in filtered_df.columns:

            top_reviews = (
                filtered_df.groupby("neighbourhood")
                ["number_of_reviews"].sum()
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
                yaxis={"categoryorder": "total ascending"}
            )

            st.plotly_chart(fig, use_container_width=True)

# ---------------- CORRELATION ----------------

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
    c for c in correlation_columns
    if c in filtered_df.columns
]

if len(correlation_columns) > 1:

    corr = filtered_df[correlation_columns].corr()

    fig = px.imshow(
        corr,
        text_auto=".2f",
        color_continuous_scale="RdBu",
        zmin=-1,
        zmax=1,
        title="Correlation Heatmap"
    )

    st.plotly_chart(fig, use_container_width=True)

# ---------------- PRICE OUTLIERS ----------------

st.markdown("---")
st.header("🚨 Outlier Analysis")

if "price" in filtered_df.columns:

    col1, col2 = st.columns(2)

    with col1:
        fig = px.box(
            filtered_df,
            y="price",
            title="Price Outlier Detection"
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        expensive = (
            filtered_df.nlargest(10, "price")
        )

        display_columns = [
            c for c in [
                "NAME",
                "host_name",
                "neighbourhood",
                "room_type",
                "price"
            ]
            if c in expensive.columns
        ]

        st.subheader("Top 10 Expensive Listings")

        st.dataframe(
            expensive[display_columns],
            use_container_width=True
        )

# ---------------- DATA TABLE ----------------

st.markdown("---")
st.header("📄 Filtered Dataset")

st.dataframe(
    filtered_df,
    use_container_width=True,
    height=400
)

csv = filtered_df.to_csv(index=False).encode("utf-8")

st.download_button(
    "📥 Download Filtered CSV",
    csv,
    "filtered_airbnb.csv",
    "text/csv"
)

st.success("Dashboard Loaded Successfully! 🎉")
