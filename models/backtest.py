import logging
import os
from datetime import datetime, timedelta

import matplotlib.pyplot as plt
import mlflow
import numpy as np
import pandas as pd
import xgboost as xgb
from feast import FeatureStore
from google.cloud import storage

# --- Configuration ---
# MLflow settings
MLFLOW_RUN_ID = os.environ.get("MLFLOW_RUN_ID")  # Needs to be set

# GCS settings
GCS_BUCKET_NAME = os.environ.get("GCS_BUCKET_NAME") # Needs to be set
EQUITY_CURVE_PATH = "backtest_results/equity_curve.png"

# Backtest settings
INITIAL_CAPITAL = 100000
SLIPPAGE_PCT = 0.001  # 0.1%
BROKERAGE_PCT = 0.0005  # 0.05%

# Feast settings
FEAST_REPO_PATH = "../features/feature_repo"


def load_model(run_id: str):
    """Load a trained XGBoost model from MLflow."""
    logged_model = f"runs:/{run_id}/xgb_regressor_model"
    return mlflow.xgboost.load_model(logged_model)


def run_backtest(data: pd.DataFrame, model, initial_capital: float) -> pd.DataFrame:
    """Runs the vectorized backtest."""

    # Generate signals
    features = data[["sma_5", "rsi_14", "macd_diff"]]
    predictions = model.predict(features)
    data['signal'] = np.where(predictions > 0, 1, -1) # Long on positive pred, short on negative

    # Calculate returns
    data['market_return'] = data['close_price'].pct_change()
    data['strategy_return'] = data['market_return'] * data['signal'].shift(1)

    # Apply costs
    trades = data['signal'].diff().fillna(0) != 0
    data['strategy_return_with_costs'] = data['strategy_return']
    data.loc[trades, 'strategy_return_with_costs'] -= (SLIPPAGE_PCT + BROKERAGE_PCT)

    # Calculate equity curve
    data['equity'] = initial_capital * (1 + data['strategy_return_with_costs']).cumprod()

    return data


def calculate_metrics(equity_curve: pd.Series) -> dict:
    """Calculates performance metrics."""
    total_return = (equity_curve.iloc[-1] / equity_curve.iloc[0]) - 1

    # Sharpe Ratio (assuming 1-minute returns and risk-free rate of 0)
    returns = equity_curve.pct_change().dropna()
    trading_minutes_per_year = 252 * 6.5 * 60
    sharpe_ratio = returns.mean() / returns.std() * np.sqrt(trading_minutes_per_year) # Annualized

    # Max Drawdown
    peak = equity_curve.cummax()
    drawdown = (equity_curve - peak) / peak
    max_drawdown = drawdown.min()

    return {
        "total_return": total_return,
        "sharpe_ratio": sharpe_ratio,
        "max_drawdown": max_drawdown,
    }


def plot_equity_curve(equity_curve: pd.Series, output_path: str):
    """Plots and saves the equity curve."""
    plt.figure(figsize=(12, 6))
    equity_curve.plot(title="Equity Curve")
    plt.xlabel("Date")
    plt.ylabel("Portfolio Value")
    plt.grid(True)
    plt.savefig(output_path)
    logging.info(f"Equity curve plot saved to {output_path}")


def upload_to_gcs(source_file_name: str, bucket_name: str, destination_blob_name: str):
    """Uploads a file to a GCS bucket."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(source_file_name)
    logging.info(f"File {source_file_name} uploaded to gs://{bucket_name}/{destination_blob_name}")


def backtest():
    """Main backtesting function."""
    if not MLFLOW_RUN_ID or not GCS_BUCKET_NAME:
        raise ValueError("MLFLOW_RUN_ID and GCS_BUCKET_NAME environment variables must be set.")

    # Load model
    logging.info(f"Loading model from MLflow run: {MLFLOW_RUN_ID}")
    model = load_model(MLFLOW_RUN_ID)

    # Load test data from Feast
    store = FeatureStore(repo_path=FEAST_REPO_PATH)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=10) # Using a smaller period for backtest
    symbols_to_backtest = ["GOOGL"]

    entity_df = pd.DataFrame({"symbol": symbols_to_backtest, "event_timestamp": [end_date] * len(symbols_to_backtest)})
    features_to_load = [
        "instrument_features:sma_5",
        "instrument_features:rsi_14",
        "instrument_features:macd_diff",
        "instrument_features:close_price",
    ]

    logging.info("Loading features for backtest...")
    test_df = store.get_historical_features(entity_df=entity_df, features=features_to_load).to_df()
    test_df['event_timestamp'] = pd.to_datetime(test_df['event_timestamp'])
    test_df = test_df[(test_df['event_timestamp'] >= start_date) & (test_df['event_timestamp'] <= end_date)]
    test_df = test_df.set_index('event_timestamp')

    # Run backtest
    logging.info("Running backtest simulation...")
    backtest_results = run_backtest(test_df, model, INITIAL_CAPITAL)

    # Calculate and log metrics
    metrics = calculate_metrics(backtest_results['equity'])
    logging.info(f"Backtest Metrics: {metrics}")

    # Plot equity curve and upload to GCS
    plot_equity_curve(backtest_results['equity'], "equity_curve.png")
    upload_to_gcs("equity_curve.png", GCS_BUCKET_NAME, EQUITY_CURVE_PATH)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    backtest()
