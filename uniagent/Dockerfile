FROM python:3.13-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install --no-install-recommends --yes \
        default-jdk-headless \
        poppler-utils \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt

RUN pip3 install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
RUN pip3 install --no-cache-dir --requirement /app/requirements.txt

RUN python3 -c "from sentence_transformers import CrossEncoder; CrossEncoder('BAAI/bge-reranker-v2-m3')"
RUN python3 -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/static-similarity-mrl-multilingual-v1')"

COPY resources /app/resources
COPY src /app/src
COPY predict.py /app/predict.py
COPY replay_saved_run.py /app/replay_saved_run.py
RUN python3 -c "from pathlib import Path; p=Path('/app/predict.py'); p.write_bytes(p.read_bytes().replace(bytes([13,10]), bytes([10])))" \
    && chmod +x /app/predict.py

ENTRYPOINT ["/app/predict.py"]
