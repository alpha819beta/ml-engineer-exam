import json
import joblib
import pytest
from pathlib import Path
from unittest.mock import patch

from ml_engineer_exam.lambda_handler import handler

_MODEL_DIR = Path(__file__).parent.parent.parent / "data" / "models"

SAMPLE_INPUT = {
    "MedInc": 1.6812,
    "HouseAge": 25.0,
    "AveRooms": 4.192200557103064,
    "AveBedrms": 1.0222841225626742,
    "Population": 1392.0,
    "AveOccup": 3.877437325905293,
    "Latitude": 36.06,
    "Longitude": -119.01,
}


@pytest.fixture(scope="module")
def linear_model_and_scaler():
    model = joblib.load(_MODEL_DIR / "linear.joblib")
    scaler = joblib.load(_MODEL_DIR / "scaler.joblib")
    return model, scaler


@pytest.fixture
def mock_model(linear_model_and_scaler):
    with patch("ml_engineer_exam.lambda_handler._get_model", return_value=linear_model_and_scaler):
        yield


def _post_event(body=None, query_params=None):
    return {
        "requestContext": {"http": {"method": "POST"}},
        "queryStringParameters": query_params,
        "body": json.dumps(body) if body is not None else None,
    }


def test_health_check():
    event = {"requestContext": {"http": {"method": "GET"}}, "queryStringParameters": None}
    response = handler(event, None)
    assert response["statusCode"] == 200
    assert json.loads(response["body"])["status"] == "healthy"


def test_predict_valid_input(mock_model):
    response = handler(_post_event(SAMPLE_INPUT), None)
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert "predicted_median_house_value" in body
    assert body["model_name"] == "linear"
    assert abs(body["predicted_median_house_value"] - 0.7191) < 0.001


def test_predict_model_name_query_param(mock_model):
    for model_name in ["linear", "ridge", "random_forest"]:
        response = handler(_post_event(SAMPLE_INPUT, query_params={"model_name": model_name}), None)
        assert response["statusCode"] == 200
        assert json.loads(response["body"])["model_name"] == model_name


def test_predict_invalid_model_name():
    response = handler(_post_event(SAMPLE_INPUT, query_params={"model_name": "xgboost"}), None)
    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "valid_options" in body


def test_predict_missing_required_field(mock_model):
    incomplete = {k: v for k, v in SAMPLE_INPUT.items() if k != "MedInc"}
    response = handler(_post_event(incomplete), None)
    assert response["statusCode"] == 422
    assert "details" in json.loads(response["body"])


def test_predict_invalid_json():
    event = {
        "requestContext": {"http": {"method": "POST"}},
        "queryStringParameters": None,
        "body": "not-valid-json{{{",
    }
    response = handler(event, None)
    assert response["statusCode"] == 400


def test_predict_wrong_field_type(mock_model):
    bad_input = {**SAMPLE_INPUT, "MedInc": "not-a-number"}
    response = handler(_post_event(bad_input), None)
    assert response["statusCode"] == 422
