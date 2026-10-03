--
-- PostgreSQL database dump
--

\restrict gjEHftuGP7XtLXgggVxAcqkzxSVvh7AntDYraJhKLUKgaEtaQFNDrPgYYcKfwj5

-- Dumped from database version 18.6
-- Dumped by pg_dump version 18.6

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: app_users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.app_users (
    user_id bigint NOT NULL,
    username character varying(100) NOT NULL,
    password_hash text NOT NULL,
    role character varying(20) DEFAULT 'viewer'::character varying NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT app_users_role_check CHECK (((role)::text = ANY ((ARRAY['admin'::character varying, 'analyst'::character varying, 'viewer'::character varying])::text[])))
);


--
-- Name: TABLE app_users; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.app_users IS 'Application users and role assignments for FinPay Analytics API authentication.';


--
-- Name: app_users_user_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.app_users_user_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: app_users_user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.app_users_user_id_seq OWNED BY public.app_users.user_id;


--
-- Name: audit_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.audit_logs (
    audit_id bigint NOT NULL,
    actor_id character varying(255),
    actor_type character varying(50) DEFAULT 'anonymous'::character varying NOT NULL,
    action character varying(100) NOT NULL,
    resource_type character varying(100),
    resource_id character varying(255),
    http_method character varying(10),
    endpoint character varying(255),
    ip_address inet,
    status_code integer,
    old_value jsonb,
    new_value jsonb,
    details jsonb,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: audit_logs_audit_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.audit_logs_audit_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: audit_logs_audit_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.audit_logs_audit_id_seq OWNED BY public.audit_logs.audit_id;


--
-- Name: customers; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.customers (
    customer_id bigint NOT NULL,
    first_name character varying(100) NOT NULL,
    last_name character varying(100) NOT NULL,
    email character varying(255),
    phone character varying(30),
    country character varying(100),
    customer_type character varying(50),
    registration_date date NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    city character varying(100)
);


--
-- Name: customers_customer_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.customers_customer_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: customers_customer_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.customers_customer_id_seq OWNED BY public.customers.customer_id;


--
-- Name: etl_run_log; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.etl_run_log (
    run_id bigint NOT NULL,
    run_started_at timestamp without time zone NOT NULL,
    run_completed_at timestamp without time zone,
    rows_extracted integer,
    rows_loaded integer,
    data_quality_status character varying(30),
    pipeline_status character varying(30),
    error_message text
);


--
-- Name: etl_run_log_run_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.etl_run_log_run_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: etl_run_log_run_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.etl_run_log_run_id_seq OWNED BY public.etl_run_log.run_id;


--
-- Name: merchants; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.merchants (
    merchant_id bigint NOT NULL,
    merchant_name character varying(255) NOT NULL,
    business_type character varying(100),
    country character varying(100),
    city character varying(100),
    registration_date date,
    merchant_status character varying(50),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: merchants_merchant_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.merchants_merchant_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: merchants_merchant_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.merchants_merchant_id_seq OWNED BY public.merchants.merchant_id;


--
-- Name: partners; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.partners (
    partner_id integer NOT NULL,
    partner_name character varying(255) NOT NULL,
    partner_type character varying(100),
    country character varying(100),
    status character varying(50)
);


--
-- Name: partners_partner_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.partners_partner_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: partners_partner_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.partners_partner_id_seq OWNED BY public.partners.partner_id;


--
-- Name: payment_channels; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.payment_channels (
    channel_id integer NOT NULL,
    channel_name character varying(100) NOT NULL,
    channel_type character varying(100),
    description text
);


--
-- Name: payment_channels_channel_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.payment_channels_channel_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: payment_channels_channel_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.payment_channels_channel_id_seq OWNED BY public.payment_channels.channel_id;


--
-- Name: payment_transactions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.payment_transactions (
    id bigint NOT NULL,
    reference character varying(100) NOT NULL,
    customer_email character varying(255) NOT NULL,
    amount_minor bigint NOT NULL,
    currency character varying(10) DEFAULT 'NGN'::character varying NOT NULL,
    status character varying(30) DEFAULT 'initialized'::character varying NOT NULL,
    authorization_url text,
    access_code character varying(255),
    paystack_transaction_id bigint,
    gateway_response text,
    channel character varying(50),
    paid_at timestamp without time zone,
    metadata jsonb,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT payment_transactions_amount_minor_check CHECK ((amount_minor > 0))
);


--
-- Name: payment_transactions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.payment_transactions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: payment_transactions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.payment_transactions_id_seq OWNED BY public.payment_transactions.id;


--
-- Name: reconciliation; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.reconciliation (
    reconciliation_id bigint NOT NULL,
    transaction_id uuid,
    settlement_id uuid,
    internal_amount numeric(18,2),
    external_amount numeric(18,2),
    variance numeric(18,2),
    reconciliation_status character varying(50),
    reconciliation_date date,
    notes text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: reconciliation_reconciliation_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.reconciliation_reconciliation_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: reconciliation_reconciliation_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.reconciliation_reconciliation_id_seq OWNED BY public.reconciliation.reconciliation_id;


--
-- Name: settlements; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.settlements (
    settlement_id uuid NOT NULL,
    transaction_id uuid,
    settlement_date date,
    settlement_amount numeric(18,2),
    settlement_status character varying(50),
    bank_reference character varying(255),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: transaction_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.transaction_logs (
    log_id bigint NOT NULL,
    transaction_id uuid,
    event_type character varying(100),
    event_timestamp timestamp without time zone,
    processing_time_ms integer,
    system_name character varying(100),
    message text
);


--
-- Name: transaction_logs_log_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.transaction_logs_log_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: transaction_logs_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.transaction_logs_log_id_seq OWNED BY public.transaction_logs.log_id;


--
-- Name: transactions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.transactions (
    transaction_id uuid NOT NULL,
    customer_id bigint,
    merchant_id bigint,
    channel_id integer,
    partner_id integer,
    transaction_type character varying(50),
    transaction_status character varying(50),
    amount numeric(18,2) NOT NULL,
    currency character varying(10) NOT NULL,
    transaction_timestamp timestamp without time zone NOT NULL,
    completed_timestamp timestamp without time zone,
    failure_reason text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: transactions_analytics; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.transactions_analytics (
    transaction_id text,
    customer_id bigint,
    merchant_id bigint,
    channel_id bigint,
    partner_id bigint,
    transaction_type text,
    transaction_status text,
    amount double precision,
    currency text,
    transaction_timestamp timestamp without time zone,
    completed_timestamp timestamp without time zone,
    failure_reason text,
    created_at timestamp without time zone,
    processing_time_minutes double precision,
    is_successful boolean,
    is_failed boolean,
    is_pending boolean,
    is_refunded boolean
);


--
-- Name: vw_reconciliation; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.vw_reconciliation AS
 SELECT t.transaction_id,
    t.transaction_status,
    t.amount AS transaction_amount,
    t.currency,
    t.partner_id,
    t.transaction_timestamp,
    s.settlement_id,
    s.settlement_date,
    s.settlement_amount,
    s.settlement_status,
    s.bank_reference,
        CASE
            WHEN (s.transaction_id IS NULL) THEN 'Missing Settlement'::text
            WHEN (((t.transaction_status)::text = 'Successful'::text) AND (s.settlement_amount <> t.amount)) THEN 'Amount Mismatch'::text
            WHEN (((t.transaction_status)::text = 'Successful'::text) AND ((s.settlement_status)::text <> 'Settled'::text)) THEN 'Status Mismatch'::text
            WHEN (((t.transaction_status)::text = 'Successful'::text) AND (s.settlement_amount = t.amount) AND ((s.settlement_status)::text = 'Settled'::text)) THEN 'Matched'::text
            WHEN ((t.transaction_status)::text <> 'Successful'::text) THEN 'Not Applicable'::text
            ELSE 'Review Required'::text
        END AS reconciliation_status
   FROM (public.transactions t
     LEFT JOIN public.settlements s ON ((t.transaction_id = s.transaction_id)));


--
-- Name: vw_transaction_anomalies; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.vw_transaction_anomalies AS
 WITH transaction_stats AS (
         SELECT avg(transactions.amount) AS avg_amount,
            stddev_pop(transactions.amount) AS stddev_amount
           FROM public.transactions
        ), transaction_analysis AS (
         SELECT t.transaction_id,
            t.customer_id,
            t.merchant_id,
            t.channel_id,
            t.partner_id,
            t.transaction_type,
            t.transaction_status,
            t.amount,
            t.currency,
            t.transaction_timestamp,
            t.completed_timestamp,
            t.failure_reason,
                CASE
                    WHEN (t.completed_timestamp IS NOT NULL) THEN (EXTRACT(epoch FROM (t.completed_timestamp - t.transaction_timestamp)) / (60)::numeric)
                    ELSE NULL::numeric
                END AS processing_time_minutes,
                CASE
                    WHEN (t.amount > (s.avg_amount + ((3)::numeric * s.stddev_amount))) THEN 'High Value'::text
                    WHEN ((t.completed_timestamp IS NOT NULL) AND ((EXTRACT(epoch FROM (t.completed_timestamp - t.transaction_timestamp)) / (60)::numeric) > (30)::numeric)) THEN 'Long Processing Time'::text
                    WHEN ((t.transaction_status)::text = 'Failed'::text) THEN 'Failed Transaction'::text
                    ELSE 'Normal'::text
                END AS transaction_anomaly
           FROM (public.transactions t
             CROSS JOIN transaction_stats s)
        )
 SELECT ta.transaction_id,
    ta.customer_id,
    ta.merchant_id,
    ta.channel_id,
    ta.partner_id,
    ta.transaction_type,
    ta.transaction_status,
    ta.amount,
    ta.currency,
    ta.transaction_timestamp,
    ta.completed_timestamp,
    ta.failure_reason,
    ta.processing_time_minutes,
    ta.transaction_anomaly,
    r.reconciliation_status,
        CASE
            WHEN (ta.transaction_anomaly <> 'Normal'::text) THEN 'Anomaly'::text
            WHEN (r.reconciliation_status = ANY (ARRAY['Missing Settlement'::text, 'Amount Mismatch'::text, 'Status Mismatch'::text])) THEN 'Reconciliation Exception'::text
            ELSE 'Normal'::text
        END AS risk_category
   FROM (transaction_analysis ta
     LEFT JOIN public.vw_reconciliation r ON ((ta.transaction_id = r.transaction_id)));


--
-- Name: vw_anomaly_summary; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.vw_anomaly_summary AS
 SELECT transaction_anomaly,
    risk_category,
    count(*) AS transaction_count,
    round(sum(amount), 2) AS transaction_value,
    round(avg(amount), 2) AS average_amount
   FROM public.vw_transaction_anomalies
  GROUP BY transaction_anomaly, risk_category;


--
-- Name: vw_channel_performance; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.vw_channel_performance AS
 SELECT pc.channel_name,
    count(t.transaction_id) AS total_transactions,
    count(t.transaction_id) FILTER (WHERE ((t.transaction_status)::text = 'Successful'::text)) AS successful_transactions,
    count(t.transaction_id) FILTER (WHERE ((t.transaction_status)::text = 'Failed'::text)) AS failed_transactions,
    count(t.transaction_id) FILTER (WHERE ((t.transaction_status)::text = 'Pending'::text)) AS pending_transactions,
    round(sum(t.amount), 2) AS total_transaction_value,
    round(avg(t.amount), 2) AS average_transaction_value,
    round(((100.0 * (count(t.transaction_id) FILTER (WHERE ((t.transaction_status)::text = 'Successful'::text)))::numeric) / (NULLIF(count(t.transaction_id), 0))::numeric), 2) AS success_rate
   FROM (public.transactions t
     JOIN public.payment_channels pc ON ((t.channel_id = pc.channel_id)))
  GROUP BY pc.channel_name;


--
-- Name: vw_customer_performance; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.vw_customer_performance AS
 SELECT c.customer_id,
    count(t.transaction_id) AS total_transactions,
    count(t.transaction_id) FILTER (WHERE ((t.transaction_status)::text = 'Successful'::text)) AS successful_transactions,
    count(t.transaction_id) FILTER (WHERE ((t.transaction_status)::text = 'Failed'::text)) AS failed_transactions,
    count(t.transaction_id) FILTER (WHERE ((t.transaction_status)::text = 'Pending'::text)) AS pending_transactions,
    count(t.transaction_id) FILTER (WHERE ((t.transaction_status)::text = 'Refunded'::text)) AS refunded_transactions,
    round(sum(t.amount), 2) AS total_transaction_value,
    round(sum(t.amount) FILTER (WHERE ((t.transaction_status)::text = 'Successful'::text)), 2) AS successful_transaction_value,
    round(avg(t.amount), 2) AS average_transaction_value,
    round(((100.0 * (count(t.transaction_id) FILTER (WHERE ((t.transaction_status)::text = 'Successful'::text)))::numeric) / (NULLIF(count(t.transaction_id), 0))::numeric), 2) AS success_rate
   FROM (public.customers c
     LEFT JOIN public.transactions t ON ((c.customer_id = t.customer_id)))
  GROUP BY c.customer_id;


--
-- Name: vw_customer_segments; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.vw_customer_segments AS
 SELECT customer_id,
    total_transactions,
    successful_transactions,
    failed_transactions,
    pending_transactions,
    refunded_transactions,
    total_transaction_value,
    successful_transaction_value,
    average_transaction_value,
    success_rate,
        CASE
            WHEN (total_transaction_value >= (5000000)::numeric) THEN 'High Value'::text
            WHEN (total_transaction_value >= (1000000)::numeric) THEN 'Medium Value'::text
            ELSE 'Low Value'::text
        END AS customer_segment
   FROM public.vw_customer_performance;


--
-- Name: vw_executive_kpis; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.vw_executive_kpis AS
 SELECT count(*) AS total_transactions,
    count(*) FILTER (WHERE ((transaction_status)::text = 'Successful'::text)) AS successful_transactions,
    count(*) FILTER (WHERE ((transaction_status)::text = 'Failed'::text)) AS failed_transactions,
    count(*) FILTER (WHERE ((transaction_status)::text = 'Pending'::text)) AS pending_transactions,
    count(*) FILTER (WHERE ((transaction_status)::text = 'Refunded'::text)) AS refunded_transactions,
    round(sum(amount), 2) AS total_transaction_value,
    round(sum(amount) FILTER (WHERE ((transaction_status)::text = 'Successful'::text)), 2) AS successful_transaction_value,
    round(avg(amount), 2) AS average_transaction_value,
    round(((100.0 * (count(*) FILTER (WHERE ((transaction_status)::text = 'Successful'::text)))::numeric) / (NULLIF(count(*), 0))::numeric), 2) AS success_rate
   FROM public.transactions;


--
-- Name: vw_merchant_performance; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.vw_merchant_performance AS
 SELECT m.merchant_id,
    m.merchant_name,
    m.business_type,
    count(t.transaction_id) AS total_transactions,
    count(t.transaction_id) FILTER (WHERE ((t.transaction_status)::text = 'Successful'::text)) AS successful_transactions,
    count(t.transaction_id) FILTER (WHERE ((t.transaction_status)::text = 'Failed'::text)) AS failed_transactions,
    round(sum(t.amount), 2) AS total_transaction_value,
    round(avg(t.amount), 2) AS average_transaction_value,
    round(((100.0 * (count(t.transaction_id) FILTER (WHERE ((t.transaction_status)::text = 'Successful'::text)))::numeric) / (NULLIF(count(t.transaction_id), 0))::numeric), 2) AS success_rate
   FROM (public.merchants m
     JOIN public.transactions t ON ((m.merchant_id = t.merchant_id)))
  GROUP BY m.merchant_id, m.merchant_name, m.business_type;


--
-- Name: vw_monthly_transaction_performance; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.vw_monthly_transaction_performance AS
 SELECT (date_trunc('month'::text, transaction_timestamp))::date AS month,
    count(*) AS total_transactions,
    count(*) FILTER (WHERE ((transaction_status)::text = 'Successful'::text)) AS successful_transactions,
    count(*) FILTER (WHERE ((transaction_status)::text = 'Failed'::text)) AS failed_transactions,
    count(*) FILTER (WHERE ((transaction_status)::text = 'Pending'::text)) AS pending_transactions,
    count(*) FILTER (WHERE ((transaction_status)::text = 'Refunded'::text)) AS refunded_transactions,
    round(sum(amount), 2) AS total_transaction_value,
    round(sum(amount) FILTER (WHERE ((transaction_status)::text = 'Successful'::text)), 2) AS successful_transaction_value,
    round(avg(amount), 2) AS average_transaction_value,
    round(((100.0 * (count(*) FILTER (WHERE ((transaction_status)::text = 'Successful'::text)))::numeric) / (NULLIF(count(*), 0))::numeric), 2) AS success_rate
   FROM public.transactions
  GROUP BY (date_trunc('month'::text, transaction_timestamp));


--
-- Name: vw_monthly_transaction_growth; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.vw_monthly_transaction_growth AS
 WITH monthly AS (
         SELECT vw_monthly_transaction_performance.month,
            vw_monthly_transaction_performance.total_transactions,
            vw_monthly_transaction_performance.successful_transactions,
            vw_monthly_transaction_performance.failed_transactions,
            vw_monthly_transaction_performance.pending_transactions,
            vw_monthly_transaction_performance.refunded_transactions,
            vw_monthly_transaction_performance.total_transaction_value,
            vw_monthly_transaction_performance.successful_transaction_value,
            vw_monthly_transaction_performance.average_transaction_value,
            vw_monthly_transaction_performance.success_rate
           FROM public.vw_monthly_transaction_performance
        )
 SELECT month,
    total_transactions,
    successful_transactions,
    failed_transactions,
    pending_transactions,
    refunded_transactions,
    total_transaction_value,
    successful_transaction_value,
    average_transaction_value,
    success_rate,
    lag(total_transactions) OVER (ORDER BY month) AS previous_month_transactions,
    round(((100.0 * ((total_transactions - lag(total_transactions) OVER (ORDER BY month)))::numeric) / (NULLIF(lag(total_transactions) OVER (ORDER BY month), 0))::numeric), 2) AS transaction_growth_pct,
    lag(total_transaction_value) OVER (ORDER BY month) AS previous_month_value,
    round(((100.0 * (total_transaction_value - lag(total_transaction_value) OVER (ORDER BY month))) / NULLIF(lag(total_transaction_value) OVER (ORDER BY month), (0)::numeric)), 2) AS value_growth_pct
   FROM monthly
  ORDER BY month;


--
-- Name: vw_partner_performance; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.vw_partner_performance AS
 SELECT p.partner_id,
    p.partner_name,
    p.partner_type,
    p.country,
    p.status,
    count(t.transaction_id) AS total_transactions,
    count(t.transaction_id) FILTER (WHERE ((t.transaction_status)::text = 'Successful'::text)) AS successful_transactions,
    count(t.transaction_id) FILTER (WHERE ((t.transaction_status)::text = 'Failed'::text)) AS failed_transactions,
    count(t.transaction_id) FILTER (WHERE ((t.transaction_status)::text = 'Pending'::text)) AS pending_transactions,
    count(t.transaction_id) FILTER (WHERE ((t.transaction_status)::text = 'Refunded'::text)) AS refunded_transactions,
    round(sum(t.amount), 2) AS total_transaction_value,
    round(sum(t.amount) FILTER (WHERE ((t.transaction_status)::text = 'Successful'::text)), 2) AS successful_transaction_value,
    round(avg(t.amount), 2) AS average_transaction_value,
    round(((100.0 * (count(t.transaction_id) FILTER (WHERE ((t.transaction_status)::text = 'Successful'::text)))::numeric) / (NULLIF(count(t.transaction_id), 0))::numeric), 2) AS success_rate
   FROM (public.partners p
     LEFT JOIN public.transactions t ON ((p.partner_id = t.partner_id)))
  GROUP BY p.partner_id, p.partner_name, p.partner_type, p.country, p.status;


--
-- Name: vw_partner_ranking; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.vw_partner_ranking AS
 SELECT partner_id,
    partner_name,
    partner_type,
    country,
    status,
    total_transactions,
    successful_transactions,
    failed_transactions,
    pending_transactions,
    refunded_transactions,
    total_transaction_value,
    successful_transaction_value,
    average_transaction_value,
    success_rate,
    rank() OVER (ORDER BY total_transaction_value DESC) AS value_rank,
    rank() OVER (ORDER BY success_rate DESC) AS success_rate_rank,
    rank() OVER (ORDER BY total_transactions DESC) AS volume_rank
   FROM public.vw_partner_performance;


--
-- Name: vw_payment_gateway_channel; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.vw_payment_gateway_channel AS
 SELECT COALESCE(NULLIF((channel)::text, ''::text), 'Unknown'::text) AS payment_channel,
    count(*) AS total_payment_attempts,
    count(*) FILTER (WHERE (lower((status)::text) = 'success'::text)) AS successful_payments,
    count(*) FILTER (WHERE (lower((status)::text) = 'failed'::text)) AS failed_payments,
    count(*) FILTER (WHERE (lower((status)::text) = 'pending'::text)) AS pending_payments,
    count(*) FILTER (WHERE (lower((status)::text) = 'abandoned'::text)) AS abandoned_payments,
    (COALESCE(sum(amount_minor), (0)::numeric) / 100.0) AS total_payment_value,
    (COALESCE(sum(amount_minor) FILTER (WHERE (lower((status)::text) = 'success'::text)), (0)::numeric) / 100.0) AS successful_payment_value,
    round((((count(*) FILTER (WHERE (lower((status)::text) = 'success'::text)))::numeric / (NULLIF(count(*), 0))::numeric) * (100)::numeric), 2) AS payment_success_rate
   FROM public.payment_transactions
  GROUP BY COALESCE(NULLIF((channel)::text, ''::text), 'Unknown'::text)
  ORDER BY (COALESCE(sum(amount_minor), (0)::numeric) / 100.0) DESC;


--
-- Name: vw_payment_gateway_daily; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.vw_payment_gateway_daily AS
 SELECT (created_at)::date AS payment_date,
    count(*) AS total_payment_attempts,
    count(*) FILTER (WHERE (lower((status)::text) = 'success'::text)) AS successful_payments,
    count(*) FILTER (WHERE (lower((status)::text) = 'failed'::text)) AS failed_payments,
    count(*) FILTER (WHERE (lower((status)::text) = 'pending'::text)) AS pending_payments,
    count(*) FILTER (WHERE (lower((status)::text) = 'abandoned'::text)) AS abandoned_payments,
    (COALESCE(sum(amount_minor), (0)::numeric) / 100.0) AS total_payment_value,
    (COALESCE(sum(amount_minor) FILTER (WHERE (lower((status)::text) = 'success'::text)), (0)::numeric) / 100.0) AS successful_payment_value,
    round((((count(*) FILTER (WHERE (lower((status)::text) = 'success'::text)))::numeric / (NULLIF(count(*), 0))::numeric) * (100)::numeric), 2) AS payment_success_rate
   FROM public.payment_transactions
  GROUP BY ((created_at)::date)
  ORDER BY ((created_at)::date);


--
-- Name: vw_payment_gateway_kpis; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.vw_payment_gateway_kpis AS
 SELECT count(*) AS total_payment_attempts,
    count(*) FILTER (WHERE (lower((status)::text) = 'success'::text)) AS successful_payments,
    count(*) FILTER (WHERE (lower((status)::text) = 'failed'::text)) AS failed_payments,
    count(*) FILTER (WHERE (lower((status)::text) = 'pending'::text)) AS pending_payments,
    count(*) FILTER (WHERE (lower((status)::text) = 'abandoned'::text)) AS abandoned_payments,
    (COALESCE(sum(amount_minor), (0)::numeric) / 100.0) AS total_payment_value,
    (COALESCE(sum(amount_minor) FILTER (WHERE (lower((status)::text) = 'success'::text)), (0)::numeric) / 100.0) AS successful_payment_value,
    round((COALESCE(avg(amount_minor), (0)::numeric) / 100.0), 2) AS average_payment_value,
    round((((count(*) FILTER (WHERE (lower((status)::text) = 'success'::text)))::numeric / (NULLIF(count(*), 0))::numeric) * (100)::numeric), 2) AS payment_success_rate
   FROM public.payment_transactions;


--
-- Name: app_users user_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.app_users ALTER COLUMN user_id SET DEFAULT nextval('public.app_users_user_id_seq'::regclass);


--
-- Name: audit_logs audit_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_logs ALTER COLUMN audit_id SET DEFAULT nextval('public.audit_logs_audit_id_seq'::regclass);


--
-- Name: customers customer_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customers ALTER COLUMN customer_id SET DEFAULT nextval('public.customers_customer_id_seq'::regclass);


--
-- Name: etl_run_log run_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.etl_run_log ALTER COLUMN run_id SET DEFAULT nextval('public.etl_run_log_run_id_seq'::regclass);


--
-- Name: merchants merchant_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.merchants ALTER COLUMN merchant_id SET DEFAULT nextval('public.merchants_merchant_id_seq'::regclass);


--
-- Name: partners partner_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.partners ALTER COLUMN partner_id SET DEFAULT nextval('public.partners_partner_id_seq'::regclass);


--
-- Name: payment_channels channel_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payment_channels ALTER COLUMN channel_id SET DEFAULT nextval('public.payment_channels_channel_id_seq'::regclass);


--
-- Name: payment_transactions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payment_transactions ALTER COLUMN id SET DEFAULT nextval('public.payment_transactions_id_seq'::regclass);


--
-- Name: reconciliation reconciliation_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reconciliation ALTER COLUMN reconciliation_id SET DEFAULT nextval('public.reconciliation_reconciliation_id_seq'::regclass);


--
-- Name: transaction_logs log_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transaction_logs ALTER COLUMN log_id SET DEFAULT nextval('public.transaction_logs_log_id_seq'::regclass);


--
-- Name: app_users app_users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.app_users
    ADD CONSTRAINT app_users_pkey PRIMARY KEY (user_id);


--
-- Name: app_users app_users_username_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.app_users
    ADD CONSTRAINT app_users_username_key UNIQUE (username);


--
-- Name: audit_logs audit_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_pkey PRIMARY KEY (audit_id);


--
-- Name: customers customers_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customers
    ADD CONSTRAINT customers_email_key UNIQUE (email);


--
-- Name: customers customers_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customers
    ADD CONSTRAINT customers_pkey PRIMARY KEY (customer_id);


--
-- Name: etl_run_log etl_run_log_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.etl_run_log
    ADD CONSTRAINT etl_run_log_pkey PRIMARY KEY (run_id);


--
-- Name: merchants merchants_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.merchants
    ADD CONSTRAINT merchants_pkey PRIMARY KEY (merchant_id);


--
-- Name: partners partners_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.partners
    ADD CONSTRAINT partners_pkey PRIMARY KEY (partner_id);


--
-- Name: payment_channels payment_channels_channel_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payment_channels
    ADD CONSTRAINT payment_channels_channel_name_key UNIQUE (channel_name);


--
-- Name: payment_channels payment_channels_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payment_channels
    ADD CONSTRAINT payment_channels_pkey PRIMARY KEY (channel_id);


--
-- Name: payment_transactions payment_transactions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payment_transactions
    ADD CONSTRAINT payment_transactions_pkey PRIMARY KEY (id);


--
-- Name: payment_transactions payment_transactions_reference_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payment_transactions
    ADD CONSTRAINT payment_transactions_reference_key UNIQUE (reference);


--
-- Name: reconciliation reconciliation_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reconciliation
    ADD CONSTRAINT reconciliation_pkey PRIMARY KEY (reconciliation_id);


--
-- Name: settlements settlements_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlements
    ADD CONSTRAINT settlements_pkey PRIMARY KEY (settlement_id);


--
-- Name: transaction_logs transaction_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transaction_logs
    ADD CONSTRAINT transaction_logs_pkey PRIMARY KEY (log_id);


--
-- Name: transactions transactions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_pkey PRIMARY KEY (transaction_id);


--
-- Name: idx_app_users_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_app_users_active ON public.app_users USING btree (is_active);


--
-- Name: idx_app_users_role; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_app_users_role ON public.app_users USING btree (role);


--
-- Name: idx_app_users_username; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_app_users_username ON public.app_users USING btree (username);


--
-- Name: idx_audit_logs_action; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_logs_action ON public.audit_logs USING btree (action);


--
-- Name: idx_audit_logs_actor_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_logs_actor_id ON public.audit_logs USING btree (actor_id);


--
-- Name: idx_audit_logs_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_logs_created_at ON public.audit_logs USING btree (created_at);


--
-- Name: idx_audit_logs_resource; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_logs_resource ON public.audit_logs USING btree (resource_type, resource_id);


--
-- Name: idx_audit_logs_status_code; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_logs_status_code ON public.audit_logs USING btree (status_code);


--
-- Name: idx_payment_transactions_channel; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_payment_transactions_channel ON public.payment_transactions USING btree (channel);


--
-- Name: idx_payment_transactions_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_payment_transactions_created_at ON public.payment_transactions USING btree (created_at);


--
-- Name: idx_payment_transactions_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_payment_transactions_status ON public.payment_transactions USING btree (status);


--
-- Name: idx_reconciliation_transaction; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_reconciliation_transaction ON public.reconciliation USING btree (transaction_id);


--
-- Name: idx_settlements_transaction; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_settlements_transaction ON public.settlements USING btree (transaction_id);


--
-- Name: idx_transactions_customer; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_transactions_customer ON public.transactions USING btree (customer_id);


--
-- Name: idx_transactions_merchant; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_transactions_merchant ON public.transactions USING btree (merchant_id);


--
-- Name: idx_transactions_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_transactions_status ON public.transactions USING btree (transaction_status);


--
-- Name: idx_transactions_timestamp; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_transactions_timestamp ON public.transactions USING btree (transaction_timestamp);


--
-- Name: reconciliation reconciliation_settlement_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reconciliation
    ADD CONSTRAINT reconciliation_settlement_id_fkey FOREIGN KEY (settlement_id) REFERENCES public.settlements(settlement_id);


--
-- Name: reconciliation reconciliation_transaction_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reconciliation
    ADD CONSTRAINT reconciliation_transaction_id_fkey FOREIGN KEY (transaction_id) REFERENCES public.transactions(transaction_id);


--
-- Name: settlements settlements_transaction_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settlements
    ADD CONSTRAINT settlements_transaction_id_fkey FOREIGN KEY (transaction_id) REFERENCES public.transactions(transaction_id);


--
-- Name: transaction_logs transaction_logs_transaction_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transaction_logs
    ADD CONSTRAINT transaction_logs_transaction_id_fkey FOREIGN KEY (transaction_id) REFERENCES public.transactions(transaction_id);


--
-- Name: transactions transactions_channel_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_channel_id_fkey FOREIGN KEY (channel_id) REFERENCES public.payment_channels(channel_id);


--
-- Name: transactions transactions_customer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_customer_id_fkey FOREIGN KEY (customer_id) REFERENCES public.customers(customer_id);


--
-- Name: transactions transactions_merchant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_merchant_id_fkey FOREIGN KEY (merchant_id) REFERENCES public.merchants(merchant_id);


--
-- Name: transactions transactions_partner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_partner_id_fkey FOREIGN KEY (partner_id) REFERENCES public.partners(partner_id);


--
-- PostgreSQL database dump complete
--

\unrestrict gjEHftuGP7XtLXgggVxAcqkzxSVvh7AntDYraJhKLUKgaEtaQFNDrPgYYcKfwj5

