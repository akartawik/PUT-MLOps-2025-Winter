import logging
from pathlib import Path
from datetime import datetime

from ml_app.model import MLService, ImageClassificationResult
from ml_app.s3_connector import S3Connector
from ml_app.settings import settings


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

ml_service = MLService(model_path=settings.model_path, device=settings.device)
s3_connector = S3Connector()


def lambda_handler(event: dict, context: dict) -> dict:
    logger.info(f"Received event: {event}")

    record = event["Records"][0]
    bucket_name = record["s3"]["bucket"]["name"]
    object_key = record["s3"]["object"]["key"]

    logger.debug(f"Loading object {object_key} from bucket {bucket_name}")
    image = s3_connector.get_image(object_key, bucket_name)

    logger.debug("Performing prediction")
    result: ImageClassificationResult = ml_service.predict(image)

    prediction_dict = {
        "source_key": object_key,
        "class_id": result["class_id"],
        "class_name": result["class_name"],
        "score": result["score"],
    }

    logger.debug(f"Prediction result: {prediction_dict}")

    input_filename = Path(object_key).stem
    output_key = str(
        (
            Path(settings.predictions_s3_folder)
            / f"{input_filename}_prediction_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
        )
    )

    logger.debug(f"Saving prediction to {output_key} in bucket {bucket_name}")
    s3_connector.put_json(output_key, prediction_dict, bucket_name)

    return {
        "statusCode": 200,
        "body": prediction_dict,
    }
