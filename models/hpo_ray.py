import logging
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import ray
import xgboost as xgb
from feast import FeatureStore
from ray import tune
from ray.tune.schedulers import ASHAScheduler

from models.backtest import calculate_metrics, run_backtest

# --- Configuration ---
FEAST_REPO_PATH = "../features/feature_repo"
INITIAL_CAPITAL = 100000

# Ray Tune settings
NUM_SAMPLES = 100
CONCURRENT_TRIALS = 32

# Search space for XGBoost
SEARCH_SPACE = {
    "objective": "reg:squarederror",
    "eval_metric": "rmse",
    "n_estimators": tune.randint(100, 1000),
    "max_depth": tune.randint(3, 10),
    "learning_rate": tune.loguniform(1e-4, 1e-1),
    "subsample": tune.uniform(0.5, 1.0),
    "colsample_bytree": tune.uniform(0.5, 1.0),
}


def load_data_for_hpo(store: FeatureStore, symbols: list[str], start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """Loads and prepares data for HPO."""
    entity_df = pd.DataFrame({"symbol": symbols, "event_timestamp": [end_date] * len(symbols)})
    features_to_load = [
        "instrument_features:sma_5", "instrument_features:rsi_14",
        "instrument_features:macd_diff", "instrument_features:close_price",
    ]

    df = store.get_historical_features(entity_df=entity_df, features=features_to_load).to_df()
    df['event_timestamp'] = pd.to_datetime(df['event_timestamp'])
    df = df[(df['event_timestamp'] >= start_date) & (df['event_timestamp'] <= end_date)]
    df = df.set_index('event_timestamp').sort_index()

    # Calculate target
    df = df.sort_values(by=["symbol", "event_timestamp"])
    df["target_return"] = df.groupby("symbol")["close_price"].pct_change().shift(-1)
    df = df.dropna()

    return df


def trainable(config, data):
    """Ray Tune trainable function."""

    # Split data
    train_size = int(len(data) * 0.8)
    train_df, val_df = data[:train_size], data[train_size:]

    X_train = train_df[["sma_5", "rsi_14", "macd_diff"]]
    y_train = train_df["target_return"]

    # Train model
    model = xgb.XGBRegressor(**config)
    model.fit(X_train, y_train, verbose=False)

    # Run backtest on validation set
    backtest_results = run_backtest(val_df, model, INITIAL_CAPITAL)

    # Calculate Sharpe ratio
    metrics = calculate_metrics(backtest_results['equity'])
    sharpe_ratio = metrics.get("sharpe_ratio", -1.0) # Default to -1 if not calculated

    # Report metric to Ray Tune
    tune.report(sharpe_ratio=sharpe_ratio)


def run_hpo():
    """Main HPO function."""
    ray.init(ignore_reinit_error=True, num_cpus=CONCURRENT_TRIALS)

    # Load data once
    store = FeatureStore(repo_path=FEAST_REPO_PATH)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    data = load_data_for_hpo(store, ["GOOGL"], start_date, end_date)

    # Put data in Ray object store to be accessed by all trials
    data_ref = ray.put(data)

    # ASHA scheduler
    scheduler = ASHAScheduler(
        metric="sharpe_ratio",
        mode="max",
        max_t=10, # Max number of iterations/epochs
        grace_period=1,
        reduction_factor=2
    )

    # Run Tune
    analysis = tune.run(
        tune.with_parameters(trainable, data=data_ref),
        resources_per_trial={"cpu": 1},
        config=SEARCH_SPACE,
        num_samples=NUM_SAMPLES,
        scheduler=scheduler
    )

    best_config = analysis.get_best_config(metric="sharpe_ratio", mode="max")
    logging.info(f"Best hyperparameters found: {best_config}")

    ray.shutdown()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_hpo()
