from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    device: str = "cpu"
    model_path: str = "/var/task/models/efficientnet_b0.pth"
    predictions_s3_folder: str = "predictions/"


settings = Settings()
