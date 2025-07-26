from fastapi import FastAPI
from prometheus_client import Counter, Histogram, generate_latest
from starlette.responses import Response

# --- Metric Definitions ---
TICKS_RECEIVED = Counter(
    "ticks_received_total",
    "Total number of ticks received from the data source",
    ["symbol"],
)

ORDERS_EXECUTED = Counter(
    "orders_executed_total",
    "Total number of orders executed",
    ["symbol", "order_type", "status"],
)

MODEL_LATENCY = Histogram(
    "model_latency_ms",
    "Model prediction latency in milliseconds",
    ["model_name"],
)

# --- FastAPI App ---
app = FastAPI()

@app.get("/metrics")
def get_metrics():
    """Returns Prometheus metrics."""
    return Response(generate_latest(), media_type="text/plain")

@app.get("/health")
def health_check():
    return {"status": "ok"}

# --- Helper functions for other services to import ---
def record_tick(symbol: str):
    """Increments the ticks_received_total counter."""
    TICKS_RECEIVED.labels(symbol=symbol).inc()

def record_order(symbol: str, order_type: str, status: str):
    """Increments the orders_executed_total counter."""
    ORDERS_EXECUTED.labels(symbol=symbol, order_type=order_type, status=status).inc()

def record_model_latency(model_name: str, latency_ms: float):
    """Observes model latency."""
    MODEL_LATENCY.labels(model_name=model_name).observe(latency_ms)

# Example of how to run this exporter as a standalone service
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
