import json
import os
import tempfile
from pathlib import Path

import boto3
import joblib
import pandas as pd
from loguru import logger
from pydantic import BaseModel, ValidationError

from ml_engineer_exam.prediction import run_prediction

S3_BUCKET = os.environ["S3_BUCKET"]
MODEL_PREFIX = os.environ.get("MODEL_PREFIX", "models")
DEFAULT_MODEL_NAME = os.environ.get("DEFAULT_MODEL_NAME", "linear")
VALID_MODELS = {"linear", "ridge", "random_forest"}

_s3 = boto3.client("s3")
_tmp = Path(tempfile.gettempdir())


class HousingFeatures(BaseModel):
    MedInc: float
    HouseAge: float
    AveRooms: float
    AveBedrms: float
    Population: float
    AveOccup: float
    Latitude: float
    Longitude: float


def _load_artifact(s3_key: str, local_path: Path) -> None:
    """Download a file from S3 only if it isn't already cached in /tmp."""
    if not local_path.exists():
        logger.info(f"Downloading s3://{S3_BUCKET}/{s3_key}")
        _s3.download_file(S3_BUCKET, s3_key, str(local_path))


def _get_model(model_name: str):
    model_path = _tmp / f"{model_name}.joblib"
    scaler_path = _tmp / "scaler.joblib"
    _load_artifact(f"{MODEL_PREFIX}/{model_name}.joblib", model_path)
    _load_artifact(f"{MODEL_PREFIX}/scaler.joblib", scaler_path)
    return joblib.load(model_path), joblib.load(scaler_path)


def _response(status: int, body: dict) -> dict:
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }


def handler(event, context):
    http_method = (
        event.get("requestContext", {}).get("http", {}).get("method", "POST").upper()
    )

    if http_method == "GET":
        return _response(200, {"status": "healthy"})

    try:
        query = event.get("queryStringParameters") or {}
        model_name = query.get("model_name", DEFAULT_MODEL_NAME)

        if model_name not in VALID_MODELS:
            return _response(
                400,
                {
                    "error": f"Invalid model_name '{model_name}'",
                    "valid_options": sorted(VALID_MODELS),
                },
            )

        raw_body = event.get("body") or "{}"
        body = json.loads(raw_body)
        features = HousingFeatures(**body)

        model, scaler = _get_model(model_name)
        predictions = run_prediction(
            model=model,
            data=pd.DataFrame([features.model_dump()]),
            scaler=scaler,
        )
        predicted_value = float(predictions[0])

        logger.info(f"model={model_name} prediction={predicted_value:.4f}")
        return _response(
            200,
            {
                "model_name": model_name,
                "predicted_median_house_value": predicted_value,
                "input": features.model_dump(),
            },
        )

    except json.JSONDecodeError as exc:
        return _response(400, {"error": f"Invalid JSON body: {exc}"})
    except ValidationError as exc:
        return _response(422, {"error": "Input validation failed", "details": exc.errors()})
    except Exception as exc:
        logger.error(f"Unhandled error: {exc}")
        return _response(500, {"error": "Internal server error"})
