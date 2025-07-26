import logging
import os
from datetime import datetime, timedelta

import mlflow
import pandas as pd
import xgboost as xgb
from feast import FeatureStore
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split

# --- Configuration ---
# MLflow settings - replace with your Vertex AI MLflow tracking URI
MLFLOW_TRACKING_URI = os.environ.get("MLFLOW_TRACKING_URI", "http://127.0.0.1:5000")
mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

# Feast settings
FEAST_REPO_PATH = "../features/feature_repo"
ENTITY_NAME = "symbol"
FEATURE_VIEW_NAME = "instrument_features"

# Model parameters
XGB_PARAMS = {
    "objective": "reg:squarederror",
    "n_estimators": 100,
    "max_depth": 6,
    "learning_rate": 0.1,
    "eval_metric": "rmse",
}


def load_features(feature_store: FeatureStore, symbols: list[str], start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """Load features from the offline store."""
    entity_df = pd.DataFrame({"symbol": symbols, "event_timestamp": [end_date] * len(symbols)})

    features_to_load = [
        f"{FEATURE_VIEW_NAME}:sma_5",
        f"{FEATURE_VIEW_NAME}:rsi_14",
        f"{FEATURE_VIEW_NAME}:macd_diff",
        f"{FEATURE_VIEW_NAME}:close_price", # Assuming close_price is a feature
    ]

    training_df = feature_store.get_historical_features(
        entity_df=entity_df,
        features=features_to_load,
    ).to_df()

    # Filter by date range
    training_df['event_timestamp'] = pd.to_datetime(training_df['event_timestamp'])
    training_df = training_df[(training_df['event_timestamp'] >= start_date) & (training_df['event_timestamp'] <= end_date)]

    return training_df


def calculate_target(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate the next-minute return."""
    df = df.sort_values(by=["symbol", "event_timestamp"])
    df["target_return"] = df.groupby("symbol")["close_price"].pct_change().shift(-1)
    df = df.dropna()
    return df


def train():
    """Main training function."""

    # Initialize Feast feature store
    store = FeatureStore(repo_path=FEAST_REPO_PATH)

    # Define symbols and date range for training
    symbols_to_train = ["GOOGL"] # Example symbol
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    # Load data
    logging.info("Loading features from Feast...")
    features_df = load_features(store, symbols_to_train, start_date, end_date)

    # Calculate target
    logging.info("Calculating target variable...")
    data = calculate_target(features_df)

    # Split data
    X = data[["sma_5", "rsi_14", "macd_diff"]]
    y = data["target_return"]
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)

    # Start MLflow run
    with mlflow.start_run() as run:
        logging.info(f"Starting MLflow run: {run.info.run_id}")

        # Log parameters
        mlflow.log_params(XGB_PARAMS)

        # Train model
        logging.info("Training XGBoost model...")
        model = xgb.XGBRegressor(**XGB_PARAMS)
        model.fit(X_train, y_train, eval_set=[(X_val, y_val)], early_stopping_rounds=10, verbose=False)

        # Evaluate model
        predictions = model.predict(X_val)
        rmse = mean_squared_error(y_val, predictions, squared=False)

        # Log metrics
        logging.info(f"Validation RMSE: {rmse}")
        mlflow.log_metric("val_rmse", rmse)

        # Log model
        logging.info("Logging model to MLflow...")
        mlflow.xgboost.log_model(model, "xgb_regressor_model")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    train()
