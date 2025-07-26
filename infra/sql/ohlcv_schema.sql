-- Enable the TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Table for 1-minute OHLCV data
CREATE TABLE ohlcv_1min (
    time TIMESTAMPTZ NOT NULL,
    instrument_token INTEGER NOT NULL,
    open DOUBLE PRECISION NOT NULL,
    high DOUBLE PRECISION NOT NULL,
    low DOUBLE PRECISION NOT NULL,
    close DOUBLE PRECISION NOT NULL,
    volume BIGINT NOT NULL
);

-- Create a hypertable for the 1-minute data
SELECT create_hypertable('ohlcv_1min', 'time');

-- Add composite index for faster queries
CREATE INDEX ON ohlcv_1min (instrument_token, time DESC);


-- Table for end-of-day (EOD) OHLCV data
CREATE TABLE ohlcv_eod (
    time TIMESTAMPTZ NOT NULL,
    instrument_token INTEGER NOT NULL,
    open DOUBLE PRECISION NOT NULL,
    high DOUBLE PRECISION NOT NULL,
    low DOUBLE PRECISION NOT NULL,
    close DOUBLE PRECISION NOT NULL,
    volume BIGINT NOT NULL
);

-- Create a hypertable for the EOD data
SELECT create_hypertable('ohlcv_eod', 'time');

-- Add composite index for faster queries
CREATE INDEX ON ohlcv_eod (instrument_token, time DESC);
