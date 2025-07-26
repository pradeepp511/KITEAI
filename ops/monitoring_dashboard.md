# Cloud Monitoring Dashboard for the Autonomous Trading Platform

This guide explains how to set up a dashboard in Google Cloud Monitoring to visualize key performance indicators (KPIs) and set up alerts for the autonomous trading platform.

## Prerequisites

1.  **Prometheus Integration:** You must have a Prometheus server scraping the `/metrics` endpoints of your services (e.g., `ops/metrics_exporter.py`).
2.  **Google Cloud Operations Suite:** The Google Cloud Operations (formerly Stackdriver) agent must be configured to collect metrics from your Prometheus server and send them to Cloud Monitoring. This is often done using the Stackdriver Prometheus sidecar or the OpenTelemetry Collector.
3.  **Deployed Services:** The services (`auth`, `ingestion`, `execution`, `ops`) should be deployed and running, exposing their metrics.

## Creating the Dashboard

1.  **Navigate to Cloud Monitoring:** In the Google Cloud Console, go to "Monitoring".
2.  **Go to Dashboards:** In the left-hand menu, select "Dashboards".
3.  **Create Dashboard:** Click "+ Create Dashboard".
4.  **Add Widgets:** Add new widgets (charts) to the dashboard for each metric you want to track.

---

### Chart 1: P&L (Profit and Loss)

To visualize P&L, you would typically have a metric representing the portfolio's equity over time. Since we don't have a direct P&L metric in the exporter, we'll assume you have a way to calculate and expose `portfolio_equity_usd`.

*   **Widget Type:** Line Chart
*   **Title:** Portfolio Equity
*   **Metric:**
    *   Use the Metrics Explorer.
    *   **Metric:** Find your custom Prometheus metric, which will be named something like `prometheus.io/portfolio_equity_usd/gauge`.
    *   **Group By:** You can group by `symbol` if your metric has that label.

---

### Chart 2: Model Prediction Latency

This chart will visualize the latency of your prediction model.

*   **Widget Type:** Heatmap or Line Chart (for 95th percentile)
*   **Title:** Model Prediction Latency (P95)
*   **MQL (Monitoring Query Language):** Use MQL for more advanced queries.
    ```mql
    fetch prometheus_target::'prometheus.io/model_latency_ms/histogram'
    | {
        p95: value.p95
      }
    | group_by [metric.model_name], [p95: p95(p95)]
    ```
    This query calculates the 95th percentile latency for each model.

---

### Chart 3: Ticks Received Rate

This chart shows the rate of incoming market data ticks.

*   **Widget Type:** Line Chart
*   **Title:** Ticks Received Rate (per minute)
*   **MQL:**
    ```mql
    fetch prometheus_target::'prometheus.io/ticks_received_total/counter'
    | rate(1m)
    | group_by [metric.symbol]
    ```
    This query calculates the per-minute rate of ticks for each symbol.

---

## Setting Up Alerts

### Alert 1: High Model Latency

This alert will notify you if the model's prediction latency exceeds a threshold.

1.  **Navigate to Alerting:** In the Monitoring console, go to "Alerting".
2.  **Create Policy:** Click "+ Create Policy".
3.  **Select a Metric:**
    *   Use the Metrics Explorer to find the `model_latency_ms` metric.
    *   Use an aggregation to get the 95th percentile (`p95`).
4.  **Configure Trigger:**
    *   **Condition:** "is above"
    *   **Threshold:** e.g., `100` (for 100ms)
    *   **For:** `5 minutes`
5.  **Configure Notifications:**
    *   Choose a notification channel (e.g., email, PagerDuty, Slack).
6.  **Name and Save:** Give the policy a descriptive name and save it.

### Alert 2: Feature Drift

Alerting on feature drift is more complex and usually requires a dedicated feature monitoring solution. However, you can create a simple alert based on the *distribution* of a feature.

For example, to detect if the average `rsi_14` value has drifted significantly:

1.  **Expose Feature Metrics:** You would first need to modify a service (e.g., the training or prediction service) to expose a `Histogram` metric for each important feature, like `feature_value_rsi_14`.
2.  **Create Alerting Policy:**
    *   **Metric:** `prometheus.io/feature_value_rsi_14/histogram`.
    *   **Condition:** Set a condition on the `mean` of the histogram. For example, alert if the mean moves outside a historical range (e.g., mean > 70 or mean < 30 for RSI).
    *   This is a basic form of drift detection. More advanced methods would use statistical tests like the Kolmogorov-Smirnov test.

---

This guide provides a starting point. You should customize the dashboards and alerts based on your specific needs and the metrics you expose from your services.
