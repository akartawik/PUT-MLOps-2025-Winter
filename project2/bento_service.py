from functools import lru_cache
from pathlib import Path
import logging

import bentoml
import numpy as np
import torch
from pydantic import BaseModel


def _get_logger() -> logging.Logger:
    ch = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    ch.setFormatter(formatter)
    bentoml_logger = logging.getLogger("bentoml")
    bentoml_logger.addHandler(ch)
    bentoml_logger.setLevel(logging.DEBUG)

    return bentoml_logger


logger = _get_logger()


SERVICE_NAME = "mnist_classifier_app"
PORT = 8000


class ClassificationResponse(BaseModel):
    predictions: list[int]


@bentoml.service(name=SERVICE_NAME, http={"port": PORT})
class MNISTClassifierService:
    _TS_MODEL_PATH = (
        Path(__file__).resolve().parents[1] / "models" / "mnist_baseline_ts.pt"
    )
    _MEAN = 0.1307
    _STD = 0.3081

    def __init__(self) -> None:
        self._device = self._select_device()
        logger.debug(f"Using device: {self._device}")
        self._model = self._load_model(self._device)

    @staticmethod
    def _select_device() -> torch.device:
        if torch.cuda.is_available():
            return torch.device("cuda")
        if torch.backends.mps.is_available():
            return torch.device("mps")
        return torch.device("cpu")

    @classmethod
    @lru_cache(maxsize=1)
    def _load_model(cls, device: torch.device) -> torch.jit.ScriptModule:
        ts_path = cls._TS_MODEL_PATH
        if not ts_path.exists():
            raise FileNotFoundError(
                "TorchScript artifact not found. Export it via "
                "`save_torchscript_checkpoint` and place it at "
                f"{ts_path}."
            )

        model = torch.jit.load(str(ts_path), map_location=device)
        model.to(device)
        model.eval()
        return model

    def _prepare_model_input(self, batch: np.ndarray) -> torch.Tensor:
        if batch.ndim == 1:
            batch = batch.reshape(-1, 28, 28)
        elif batch.ndim == 2:
            batch = np.expand_dims(batch, axis=0)
        elif batch.ndim == 4:
            batch = batch.squeeze(1)

        if batch.ndim != 3:
            raise ValueError("Expected input shape (N, 28, 28) or (28, 28)")

        tensor = torch.from_numpy(batch).float()
        tensor = (tensor - self._MEAN) / self._STD
        tensor = tensor.unsqueeze(1)
        return tensor.to(self._device)

    def _predict(self, batch: np.ndarray) -> list[int]:
        tensor = self._prepare_model_input(batch)

        with torch.no_grad():
            logits = self._model(tensor)
            preds = torch.argmax(logits, dim=1)

        preds = preds.cpu().numpy().astype(np.int32).tolist()
        return preds

    @bentoml.api
    async def classify(self, batch: np.ndarray) -> ClassificationResponse:
        logger.info(f"Received request with batch size: {batch.shape}")
        preds = self._predict(batch)
        return ClassificationResponse(
            predictions=preds,
        )
