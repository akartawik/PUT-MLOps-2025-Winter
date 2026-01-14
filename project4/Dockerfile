FROM public.ecr.aws/lambda/python:3.12

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy project files
WORKDIR ${LAMBDA_TASK_ROOT}

COPY pyproject.toml .
COPY src/ src/
COPY models/ models/

# Install dependencies using uv
RUN uv pip install --system --no-cache .

# Set the handler
CMD ["ml_app.main.lambda_handler"]
