import torch
from torchvision.models import efficientnet_b0, EfficientNet_B0_Weights
from PIL import Image
from typing import TypedDict


class ImageClassificationResult(TypedDict):
    class_id: int
    class_name: str
    score: float


class MLService:
    def __init__(self, model_path: str, *, device: str = "cpu"):
        self._device = device
        self._model = self._load_model(model_path)

    def _load_model(self, model_path: str) -> torch.nn.Module:
        state_dict = torch.load(model_path, map_location=self._device)
        model = efficientnet_b0(weights=None)
        model.load_state_dict(state_dict)
        model.eval()
        return model

    def _preprocess_input(self, image: Image.Image) -> torch.Tensor:
        weights = EfficientNet_B0_Weights.IMAGENET1K_V1
        preprocess = weights.transforms()
        return preprocess(image).unsqueeze(0).to(self._device)

    def predict(self, image: Image.Image) -> ImageClassificationResult:
        input_tensor = self._preprocess_input(image)
        with torch.no_grad():
            outputs = self._model(input_tensor)
            probabilities = torch.nn.functional.softmax(outputs[0], dim=0)

        top_prob, top_catid = torch.topk(probabilities, 1)
        top_prob = float(top_prob[0].cpu())
        top_catid = int(top_catid[0].cpu())
        weights = EfficientNet_B0_Weights.IMAGENET1K_V1
        class_name = weights.meta["categories"][top_catid]

        return ImageClassificationResult(
            class_id=top_catid, class_name=class_name, score=top_prob
        )
