import numpy as np
import pandas as pd
from numba import njit
from pandas import DataFrame, Series


def sma(close: Series, period: int) -> Series:
    """Simple Moving Average (SMA)"""
    return close.rolling(window=period).mean()


def ema(close: Series, period: int) -> Series:
    """Exponential Moving Average (EMA)"""
    return close.ewm(span=period, adjust=False).mean()


@njit
def _rsi_calc(data: np.ndarray, period: int) -> np.ndarray:
    delta = np.diff(data)
    gain, loss = delta.copy(), delta.copy()
    gain[gain < 0] = 0
    loss[loss > 0] = 0
    loss = np.abs(loss)

    avg_gain = np.full_like(data, np.nan)
    avg_loss = np.full_like(data, np.nan)

    avg_gain[period] = np.mean(gain[:period])
    avg_loss[period] = np.mean(loss[:period])

    for i in range(period + 1, len(data)):
        avg_gain[i] = (avg_gain[i - 1] * (period - 1) + gain[i - 1]) / period
        avg_loss[i] = (avg_loss[i - 1] * (period - 1) + loss[i - 1]) / period

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def rsi(close: Series, period: int = 14) -> Series:
    """Relative Strength Index (RSI)"""
    rsi_values = _rsi_calc(close.to_numpy(), period)
    return pd.Series(rsi_values, index=close.index)


def macd(close: Series, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> DataFrame:
    """Moving Average Convergence Divergence (MACD)"""
    ema_fast = ema(close, fast_period)
    ema_slow = ema(close, slow_period)
    macd_line = ema_fast - ema_slow
    signal_line = ema(macd_line, signal_period)
    histogram = macd_line - signal_line
    return pd.DataFrame({'MACD': macd_line, 'Signal': signal_line, 'Histogram': histogram})


def bollinger_bands(close: Series, period: int = 20, std_dev: int = 2) -> DataFrame:
    """Bollinger Bands"""
    middle_band = sma(close, period)
    rolling_std = close.rolling(window=period).std()
    upper_band = middle_band + (rolling_std * std_dev)
    lower_band = middle_band - (rolling_std * std_dev)
    return pd.DataFrame({'Upper': upper_band, 'Middle': middle_band, 'Lower': lower_band})


@njit
def _atr_calc(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int) -> np.ndarray:
    tr = np.full_like(close, np.nan)
    for i in range(1, len(close)):
        tr[i] = np.max(np.array([high[i] - low[i], np.abs(high[i] - close[i-1]), np.abs(low[i] - close[i-1])]))

    atr = np.full_like(close, np.nan)
    atr[period] = np.mean(tr[1:period+1])

    for i in range(period + 1, len(close)):
        atr[i] = (atr[i - 1] * (period - 1) + tr[i]) / period

    return atr


def atr(high: Series, low: Series, close: Series, period: int = 14) -> Series:
    """Average True Range (ATR)"""
    atr_values = _atr_calc(high.to_numpy(), low.to_numpy(), close.to_numpy(), period)
    return pd.Series(atr_values, index=close.index)
