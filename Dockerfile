FROM python:3.11-slim
WORKDIR /app
RUN useradd --create-home --uid 10001 appuser
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir . && mkdir /app/var && chown -R appuser:appuser /app/var
USER appuser
ENV APP_STATE_DIR=/app/var
EXPOSE 8105
CMD ["python", "-m", "researchgraph", "serve", "--host", "0.0.0.0", "--port", "8105"]
