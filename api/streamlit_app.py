import os

import pandas as pd
import plotly.express as px
import requests
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

API_URL = os.getenv(
    "API_URL",
    "http://127.0.0.1:8000",
)


# ============================================================
# API HELPERS
# ============================================================

def fetch_api(endpoint: str):
    """GET request to FastAPI."""

    try:
        response = requests.get(
            f"{API_URL}{endpoint}",
            timeout=15,
        )

        response.raise_for_status()

        return response.json()

    except requests.exceptions.ConnectionError:
        st.error(
            f"Cannot connect to FastAPI at {API_URL}."
        )
        return None

    except requests.exceptions.Timeout:
        st.error("FastAPI request timed out.")
        return None

    except requests.exceptions.HTTPError as error:
        st.error(
            f"FastAPI returned an error: {error}"
        )
        return None

    except requests.exceptions.RequestException as error:
        st.error(
            f"API request failed: {error}"
        )
        return None


def post_api(endpoint: str, payload: dict):
    """POST request to FastAPI."""

    try:
        response = requests.post(
            f"{API_URL}{endpoint}",
            json=payload,
            timeout=20,
        )

        response.raise_for_status()

        return response.json()

    except requests.exceptions.ConnectionError:
        st.error(
            f"Cannot connect to FastAPI at {API_URL}."
        )
        return None

    except requests.exceptions.Timeout:
        st.error("FastAPI request timed out.")
        return None

    except requests.exceptions.HTTPError as error:

        try:
            error_detail = response.json().get(
                "detail",
                str(error),
            )
        except Exception:
            error_detail = str(error)

        st.error(
            f"Payment API error: {error_detail}"
        )

        return None

    except requests.exceptions.RequestException as error:
        st.error(
            f"API request failed: {error}"
        )
        return None


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
    <h1 style="margin-bottom:0;">
        FinPay Analytics
    </h1>
    """,
    unsafe_allow_html=True,
)

st.caption(
    "Financial transaction intelligence, operations, risk, "
    "reconciliation, and payments platform"
)


# ============================================================
# SIDEBAR
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
        "Payments",
        "Payment History",
        "Payment Analytics",
    ],
)


# ============================================================
# EXECUTIVE OVERVIEW
# ============================================================

if page == "Executive Overview":

    st.header("Executive Overview")

    kpis = fetch_api("/kpis")

    if kpis:

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

        st.subheader("Transaction Status")

        s1, s2, s3, s4 = st.columns(4)

        s1.metric(
            "Successful",
            f"{int(kpis['successful_transactions']):,}",
        )

        s2.metric(
            "Failed",
            f"{int(kpis['failed_transactions']):,}",
        )

        s3.metric(
            "Pending",
            f"{int(kpis['pending_transactions']):,}",
        )

        s4.metric(
            "Refunded",
            f"{int(kpis['refunded_transactions']):,}",
        )

        st.divider()

        channels = fetch_api("/channels")

        if channels:

            channel_df = pd.DataFrame(channels)

            st.subheader(
                "Transaction Value by Channel"
            )

            fig = px.bar(
                channel_df,
                x="channel_name",
                y="total_transaction_value",
                title="Transaction Value by Channel",
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
            )


# ============================================================
# TRANSACTIONS
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

    endpoint = (
        f"/transactions?limit={limit}"
    )

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

    data = fetch_api(endpoint)

    if data is not None:

        df = pd.DataFrame(data)

        st.metric(
            "Transactions Returned",
            f"{len(df):,}",
        )

        st.dataframe(
            df,
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

            fig = px.bar(
                channel_df,
                x="channel_name",
                y="total_transactions",
                title="Transactions by Channel",
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
            )

        with col2:

            fig = px.bar(
                channel_df,
                x="channel_name",
                y="success_rate",
                title="Success Rate by Channel",
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
            )

    if partners:

        partner_df = pd.DataFrame(partners)

        col1, col2 = st.columns(2)

        with col1:

            fig = px.bar(
                partner_df,
                x="partner_name",
                y="total_transactions",
                title="Transactions by Partner",
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
            )

        with col2:

            fig = px.bar(
                partner_df,
                x="partner_name",
                y="success_rate",
                title="Success Rate by Partner",
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
            )


# ============================================================
# ANOMALIES
# ============================================================

elif page == "Anomalies":

    st.header("Risk & Anomaly Monitoring")

    data = fetch_api(
        "/anomalies?limit=1000"
    )

    if data is not None:

        df = pd.DataFrame(data)

        st.metric(
            "Investigation Records",
            f"{len(df):,}",
        )

        if not df.empty:

            if "amount" in df.columns:

                st.metric(
                    "Anomaly Transaction Value",
                    f"₦{df['amount'].sum():,.2f}",
                )

            if "transaction_anomaly" in df.columns:

                summary = (
                    df.groupby(
                        "transaction_anomaly"
                    )
                    .size()
                    .reset_index(
                        name="transaction_count"
                    )
                )

                fig = px.bar(
                    summary,
                    x="transaction_anomaly",
                    y="transaction_count",
                    title="Anomalies by Category",
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True,
                )

            st.subheader(
                "Anomaly Investigation Queue"
            )

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
            )

        else:

            st.success(
                "No anomaly records were returned."
            )


# ============================================================
# RECONCILIATION
# ============================================================

elif page == "Reconciliation":

    st.header("Financial Reconciliation")

    data = fetch_api(
        "/reconciliation?limit=1000"
    )

    if data is not None:

        df = pd.DataFrame(data)

        st.metric(
            "Reconciliation Exceptions",
            f"{len(df):,}",
        )

        if not df.empty:

            if "reconciliation_status" in df.columns:

                summary = (
                    df.groupby(
                        "reconciliation_status"
                    )
                    .size()
                    .reset_index(
                        name="transaction_count"
                    )
                )

                fig = px.pie(
                    summary,
                    names="reconciliation_status",
                    values="transaction_count",
                    title="Reconciliation Exceptions",
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True,
                )

            st.subheader(
                "Reconciliation Investigation Queue"
            )

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
            )

        else:

            st.success(
                "No reconciliation exceptions were returned."
            )


# ============================================================
# CHANNELS
# ============================================================

elif page == "Channels":

    st.header("Payment Channel Performance")

    data = fetch_api("/channels")

    if data is not None:

        df = pd.DataFrame(data)

        if not df.empty:

            c1, c2, c3 = st.columns(3)

            c1.metric(
                "Channels",
                f"{len(df):,}",
            )

            c2.metric(
                "Transactions",
                f"{int(df['total_transactions'].sum()):,}",
            )

            c3.metric(
                "Total Value",
                f"₦{df['total_transaction_value'].sum():,.2f}",
            )

            st.divider()

            fig = px.bar(
                df,
                x="channel_name",
                y="total_transaction_value",
                title="Transaction Value by Channel",
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
            )

            fig = px.bar(
                df,
                x="channel_name",
                y="success_rate",
                title="Success Rate by Channel",
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
            )

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
            )


# ============================================================
# PARTNERS
# ============================================================

elif page == "Partners":

    st.header("Partner Performance")

    data = fetch_api("/partners")

    if data is not None:

        df = pd.DataFrame(data)

        if not df.empty:

            c1, c2, c3 = st.columns(3)

            c1.metric(
                "Partners",
                f"{len(df):,}",
            )

            c2.metric(
                "Transactions",
                f"{int(df['total_transactions'].sum()):,}",
            )

            c3.metric(
                "Total Value",
                f"₦{df['total_transaction_value'].sum():,.2f}",
            )

            st.divider()

            fig = px.bar(
                df,
                x="partner_name",
                y="total_transaction_value",
                title="Transaction Value by Partner",
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
            )

            fig = px.bar(
                df,
                x="partner_name",
                y="success_rate",
                title="Success Rate by Partner",
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
            )

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
            )


# ============================================================
# PAYMENTS
# ============================================================

elif page == "Payments":

    st.header("💳 Payments")

    st.write(
        "Initialize and verify a Paystack Test Mode payment."
    )

    st.warning(
        "Test Mode only. Do not enter real card details."
    )

    # --------------------------------------------------------
    # INITIALIZE PAYMENT
    # --------------------------------------------------------

    st.subheader("Initialize Payment")

    with st.form("payment_form"):

        email = st.text_input(
            "Customer Email",
            placeholder="customer@example.com",
        )

        amount = st.number_input(
            "Amount (NGN)",
            min_value=1.00,
            value=100.00,
            step=100.00,
        )

        description = st.text_input(
            "Description",
            value="FinPay test payment",
        )

        submitted = st.form_submit_button(
            "Initialize Payment"
        )

    if submitted:

        if not email:

            st.error(
                "Please enter a customer email."
            )

        else:

            payload = {
                "email": email,
                "amount_naira": amount,
                "currency": "NGN",
                "description": description,
            }

            result = post_api(
                "/payments/initialize",
                payload,
            )

            if result:

                st.success(
                    "Payment initialized successfully."
                )

                st.session_state[
                    "payment_reference"
                ] = result.get(
                    "reference"
                )

                st.session_state[
                    "authorization_url"
                ] = result.get(
                    "authorization_url"
                )

                st.session_state[
                    "payment_amount"
                ] = amount

    # --------------------------------------------------------
    # CHECKOUT LINK
    # --------------------------------------------------------

    authorization_url = st.session_state.get(
        "authorization_url"
    )

    reference = st.session_state.get(
        "payment_reference"
    )

    if authorization_url:

        st.divider()

        st.subheader(
            "Paystack Checkout"
        )

        st.write(
            f"Reference: `{reference}`"
        )

        st.link_button(
            "Open Paystack Checkout",
            authorization_url,
        )

        st.info(
            "Complete the payment in Paystack Test Mode, "
            "then return here and use Verify Payment below."
        )

    # --------------------------------------------------------
    # VERIFY PAYMENT
    # --------------------------------------------------------

    st.divider()

    st.subheader("Verify Payment")

    verification_reference = st.text_input(
        "Payment Reference",
        value=reference or "",
        placeholder="FINPAY-...",
    )

    verify_clicked = st.button(
        "Verify Payment"
    )

    if verify_clicked:

        if not verification_reference:

            st.error(
                "Enter a payment reference."
            )

        else:

            result = fetch_api(
                f"/payments/verify/{verification_reference}"
            )

            if result:

                payment_status = result.get(
                    "payment_status",
                    "unknown",
                )

                if (
                    str(payment_status).lower()
                    == "success"
                ):

                    st.success(
                        "Payment verified successfully."
                    )

                else:

                    st.warning(
                        f"Payment status: {payment_status}"
                    )

                v1, v2, v3, v4 = st.columns(4)

                v1.metric(
                    "Status",
                    str(payment_status),
                )

                amount_minor = result.get(
                    "amount_minor",
                    0,
                )

                v2.metric(
                    "Amount",
                    f"₦{float(amount_minor) / 100:,.2f}",
                )

                v3.metric(
                    "Currency",
                    result.get(
                        "currency",
                        "NGN",
                    ),
                )

                v4.metric(
                    "Channel",
                    result.get(
                        "channel",
                        "N/A",
                    ),
                )

                st.json(result)


# ============================================================
# PAYMENT HISTORY
# ============================================================

elif page == "Payment History":

    st.header("Payment History")

    data = fetch_api(
        "/payments/history?limit=1000"
    )

    if data is None:

        st.error(
            "Unable to retrieve payment history."
        )

    else:

        df = pd.DataFrame(data)

        if df.empty:

            st.info(
                "No payment records are currently available."
            )

        else:

            # ------------------------------------------------
            # AMOUNT CONVERSION
            # ------------------------------------------------

            if "amount_minor" in df.columns:

                df["amount_naira"] = (
                    pd.to_numeric(
                        df["amount_minor"],
                        errors="coerce",
                    ) / 100
                )

            # ------------------------------------------------
            # SUMMARY
            # ------------------------------------------------

            total_attempts = len(df)

            if "status" in df.columns:

                successful = (
                    df["status"]
                    .astype(str)
                    .str.lower()
                    .eq("success")
                    .sum()
                )

            else:

                successful = 0

            if "amount_naira" in df.columns:

                total_value = (
                    df["amount_naira"]
                    .fillna(0)
                    .sum()
                )

            else:

                total_value = 0

            h1, h2, h3 = st.columns(3)

            h1.metric(
                "Payment Attempts",
                f"{total_attempts:,}",
            )

            h2.metric(
                "Successful Payments",
                f"{successful:,}",
            )

            h3.metric(
                "Payment Value",
                f"₦{total_value:,.2f}",
            )

            st.divider()

            # ------------------------------------------------
            # STATUS FILTER
            # ------------------------------------------------

            if "status" in df.columns:

                statuses = sorted(
                    df["status"]
                    .dropna()
                    .astype(str)
                    .unique()
                    .tolist()
                )

                selected_statuses = st.multiselect(
                    "Payment Status",
                    statuses,
                    default=statuses,
                )

                filtered_df = df[
                    df["status"]
                    .astype(str)
                    .isin(selected_statuses)
                ]

            else:

                filtered_df = df

            # ------------------------------------------------
            # STATUS CHART
            # ------------------------------------------------

            if "status" in filtered_df.columns:

                status_summary = (
                    filtered_df
                    .groupby("status")
                    .size()
                    .reset_index(
                        name="payment_count"
                    )
                )

                fig = px.pie(
                    status_summary,
                    names="status",
                    values="payment_count",
                    title="Payment Status",
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True,
                )

            # ------------------------------------------------
            # DISPLAY TABLE
            # ------------------------------------------------

            st.subheader(
                "Payment Transactions"
            )

            display_columns = [
                "reference",
                "customer_email",
                "amount_naira",
                "currency",
                "status",
                "channel",
                "paystack_transaction_id",
                "gateway_response",
                "paid_at",
                "created_at",
            ]

            available_columns = [
                column
                for column in display_columns
                if column in filtered_df.columns
            ]

            st.dataframe(
                filtered_df[
                    available_columns
                ],
                use_container_width=True,
                hide_index=True,
            )
# ============================================================
# PAYMENT ANALYTICS
# ============================================================

elif page == "Payment Analytics":

    st.header("Payment Gateway Analytics")

    analytics = fetch_api(
        "/payments/analytics"
    )

    daily = fetch_api(
        "/payments/analytics/daily"
    )

    channels = fetch_api(
        "/payments/analytics/channels"
    )

    # --------------------------------------------------------
    # KPI CARDS
    # --------------------------------------------------------

    if analytics:

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Payment Attempts",
            f"{int(analytics['total_payment_attempts']):,}",
        )

        col2.metric(
            "Successful Payments",
            f"{int(analytics['successful_payments']):,}",
        )

        col3.metric(
            "Success Rate",
            f"{float(analytics['payment_success_rate']):.2f}%",
        )

        col4.metric(
            "Payment Value",
            f"₦{float(analytics['total_payment_value']):,.2f}",
        )

        st.divider()

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "Successful Value",
            f"₦{float(analytics['successful_payment_value']):,.2f}",
        )

        c2.metric(
            "Failed Payments",
            f"{int(analytics['failed_payments']):,}",
        )

        c3.metric(
            "Pending Payments",
            f"{int(analytics['pending_payments']):,}",
        )

        c4.metric(
            "Average Payment",
            f"₦{float(analytics['average_payment_value']):,.2f}",
        )

    # --------------------------------------------------------
    # DAILY TREND
    # --------------------------------------------------------

    if daily:

        daily_df = pd.DataFrame(daily)

        if not daily_df.empty:

            daily_df["payment_date"] = pd.to_datetime(
                daily_df["payment_date"]
            )

            st.subheader(
                "Daily Payment Value"
            )

            fig = px.line(
                daily_df,
                x="payment_date",
                y="total_payment_value",
                title="Daily Payment Value",
            )

            fig.update_layout(
                xaxis_title="Date",
                yaxis_title="Payment Value (NGN)",
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
            )

            st.subheader(
                "Daily Payment Success Rate"
            )

            fig_success = px.line(
                daily_df,
                x="payment_date",
                y="payment_success_rate",
                title="Daily Payment Success Rate",
            )

            fig_success.update_layout(
                xaxis_title="Date",
                yaxis_title="Success Rate (%)",
            )

            st.plotly_chart(
                fig_success,
                use_container_width=True,
            )

    # --------------------------------------------------------
    # CHANNEL ANALYSIS
    # --------------------------------------------------------

    if channels:

        channel_df = pd.DataFrame(
            channels
        )

        if not channel_df.empty:

            st.subheader(
                "Payment Value by Gateway Channel"
            )

            fig_channel = px.bar(
                channel_df,
                x="payment_channel",
                y="total_payment_value",
                title="Payment Value by Channel",
            )

            st.plotly_chart(
                fig_channel,
                use_container_width=True,
            )

            st.subheader(
                "Payment Success Rate by Channel"
            )

            fig_channel_success = px.bar(
                channel_df,
                x="payment_channel",
                y="payment_success_rate",
                title="Payment Success Rate by Channel",
            )

            st.plotly_chart(
                fig_channel_success,
                use_container_width=True,
            )

            st.subheader(
                "Gateway Channel Details"
            )

            st.dataframe(
                channel_df,
                use_container_width=True,
                hide_index=True,
            )