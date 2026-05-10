import os

# Must be set before lambda_handler is imported; the module reads it at load time.
os.environ.setdefault("S3_BUCKET", "test-bucket")
