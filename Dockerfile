FROM python:3.12-slim AS builder
WORKDIR /build
COPY requirements.txt requirements-providers.txt requirements-ui.txt ./
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements-ui.txt

FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 RESEARCH_CACHE_DIR=/app/.cache/researcher
WORKDIR /app
COPY --from=builder /wheels /wheels
COPY requirements.txt requirements-providers.txt requirements-ui.txt ./
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r requirements-ui.txt \
    && rm -rf /wheels \
    && useradd --uid 10001 --create-home researcher \
    && mkdir /app/.cache && chown researcher:researcher /app/.cache
COPY ai ./ai
COPY researcher ./researcher
COPY data ./data
COPY demo_ai.py .
USER researcher
EXPOSE 8501
ENTRYPOINT ["python", "-m", "researcher"]
CMD ["demo", "--offline", "--no-cache"]
