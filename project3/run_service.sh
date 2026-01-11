#!/usr/bin/env bash
uv run bentoml build --name mnist_classifier_app --version v1 --containerize
docker run --rm -p 8080:8080 mnist_classifier_app:v1