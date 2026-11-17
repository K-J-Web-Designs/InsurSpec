FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src/ ./src/
COPY templates/ ./templates/
COPY skills_factory/ ./skills_factory/

RUN pip install --upgrade pip && \
    pip install typer rich pydantic jinja2 ruamel.yaml google-genai boto3

ENV PYTHONPATH=/app/src

WORKDIR /workspace

ENTRYPOINT ["python", "-m", "insur_spec.cli"]
CMD ["--help"]
