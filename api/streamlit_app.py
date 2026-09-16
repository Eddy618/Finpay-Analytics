import requests
import pandas as pd
import plotly.express as px
import streamlit as st


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="FinPay Analytics",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CONFIGURATION
# ============================================================

import os

API_URL = os.getenv(
    "API_URL",
    "http://127.0.0.1:8000",
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>
        .main-title {
            font-size: 2.4rem;
            font-weight: 700;
            margin-bottom: 0;
        }

        .subtitle {
            font-size: 1rem;
            color: #6b7280;
            margin-bottom: 1.5rem;
        }

        .section-title {
            font-size: 1.4rem;
            font-weight: 600;
            margin-top: 1rem;
        }

        div[data-testid="stMetric"] {
            padding: 12px;
            border-radius: 10px;
            border: 1px solid #e5e7eb;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# API HELPER
# ============================================================

@st.cache_data(ttl=60)
def fetch_api(endpoint: str):
    """Fetch data from the FastAPI backend."""

    try:
        response = requests.get(
            f"{API_URL}{endpoint}",
            timeout=15,
        )

        response.raise_for_status()

        return response.json()

    except requests.exceptions.ConnectionError:
        st.error(
            "Unable to connect to the FinPay API. "
            "Make sure FastAPI is running on port 8000."
        )
        return None

    except requests.exceptions.Timeout:
        st.error("The FinPay API request timed out.")
        return None

    except requests.exceptions.HTTPError as error:
        st.error(f"API returned an error: {error}")
        return None

    except requests.exceptions.RequestException as error:
        st.error(f"API request failed: {error}")
        return None


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="main-title">FinPay Analytics</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">'
    "Financial transaction intelligence, operations and risk monitoring"
    "</div>",
    unsafe_allow_html=True,
)


# ============================================================
# SIDEBAR NAVIGATION
# ============================================================

st.sidebar.title("FinPay")

page = st.sidebar.radio(
    "Navigation",
    [
        "Executive Overview",
        "Transactions",
        "Operations",
        "Anomalies",
        "Reconciliation",
        "Channels",
        "Partners",
    ],
)


# ============================================================
# EXECUTIVE OVERVIEW
# ============================================================

if page == "Executive Overview":

    st.header("Executive Overview")

    kpis = fetch_api("/kpis")

    if kpis:

        # ----------------------------------------------------
        # KPI CARDS
        # ----------------------------------------------------

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Total Transactions",
            f"{int(kpis['total_transactions']):,}",
        )

        col2.metric(
            "Transaction Value",
            f"₦{float(kpis['total_transaction_value']):,.2f}",
        )

        col3.metric(
            "Success Rate",
            f"{float(kpis['success_rate']):.2f}%",
        )

        col4.metric(
            "Successful Value",
            f"₦{float(kpis['successful_transaction_value']):,.2f}",
        )

        st.divider()

        # ----------------------------------------------------
        # STATUS SUMMARY
        # ----------------------------------------------------

        st.subheader("Transaction Status")

        status1, status2, status3, status4 = st.columns(4)

        status1.metric(
            "Successful",
            f"{int(kpis['successful_transactions']):,}",
        )

        status2.metric(
            "Failed",
            f"{int(kpis['failed_transactions']):,}",
        )

        status3.metric(
            "Pending",
            f"{int(kpis['pending_transactions']):,}",
        )

        status4.metric(
            "Refunded",
            f"{int(kpis['refunded_transactions']):,}",
        )

        st.divider()

        # ----------------------------------------------------
        # CHANNEL + PARTNER DATA
        # ----------------------------------------------------

        channels = fetch_api("/channels")
        partners = fetch_api("/partners")

        if channels:

            channel_df = pd.DataFrame(channels)

            st.subheader("Transaction Value by Channel")

            fig_channel = px.bar(
                channel_df,
                x="channel_name",
                y="total_transaction_value",
                title="Transaction Value by Channel",
            )

            fig_channel.update_layout(
                xaxis_title="Payment Channel",
                yaxis_title="Transaction Value",
            )

            st.plotly_chart(
                fig_channel,
                use_container_width=True,
            )

        if partners:

            partner_df = pd.DataFrame(partners)

            st.subheader("Transaction Value by Partner")

            fig_partner = px.bar(
                partner_df,
                x="partner_name",
                y="total_transaction_value",
                title="Transaction Value by Partner",
            )

            fig_partner.update_layout(
                xaxis_title="Partner",
                yaxis_title="Transaction Value",
            )

            st.plotly_chart(
                fig_partner,
                use_container_width=True,
            )


# ============================================================
# TRANSACTION EXPLORER
# ============================================================

