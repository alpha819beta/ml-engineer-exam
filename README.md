# README #

* Quick Summary

The Milliman IntelliScript Machine Learning Engineer Exam.

## Repo Overview ##

* Folder Summary

- src
  - ml_engineer_exam
    - model
      - The module needed to train and evaluate the model
    - prediction
      - The module needed to make predictions with the trained model
    - prepare
      - The module needed to prepare the data for training and evaluation
    - scripts
      - run_model_training.py
        - Trains a model ('linear', 'ridge', 'random_forest') using the California housing dataset.
      - run_prediction.py
        - Makes predictions using a trained model and sample input data.
    - config.py
      - Config classes for model training and prediction

### How do I get set up? ###

* Pre-requisites (local running)
  - [Setup SSH Keys needed to pull down repositories](https://www.atlassian.com/git/tutorials/git-ssh)
  - [Install UV](https://docs.astral.sh/uv/getting-started/installation/)

* Repo-setup

- Clone Repo (in IDE)
- Setup UV Environment

### How to run ###

#### Run scripts ####

  - Run Command
  ```shell
  uv run run_model_training --model_type linear 
  uv run run_prediction --model_name linear --input_data "{\"MedInc\": 1.6812, \"HouseAge\": 25.0, \"AveRooms\": 4.192200557103064, \"AveBedrms\": 1.0222841225626742, \"Population\": 1392.0, \"AveOccup\": 3.877437325905293, \"Latitude\": 36.06, \"Longitude\": -119.01}"
  ```

### Run Tests ###

#### Run Unit Tests For Chart Summary ####

```shell
uv run pytest -v
```

## AWS Deployment ##

### Architecture ###

```
GitHub Actions (push to main)
        │
        ├─ 1. Run tests
        ├─ 2. Sync model artifacts → S3
        └─ 3. SAM build + deploy
                    │
                    ▼
        API Gateway HTTP API
                    │
                    ▼
        AWS Lambda  (python3.12)
          ├── Loads model from S3 (/tmp cache on warm start)
          ├── Validates input with Pydantic
          └── Returns JSON prediction
                    │
                    ▼
        S3 Bucket  (model artifacts)
          ├── models/linear.joblib
          ├── models/ridge.joblib
          ├── models/random_forest.joblib
          └── models/scaler.joblib
```

Infrastructure is defined in `infrastructure/template.yaml` (AWS SAM).

### Prerequisites ###

- [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html) configured with credentials
- [SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html)
- [Docker](https://docs.docker.com/get-docker/) (required for `sam build --use-container`)

### GitHub Secrets ###

Add these under **Settings → Secrets and variables → Actions** in your fork:

| Secret | Description |
|---|---|
| `AWS_ACCESS_KEY_ID` | IAM user access key with S3 + CloudFormation + Lambda permissions |
| `AWS_SECRET_ACCESS_KEY` | Corresponding secret key |
| `AWS_REGION` | Target region, e.g. `us-east-1` |
| `S3_BUCKET_NAME` | Bucket name for model artifacts (created automatically on first deploy) |

### Deploy ###

**Automatic:** push to `main` — the [deploy workflow](.github/workflows/deploy.yml) runs tests,
uploads models, and deploys the stack.

**Manual trigger:** use the "Run workflow" button in the Actions tab to choose environment
(`dev` / `staging` / `prod`) and model variant.

The workflow prints the live endpoint URL at the end of the deploy step.

### API Usage ###

**Health check**
```bash
curl https://<api-id>.execute-api.<region>.amazonaws.com/health
```

**Predict** (default model: `linear`)
```bash
curl -X POST https://<api-id>.execute-api.<region>.amazonaws.com/predict \
  -H "Content-Type: application/json" \
  -d '{
    "MedInc": 1.6812, "HouseAge": 25.0,
    "AveRooms": 4.192200557103064, "AveBedrms": 1.0222841225626742,
    "Population": 1392.0, "AveOccup": 3.877437325905293,
    "Latitude": 36.06, "Longitude": -119.01
  }'
```

**Switch model** via query param (`linear`, `ridge`, `random_forest`):
```bash
curl -X POST ".../predict?model_name=random_forest" -d '{...}'
```

**Response**
```json
{
  "model_name": "linear",
  "predicted_median_house_value": 0.7191,
  "input": { "MedInc": 1.6812, "..." }
}
```

### Local Testing with SAM ###

```bash
# Install dependencies and generate requirements.txt
uv sync
uv export --no-dev --no-hashes --output-file requirements.txt

# Build (matches Lambda runtime via Docker)
sam build --template infrastructure/template.yaml --use-container

# Invoke the function locally using the sample event
sam local invoke PredictionFunction --event tests/events/predict_event.json \
  --env-vars '{"PredictionFunction": {"S3_BUCKET": "dummy", "MODEL_PREFIX": "models", "DEFAULT_MODEL_NAME": "linear"}}'

# Or start a local HTTP server
sam local start-api --template infrastructure/template.yaml
```

> **Note:** Local invocation downloads models from S3. To run fully offline, replace
> `_get_model` with a local path loader, or point `S3_BUCKET` at a LocalStack instance.

### Tear Down ###

```bash
aws cloudformation delete-stack --stack-name ml-housing-inference-prod --region <region>
```

---

### Contribution guidelines ###

* Code review

All code reviews should be attached to a merge request or equivalent in your version control system 
(e.g. merge requests are called pull requests in bitbucket)

* Other guidelines

- Add doc strings (preferable restStructuredText)
- Use an IDE like Pycharm, Visual Studio Code, 
- Follow PEP standards
- Create new branches for any work that you do
- Make sure to bump the project version

  ```bash
  uv version --bump minor #patch or minor or major (0.0.1 or major.minor.patch)
  ```

### Who do I talk to? ###

* Dependencies

The project dependencies are located in the pyproject.toml file.
You can see them by running a pip command "pip show ml_engineer_exam" after installing the package via uv.

* Repo owner or admin 

Contact nicholas.arquette@milliman.com