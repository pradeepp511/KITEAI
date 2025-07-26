import logging
import os
from datetime import datetime

from fastapi import FastAPI, HTTPException
from feast import FeatureStore
from google.cloud import aiplatform
from pydantic import BaseModel

# --- Configuration ---
FEAST_REPO_PATH = "../features/feature_repo"
VERTEX_AI_PROJECT = os.environ.get("VERTEX_AI_PROJECT")
VERTEX_AI_REGION = os.environ.get("VERTEX_AI_REGION")
VERTEX_AI_ENDPOINT_ID = os.environ.get("VERTEX_AI_ENDPOINT_ID")

# --- Pydantic Models ---
class SignalRequest(BaseModel):
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int

class SignalResponse(BaseModel):
    action: str  # "buy", "sell", "hold"
    confidence: float


# --- Initialization ---
app = FastAPI()
store = FeatureStore(repo_path=FEAST_REPO_PATH)

aiplatform.init(project=VERTEX_AI_PROJECT, location=VERTEX_AI_REGION)
endpoint = aiplatform.Endpoint(endpoint_name=VERTEX_AI_ENDPOINT_ID)


@app.post("/signal", response_model=SignalResponse)
def get_signal(request: SignalRequest):
    """
    Generates a trading signal based on online features and a deployed model.
    """
    # 1. Fetch online features from Feast
    feature_vector = store.get_online_features(
        features=[
            "instrument_features:sma_5",
            "instrument_features:rsi_14",
            "instrument_features:macd_diff",
        ],
        entity_rows=[{"symbol": request.symbol}],
    ).to_dict()

    # 2. Prepare feature vector for prediction
    # The order of features must match the model's training order.
    instance = [
        feature_vector["sma_5"][0],
        feature_vector["rsi_14"][0],
        feature_vector["macd_diff"][0],
    ]

    # 3. Get prediction from Vertex AI Endpoint
    if not all([VERTEX_AI_PROJECT, VERTEX_AI_REGION, VERTEX_AI_ENDPOINT_ID]):
        raise HTTPException(status_code=500, detail="Vertex AI environment variables not configured.")

    try:
        prediction_result = endpoint.predict(instances=[instance])
        predicted_return = prediction_result.predictions[0][0] # Assuming nested list output
    except Exception as e:
        logging.error(f"Failed to get prediction from Vertex AI: {e}")
        return {"action": "hold", "confidence": 0.0}

    # 4. Translate prediction to action
    confidence = abs(predicted_return)

    if predicted_return > 0.0005:  # Example threshold
        action = "buy"
    elif predicted_return < -0.0005: # Example threshold
        action = "sell"
    else:
        action = "hold"
        confidence = 1.0 - confidence

    return {"action": action, "confidence": confidence}


@app.get("/health")
def health_check():
    return {"status": "ok"}
