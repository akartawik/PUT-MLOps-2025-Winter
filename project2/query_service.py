import argparse
import json
from pathlib import Path

import requests
import numpy as np
from torchvision.datasets import MNIST


def _load_sample(index: int, data_dir: Path, *, download: bool = False) -> np.ndarray:
    dataset = MNIST(root=data_dir, train=False, download=download)
    sample, _ = dataset[index]
    sample = np.array(sample).astype("float32")
    return sample


def _build_payload(sample: np.ndarray) -> dict[str, list[list[float]]]:
    payload = {"batch": [sample.tolist()]}
    return payload


def _print_sample(img: np.ndarray) -> None:
    x = img / (img.max() + 1e-8)
    chars = " .:-=+*#%@"
    for row in x:
        line = "".join(chars[int(v * (len(chars) - 1))] for v in row)
        print(line)


def main() -> None:
    parser = argparse.ArgumentParser(description="Send MNIST sample to Bento service")
    parser.add_argument(
        "--url",
        default="http://127.0.0.1:8000/classify",
        help="Endpoint exposed by Bento service",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("./data"),
        help="Directory to download MNIST dataset",
    )
    parser.add_argument(
        "--index",
        type=int,
        default=0,
        help="Dataset sample index to send",
    )
    args = parser.parse_args()
    download = not args.data_dir.exists()
    sample = _load_sample(index=args.index, data_dir=args.data_dir, download=download)
    print("Sample:")
    print("=" * 40)
    _print_sample(sample)
    print("=" * 40)
    payload = _build_payload(sample)
    response = requests.post(args.url, json=payload, timeout=30)
    response.raise_for_status()

    print("Response status:", response.status_code)
    print(json.dumps(response.json(), indent=2))


if __name__ == "__main__":
    main()