elif page == "Transactions":

    st.header("Transaction Explorer")

    col1, col2 = st.columns(2)

    with col1:
        status = st.selectbox(
            "Transaction Status",
            [
                "All",
                "Successful",
                "Failed",
                "Pending",
                "Refunded",
            ],
        )

    with col2:
        transaction_type = st.selectbox(
            "Transaction Type",
            [
                "All",
                "Payment",
                "Transfer",
                "Withdrawal",
                "Refund",
            ],
        )

    limit = st.slider(
        "Records to display",
        min_value=10,
        max_value=1000,
        value=100,
        step=10,
    )

    endpoint = f"/transactions?limit={limit}"

    params = []

    if status != "All":
        params.append(
            f"status={status}"
        )

    if transaction_type != "All":
        params.append(
            f"transaction_type={transaction_type}"
        )

    if params:
        endpoint += "&" + "&".join(params)

    transactions = fetch_api(endpoint)

    if transactions:

        transaction_df = pd.DataFrame(
            transactions
        )

        st.metric(
            "Transactions Returned",
            f"{len(transaction_df):,}",
        )

        st.dataframe(
            transaction_df,
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# OPERATIONS
# ============================================================

elif page == "Operations":

    st.header("Operations Dashboard")

    channels = fetch_api("/channels")
    partners = fetch_api("/partners")

    if channels:

        channel_df = pd.DataFrame(channels)

        col1, col2 = st.columns(2)

        with col1:

            fig_volume = px.bar(
                channel_df,
                x="channel_name",
                y="total_transactions",
                title="Transactions by Channel",
            )

            st.plotly_chart(
                fig_volume,
                use_container_width=True,
            )

        with col2:

            fig_success = px.bar(
                channel_df,
                x="channel_name",
                y="success_rate",
                title="Success Rate by Channel",
            )

            st.plotly_chart(
                fig_success,
                use_container_width=True,
            )

    if partners:

        partner_df = pd.DataFrame(partners)

        col1, col2 = st.columns(2)

        with col1:

            fig_partner_volume = px.bar(
                partner_df,
                x="partner_name",
                y="total_transactions",
                title="Transactions by Partner",
            )

            st.plotly_chart(
                fig_partner_volume,
                use_container_width=True,
            )

        with col2:

            fig_partner_success = px.bar(
                partner_df,
                x="partner_name",
                y="success_rate",
                title="Success Rate by Partner",
            )

            st.plotly_chart(
                fig_partner_success,
                use_container_width=True,
            )


# ============================================================
# ANOMALIES
# ============================================================

elif page == "Anomalies":

    st.header("Risk & Anomaly Monitoring")

    anomalies = fetch_api(
        "/anomalies?limit=1000"
    )

    if anomalies:

        anomaly_df = pd.DataFrame(
            anomalies
        )

        # ----------------------------------------------------
        # SUMMARY
        # ----------------------------------------------------

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Investigation Records",
            f"{len(anomaly_df):,}",
        )

        if "amount" in anomaly_df.columns:

            total_value = anomaly_df["amount"].sum()

            col2.metric(
                "Anomaly Transaction Value",
                f"₦{total_value:,.2f}",
            )

        if "transaction_anomaly" in anomaly_df.columns:

            category_count = (
                anomaly_df["transaction_anomaly"]
                .nunique()
            )

            col3.metric(
                "Anomaly Categories",
                f"{category_count:,}",
            )

        st.divider()

        # ----------------------------------------------------
        # ANOMALY CATEGORY CHART
        # ----------------------------------------------------

        if "transaction_anomaly" in anomaly_df.columns:

            category_df = (
                anomaly_df
                .groupby(
                    "transaction_anomaly",
                    as_index=False
                )
                .size()
                .rename(
                    columns={
                        "size": "transaction_count"
                    }
                )
            )

            fig_anomaly = px.bar(
                category_df,
                x="transaction_anomaly",
                y="transaction_count",
                title="Anomalies by Category",
            )

            st.plotly_chart(
                fig_anomaly,
                use_container_width=True,
            )

        # ----------------------------------------------------
        # FILTER
        # ----------------------------------------------------

        if "transaction_anomaly" in anomaly_df.columns:

            categories = sorted(
                anomaly_df[
                    "transaction_anomaly"
                ]
                .dropna()
                .unique()
                .tolist()
            )

            selected_category = st.multiselect(
                "Filter anomaly category",
                categories,
                default=categories,
            )

            filtered_df = anomaly_df[
                anomaly_df[
                    "transaction_anomaly"
                ].isin(selected_category)
            ]

        else:

            filtered_df = anomaly_df

        # ----------------------------------------------------
        # INVESTIGATION TABLE
        # ----------------------------------------------------

        st.subheader(
            "Anomaly Investigation Queue"
        )

        st.dataframe(
            filtered_df,
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# RECONCILIATION
# ============================================================

elif page == "Reconciliation":

    st.header("Financial Reconciliation")

    reconciliation = fetch_api(
        "/reconciliation?limit=1000"
    )

    if reconciliation:

        reconciliation_df = pd.DataFrame(
            reconciliation
        )

        # ----------------------------------------------------
        # SUMMARY
        # ----------------------------------------------------

        st.metric(
            "Investigation Records",
            f"{len(reconciliation_df):,}",
        )

        if (
            "reconciliation_status"
            in reconciliation_df.columns
        ):

            summary_df = (
                reconciliation_df
                .groupby(
                    "reconciliation_status",
                    as_index=False
                )
                .size()
                .rename(
                    columns={
                        "size": "transaction_count"
                    }
                )
            )

            fig_reconciliation = px.pie(
                summary_df,
                names="reconciliation_status",
                values="transaction_count",
                title="Reconciliation Exceptions",
            )

            st.plotly_chart(
                fig_reconciliation,
                use_container_width=True,
            )

        # ----------------------------------------------------
        # FILTER
        # ----------------------------------------------------

        if (
            "reconciliation_status"
            in reconciliation_df.columns
        ):

            statuses = sorted(
                reconciliation_df[
                    "reconciliation_status"
                ]
                .dropna()
                .unique()
                .tolist()
            )

            selected_status = st.multiselect(
                "Reconciliation status",
                statuses,
                default=statuses,
            )

            filtered_df = reconciliation_df[
                reconciliation_df[
                    "reconciliation_status"
                ].isin(selected_status)
            ]

        else:

            filtered_df = reconciliation_df

        # ----------------------------------------------------
        # TABLE
        # ----------------------------------------------------

        st.subheader(
            "Reconciliation Investigation Queue"
        )

        st.dataframe(
            filtered_df,
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# CHANNELS
# ============================================================

elif page == "Channels":

    st.header("Payment Channel Performance")

    channels = fetch_api("/channels")

    if channels:

        channel_df = pd.DataFrame(channels)

        # ----------------------------------------------------
        # KPI SUMMARY
        # ----------------------------------------------------

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Channels",
            f"{len(channel_df):,}",
        )

        if "total_transactions" in channel_df:

            col2.metric(
                "Transactions",
                f"{int(channel_df['total_transactions'].sum()):,}",
            )

        if "total_transaction_value" in channel_df:

            col3.metric(
                "Total Value",
                f"₦{channel_df['total_transaction_value'].sum():,.2f}",
            )

        st.divider()

        # ----------------------------------------------------
        # TRANSACTION VALUE
        # ----------------------------------------------------

        fig_value = px.bar(
            channel_df,
            x="channel_name",
            y="total_transaction_value",
            title="Transaction Value by Channel",
        )

        st.plotly_chart(
            fig_value,
            use_container_width=True,
        )

        # ----------------------------------------------------
        # SUCCESS RATE
        # ----------------------------------------------------

        fig_success = px.bar(
            channel_df,
            x="channel_name",
            y="success_rate",
            title="Success Rate by Channel",
        )

        st.plotly_chart(
            fig_success,
            use_container_width=True,
        )

        st.dataframe(
            channel_df,
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# PARTNERS
# ============================================================

elif page == "Partners":

    st.header("Partner Performance")

    partners = fetch_api("/partners")

    if partners:

        partner_df = pd.DataFrame(
            partners
        )

        # ----------------------------------------------------
        # KPI SUMMARY
        # ----------------------------------------------------

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Partners",
            f"{len(partner_df):,}",
        )

        if "total_transactions" in partner_df:

            col2.metric(
                "Transactions",
                f"{int(partner_df['total_transactions'].sum()):,}",
            )

        if "total_transaction_value" in partner_df:

            col3.metric(
                "Total Value",
                f"₦{partner_df['total_transaction_value'].sum():,.2f}",
            )

        st.divider()

        # ----------------------------------------------------
        # TRANSACTION VALUE
        # ----------------------------------------------------

        fig_value = px.bar(
            partner_df,
            x="partner_name",
            y="total_transaction_value",
            title="Transaction Value by Partner",
        )

        st.plotly_chart(
            fig_value,
            use_container_width=True,
        )

        # ----------------------------------------------------
        # SUCCESS RATE
        # ----------------------------------------------------

        fig_success = px.bar(
            partner_df,
            x="partner_name",
            y="success_rate",
            title="Success Rate by Partner",
        )

        st.plotly_chart(
            fig_success,
            use_container_width=True,
        )

        st.dataframe(
            partner_df,
            use_container_width=True,
            hide_index=True,
        )