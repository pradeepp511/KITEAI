CREATE TABLE IF NOT EXISTS orders (
    order_id VARCHAR(255) PRIMARY KEY,
    exchange_order_id VARCHAR(255),
    symbol VARCHAR(50) NOT NULL,
    transaction_type VARCHAR(10) NOT NULL,
    order_type VARCHAR(10) NOT NULL,
    quantity INTEGER NOT NULL,
    price DOUBLE PRECISION,
    status VARCHAR(20) NOT NULL,
    order_timestamp TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
