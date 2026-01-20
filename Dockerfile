ARG PYTHON_VERSION=3.14-slim
FROM python:${PYTHON_VERSION} AS base

LABEL org.opencontainers.image.authors="Alexander Kharkevich <alex@kharkevich.org>"
LABEL org.opencontainers.image.source="https://github.com/mlflow-oidc/echo-service"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.description="Echo Service"

RUN adduser --disabled-password --gecos '' python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y \
    && rm -rf /var/lib/apt/lists/*

FROM base AS builder

RUN pip install --no-cache-dir build

USER python
WORKDIR /app
# podman can't create directories with the right permissions
RUN chown python:python /app

COPY --chown=python:python . /app/

RUN python -m build --wheel --outdir /app/dist

FROM base AS final

RUN --mount=type=bind,from=builder,source=/app/dist,target=/app/dist \
    pip install --no-cache-dir /app/dist/*.whl


USER python

EXPOSE 8800

CMD ["uvicorn", "echo_service:app", "--host", "0.0.0.0", "--port", "8800"]
