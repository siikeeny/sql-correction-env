FROM python:3.11-slim

# metadata
LABEL name="sql-correction-env"
LABEL version="1.0"
LABEL description="OpenEnv SQL Query Correction RL Environment"

WORKDIR /app

# install deps first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy project
COPY . .

# HF Spaces expects port 7860
EXPOSE 7860

# health check so HF Space knows when it's ready
HEALTHCHECK --interval=10s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:7860/health', timeout=3)"

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1"]
