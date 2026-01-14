import argparse
from pathlib import Path

import torch
from torchvision import models


URL = "https://download.pytorch.org/models/efficientnet_b0_rwightman-7f5810bc.pth"


def download_model_weights(url=URL, weights_path="efficientnet_b0.pth"):
    """Download model weights from a given URL and save them locally.

    Args:
        url (str): The URL to download the model weights from.
        weights_path (str): The local path to save the downloaded weights.
    """
    state_dict = torch.hub.load_state_dict_from_url(url, progress=True)
    torch.save(state_dict, weights_path)
    print(f"Model weights downloaded and saved as {weights_path}")


def main():
    parser = argparse.ArgumentParser(description="Download model weights")
    parser.add_argument(
        "--url",
        type=str,
        default=URL,
        help="URL to download the model weights from",
    )
    parser.add_argument(
        "--weights_path",
        type=str,
        default=Path(__file__).parents[1] / "models" / "efficientnet_b0.pth",
        help="Path to save the downloaded model weights as",
    )
    args = parser.parse_args()

    if not Path(args.weights_path).parent.exists():
        Path(args.weights_path).parent.mkdir(parents=True, exist_ok=True)

    download_model_weights(url=args.url, weights_path=args.weights_path)


if __name__ == "__main__":
    main()
