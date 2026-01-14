import json
import io
from PIL import Image
import boto3


class S3Connector:
    def __init__(self, bucket_name: str | None = None):
        self._client = boto3.client("s3")
        self._bucket_name = bucket_name

    def set_bucket(self, bucket_name: str) -> None:
        self._bucket_name = bucket_name

    def get_image(self, key: str, bucket_name: str | None = None) -> Image.Image:
        """Download an image from S3 and return as PIL Image."""
        bucket = bucket_name or self._bucket_name
        if not bucket:
            raise ValueError("Bucket name must be provided")

        response = self._client.get_object(Bucket=bucket, Key=key)
        image_data = response["Body"].read()
        return Image.open(io.BytesIO(image_data)).convert("RGB")

    def put_json(self, key: str, data: dict, bucket_name: str | None = None) -> None:
        """Upload a dict as JSON to S3."""
        bucket = bucket_name or self._bucket_name
        if not bucket:
            raise ValueError("Bucket name must be provided")

        self._client.put_object(
            Bucket=bucket,
            Key=key,
            Body=json.dumps(data),
            ContentType="application/json",
        )
