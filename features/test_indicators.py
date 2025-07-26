import numpy as np
import pandas as pd
import pytest

from features.indicators import (atr, bollinger_bands, ema, macd, rsi, sma)


@pytest.fixture
def sample_data() -> pd.DataFrame:
    """Fixture to create sample OHLCV data."""
    # Using real data for a known period to make validation easier.
    # GOOGL stock data from 2023-01-03 to 2023-02-10
    data = {
        'open': [89.83, 89.54, 88.26, 86.60, 87.36, 88.07, 88.58, 90.50, 94.67, 94.95, 98.30, 99.07, 100.00, 98.68, 97.42, 95.50, 94.95, 91.80, 92.51, 95.01, 99.27, 102.35, 104.90, 107.00, 105.12, 105.25, 108.22, 107.52, 107.93, 108.56],
        'high': [91.05, 90.79, 89.31, 88.35, 87.60, 88.51, 90.84, 94.93, 95.27, 97.22, 98.79, 99.42, 100.29, 99.88, 97.75, 96.08, 95.09, 92.68, 94.07, 98.32, 100.67, 103.18, 105.18, 107.04, 106.88, 106.53, 108.97, 108.00, 108.62, 109.10],
        'low': [88.98, 88.85, 86.30, 86.50, 85.97, 87.14, 88.28, 90.22, 93.60, 94.02, 97.03, 97.60, 97.80, 97.25, 94.01, 94.66, 91.00, 91.01, 92.20, 94.52, 98.86, 101.01, 102.53, 104.51, 104.76, 104.81, 106.60, 106.31, 107.02, 107.03],
        'close': [90.30, 90.46, 86.77, 88.08, 86.80, 88.07, 90.79, 94.86, 95.09, 97.10, 98.71, 98.39, 99.28, 99.37, 94.61, 94.71, 91.24, 92.56, 93.65, 97.95, 100.00, 101.21, 104.62, 105.22, 105.12, 105.92, 108.90, 107.21, 108.04, 108.91]
    }
    dates = pd.to_datetime(pd.date_range(start='2023-01-03', periods=30, freq='B'))
    return pd.DataFrame(data, index=dates)

def test_sma(sample_data):
    period = 5
    sma_series = sma(sample_data['close'], period=period)
    assert isinstance(sma_series, pd.Series)
    assert sma_series.isnull().sum() == period - 1
    assert np.isclose(sma_series.iloc[-1], 107.796)

def test_ema(sample_data):
    period = 5
    ema_series = ema(sample_data['close'], period=period)
    assert isinstance(ema_series, pd.Series)
    assert not ema_series.isnull().any()
    assert np.isclose(ema_series.iloc[-1], 107.493, atol=1e-3)

def test_rsi(sample_data):
    period = 14
    rsi_series = rsi(sample_data['close'], period=period)
    assert isinstance(rsi_series, pd.Series)
    assert rsi_series.isnull().sum() == period
    assert np.isclose(rsi_series.iloc[-1], 72.93, atol=1e-2)

def test_macd(sample_data):
    macd_df = macd(sample_data['close'])
    assert isinstance(macd_df, pd.DataFrame)
    assert 'MACD' in macd_df.columns
    assert 'Signal' in macd_df.columns
    assert 'Histogram' in macd_df.columns
    assert np.isclose(macd_df['MACD'].iloc[-1], 4.178, atol=1e-3)
    assert np.isclose(macd_df['Signal'].iloc[-1], 3.357, atol=1e-3)
    assert np.isclose(macd_df['Histogram'].iloc[-1], 0.821, atol=1e-3)

def test_bollinger_bands(sample_data):
    period = 20
    bb_df = bollinger_bands(sample_data['close'], period=period)
    assert isinstance(bb_df, pd.DataFrame)
    assert 'Upper' in bb_df.columns
    assert 'Middle' in bb_df.columns
    assert 'Lower' in bb_df.columns
    assert bb_df['Upper'].isnull().sum() == period - 1
    assert np.isclose(bb_df['Upper'].iloc[-1], 112.14, atol=1e-2)
    assert np.isclose(bb_df['Middle'].iloc[-1], 100.78, atol=1e-2)
    assert np.isclose(bb_df['Lower'].iloc[-1], 89.42, atol=1e-2)

def test_atr(sample_data):
    period = 14
    atr_series = atr(sample_data['high'], sample_data['low'], sample_data['close'], period=period)
    assert isinstance(atr_series, pd.Series)
    assert atr_series.isnull().sum() == period
    assert np.isclose(atr_series.iloc[-1], 2.607, atol=1e-3)
