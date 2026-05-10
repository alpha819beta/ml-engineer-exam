from pathlib import Path
from pytest import fixture

# Resolve model dir relative to this file so tests work regardless of where
# the package is installed or what MLConfig computes for the current machine.
_MODEL_DIR = Path(__file__).parent.parent / "data" / "models"

@fixture(scope="session")
def session_fixture() -> dict:

    """
    Session scoped fixture to provide model information for tests
    :return:
    """

    model_info = {
        "model_path": _MODEL_DIR / "linear.joblib",
        "input_data": "{\"MedInc\": 1.6812, \"HouseAge\": 25.0, \"AveRooms\": 4.192200557103064, \"AveBedrms\": 1.0222841225626742, \"Population\": 1392.0, \"AveOccup\": 3.877437325905293, \"Latitude\": 36.06, \"Longitude\": -119.01}"
    }

    return model_info
